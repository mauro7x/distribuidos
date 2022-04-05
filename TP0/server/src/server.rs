use crate::{client_handler::ClientHandler, config::Config};
use log::{debug, info, trace, warn};
use std::{
    error::Error,
    io,
    net::{SocketAddr, TcpListener, TcpStream},
    sync::mpsc::{Receiver, TryRecvError},
    thread,
    time::Duration,
};

/// ## Arguments
/// 
/// * `accept_sleep_time`: time to sleep when there are no connections to accept.
/// * `ctrlc_receiver`: receiver from channel for handling Ctrl-C signals.
/// * `next_id`: next ID to be used for incoming connections.
/// * `port` (self-descriptive).
/// * `listener`: TcpListener abstraction used for receiving connections.
/// * `handlers`: array of ClientHandler's objects representing established connections.
#[derive(Debug)]
pub struct Server {
    accept_sleep_time: Duration,
    ctrlc_receiver: Receiver<()>,
    next_id: u16,
    port: u16,
    listener: TcpListener,
    handlers: Vec<ClientHandler>,
}

impl Server {
    /// Creates Server with non-blocking TcpListener initialized and bound.
    pub fn new(config: Config, rx: Receiver<()>) -> Result<Server, Box<dyn Error>> {
        trace!("Creating server with config: {:#?}", config);
        let listener_addr = format!("{}:{}", config.host, config.port);
        trace!("Creating TcpListener with addr: {:?}", listener_addr);
        let listener = TcpListener::bind(listener_addr)?;
        listener.set_nonblocking(true)?;

        let server = Server {
            accept_sleep_time: config.accept_sleep_time,
            ctrlc_receiver: rx,
            next_id: 0,
            port: config.port,
            listener,
            handlers: vec![],
        };

        debug!("Created successfully: {:#?}", server);
        Ok(server)
    }

    /// Runs server main loop, accepting connections in a non-blocking
    /// way, allowing to check for Ctrl-C signals received, and to
    /// join client's threads that have already finished executing.
    /// 
    /// Before finishing, joins every thread in a blocking way (graceful).
    pub fn run(mut self) -> Result<(), Box<dyn Error>> {
        trace!("Starting server...");

        info!("Listening to connections on port {}", self.port);
        loop {
            let connection = self.listener.accept();

            match connection {
                Ok((stream, addr)) => self.handle_new_connection(stream, addr)?,
                Err(ref e) if e.kind() == io::ErrorKind::WouldBlock => match self.stopped()? {
                    true => break,
                    false => self.join_threads(false),
                },
                Err(e) => {
                    warn!("Connection failed: {}", e);
                    break;
                }
            }
        }

        self.join_threads(true);

        trace!("Server finished gracefully");
        Ok(())
    }

    /// Checks if a Ctrl-C signal was received.
    fn stopped(&self) -> Result<bool, Box<dyn Error>> {
        match self.ctrlc_receiver.try_recv() {
            Ok(_) => {
                debug!("Ctrl-C signal received");
                Ok(true)
            }
            Err(TryRecvError::Empty) => {
                thread::sleep(self.accept_sleep_time);
                Ok(false)
            }
            Err(TryRecvError::Disconnected) => {
                Err("Ctrl-C signal receiver disconnected unexpectedly".into())
            }
        }
    }

    /// Handles a new connection request createing a ClientHandler
    /// and adding it to the array of client handlers.
    fn handle_new_connection(
        &mut self,
        stream: TcpStream,
        addr: SocketAddr,
    ) -> Result<(), Box<dyn Error>> {
        info!("New connection from {}", addr);
        let handler = ClientHandler::new(self.next_id, stream)?;
        self.next_id += 1;
        self.handlers.push(handler);

        Ok(())
    }

    /// Joins client's threads. Blocking will depend on `wait` argument.
    fn join_threads(&mut self, wait: bool) {
        if wait {
            trace!("Joining client handlers (blocking)...");
        }

        let mut handlers = vec![];
        while let Some(handler) = self.handlers.pop() {
            if wait || handler.joineable() {
                handler.join();
            } else {
                handlers.push(handler);
            }
        }

        self.handlers = handlers;
    }
}
