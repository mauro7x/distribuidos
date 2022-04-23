use super::config::Config;
use std::{
    fmt::{self, Debug},
    io::Write,
    net::{SocketAddr, TcpListener, TcpStream},
    sync::mpsc::{self, Receiver, TryRecvError},
};

use distribuidos_sync::BoundedThreadPool;
use distribuidos_tp1_protocols::common::CLOSE;
use distribuidos_types::BoxResult;

pub struct Server {
    listener: TcpListener,
    stop_signal_receiver: Receiver<()>,
    handler_pool: BoundedThreadPool,
}

impl Server {
    pub fn new() -> BoxResult<Server> {
        let Config {
            host,
            port,
            thread_pool_size,
            queue_size,
        } = Config::new()?;
        let listener_addr = format!("{}:{}", host, port);
        let listener = TcpListener::bind(listener_addr)?;
        let local_addr = listener.local_addr()?;

        let server = Server {
            listener,
            handler_pool: BoundedThreadPool::new(thread_pool_size, queue_size),
            stop_signal_receiver: Server::set_stop_signal_handler(local_addr)?,
        };

        Ok(server)
    }

    pub fn run<F>(&mut self, f: F) -> BoxResult<()>
    where
        F: Fn(TcpStream) + Send + Copy + 'static,
    {
        for connection in self.listener.incoming() {
            if self.stopped()? {
                break;
            }

            let stream = connection?;
            self.handler_pool.execute(move || f(stream)).unwrap();
        }

        self.handler_pool.join();

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
            tx.send(())
                .expect("Could not send signal on stop-signal channel.");

            match TcpStream::connect(addr) {
                Ok(mut stream) => {
                    if stream.write_all(&CLOSE).is_err() {
                        println!("Failed writing in the stream")
                    };
                }
                Err(_) => {
                    println!("Server is not accepting connections")
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
