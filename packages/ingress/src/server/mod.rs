mod config;
mod constants;

use self::config::Config;
use std::{
    fmt::{self, Debug},
    net::{SocketAddr, TcpListener, TcpStream},
    sync::mpsc::{self, Receiver, TryRecvError},
};

use distribuidos_sync::WorkerPool;
use distribuidos_tp1_protocols::requests::send_close_req;
use distribuidos_types::BoxResult;
use log::{debug, info, trace, warn};

pub struct Server {
    listener: TcpListener,
    stop_signal_receiver: Receiver<()>,
    handler_pool: WorkerPool<TcpStream>,
}

impl Server {
    pub fn new<C, F>(context: C, handler: F) -> BoxResult<Server>
    where
        C: Clone + Send + 'static,
        F: Fn(&mut C, TcpStream) + Copy + Send + 'static,
    {
        trace!("Creating Server...");
        let Config {
            host,
            port,
            thread_pool_size,
            queue_size,
        } = Config::new()?;
        let listener_addr = format!("{}:{}", host, port);
        trace!("Binding TcpListener...");
        let listener = TcpListener::bind(listener_addr)?;
        let local_addr = listener.local_addr()?;

        let server = Server {
            listener,
            handler_pool: WorkerPool::new(thread_pool_size, queue_size, context, handler),
            stop_signal_receiver: Server::set_stop_signal_handler(local_addr)?,
        };
        trace!("Server created: {:?}", server);

        Ok(server)
    }

    pub fn run(&mut self) -> BoxResult<()> {
        trace!("Running Server...");

        info!("Listening on {}", self.listener.local_addr()?);
        for connection in self.listener.incoming() {
            if self.stopped()? {
                trace!("Server has received stop signal");
                break;
            }

            let stream = connection?;
            debug!("New connection established: {:?}", stream);
            self.handler_pool.execute(stream).unwrap();
        }

        trace!("Joining Server's handler thread pool...");
        self.handler_pool.join();
        trace!("Server exited gracefully");

        Ok(())
    }

    fn stopped(&self) -> BoxResult<bool> {
        match self.stop_signal_receiver.try_recv() {
            Ok(_) => Ok(true),
            Err(TryRecvError::Empty) => Ok(false),
            Err(TryRecvError::Disconnected) => {
                Err("Ctrl-C signal receiver disconnected unexpectedly".into())
            }
        }
    }

    // Static

    fn set_stop_signal_handler(addr: SocketAddr) -> BoxResult<Receiver<()>> {
        let (tx, rx) = mpsc::channel();
        ctrlc::set_handler(move || {
            trace!("(Ctrl-C) Signal received");
            tx.send(())
                .expect("Could not send signal on stop-signal channel.");
            trace!("(Ctrl-C) Stop message sent in channel");

            match TcpStream::connect(addr) {
                Ok(mut stream) => {
                    if let Err(err) = send_close_req(&mut stream) {
                        warn!("(Ctrl-C) Could not send terminate request - {:?}", err)
                    }
                }
                Err(_) => {
                    warn!("(Ctrl-C) Could not establish connection with Server")
                }
            }
        })?;

        Ok(rx)
    }
}

impl Debug for Server {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:?}", self.listener)
    }
}
