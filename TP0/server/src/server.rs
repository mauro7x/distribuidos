use crate::{client_handler::ClientHandler, config::Config};
use log::{debug, info, trace, warn};
use std::{
    error::Error,
    net::{SocketAddr, TcpListener, TcpStream},
};

#[derive(Debug)]
pub struct Server {
    next_id: u16,
    port: u16,
    listener: TcpListener,
    handlers: Vec<ClientHandler>,
}

impl Server {
    pub fn new(config: Config) -> Result<Server, Box<dyn Error>> {
        trace!("Creating server with config: {:#?}", config);
        let listener_addr = format!("{}:{}", config.host, config.port);
        trace!("Creating TcpListener with addr: {:?}", listener_addr);
        let listener = TcpListener::bind(listener_addr)?;

        let server = Server {
            next_id: 0,
            port: config.port,
            listener,
            handlers: vec![],
        };

        debug!("Created successfully: {:#?}", server);
        Ok(server)
    }

    pub fn run(&mut self) -> Result<(), Box<dyn Error>> {
        trace!("Starting server...");

        info!("Listening to connections on port {}", self.port);
        loop {
            let connection = self.listener.accept();

            match connection {
                Ok((stream, addr)) => self.handle_new_connection(stream, addr)?,
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

    fn handle_new_connection(
        &mut self,
        stream: TcpStream,
        addr: SocketAddr,
    ) -> Result<(), Box<dyn Error>> {
        info!("New connection from {}", addr);
        let handler = ClientHandler::new(self.next_id, stream);
        self.next_id += 1;
        self.handlers.push(handler);

        Ok(())
    }

    fn join_threads(&mut self, wait: bool) {
        trace!("Joining client handlers... (wait: {})", wait);
        let mut handlers = vec![];
        for handler in self.handlers.pop() {
            if wait || handler.joineable() {
                handler.join();
            } else {
                handlers.push(handler);
            }
        }

        self.handlers = handlers;
    }
}
