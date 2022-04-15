use log::{debug, info, trace, warn};
use std::{
    error::Error,
    io::{Read, Write},
    net::{Shutdown, TcpStream},
    str,
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    thread::{self, JoinHandle},
};
use crate::constants::MAX_LEN;

/// ## Arguments
/// 
/// * `id` (self-descriptive).
/// * `finished`: AtomicBool used to check if thread executing has finished
/// and can be joined in a non-blocking way.
/// * `joiner`: `JoinHandle`r received from thread spawn.
#[derive(Debug)]
pub struct ClientHandler {
    id: u16,
    finished: Arc<AtomicBool>,
    joiner: Option<JoinHandle<()>>,
}

impl ClientHandler {
    /// Creates a ClientHandler, setting stream received as blocking,
    /// and spawning a thread to execute the inner handler.
    pub fn new(id: u16, stream: TcpStream) -> Result<ClientHandler, Box<dyn Error>> {
        trace!("Creating ClientHandler for client #{}", id);
        stream.set_nonblocking(false)?;
        let finished = Arc::new(AtomicBool::new(false));
        let cloned_finished = finished.clone();
        trace!("[#{}] Spawning thread...", id);
        let joiner = thread::spawn(move || ClientHandler::handle(id, cloned_finished, stream));
        let client_handler = ClientHandler {
            id,
            finished,
            joiner: Some(joiner),
        };

        debug!("[#{}] Created successfully: {:#?}", id, client_handler);
        Ok(client_handler)
    }

    /// Main thread handler function, calls `inner_handler` and catches
    /// errors, logging a warning in case of any. Finally, flags `ClientHandler`
    /// as finished.
    fn handle(id: u16, finished: Arc<AtomicBool>, stream: TcpStream) {
        trace!("[#{}] Starting handler execution", id);

        if let Err(e) = ClientHandler::inner_handler(id, stream) {
            warn!("[#{}] Error while handling client: {:?}", id, e);
        }

        finished.store(true, Ordering::Relaxed);
        trace!("[#{}] Handler execution finished", id);
    }

    /// Actual logic handler that will execute the protocol
    /// to perform as an echo server with the client connection.
    fn inner_handler(id: u16, mut stream: TcpStream) -> Result<(), Box<dyn Error>> {
        let mut data = [0_u8; MAX_LEN];

        trace!("[#{}] Receiving data from client...", id);
        let size = stream.read(&mut data)?;
        info!(
            "[#{}] Received data from client: {:?}",
            id,
            str::from_utf8(&data[0..size])?
        );

        trace!("[#{}] Writing data to client...", id);
        stream.write_all(&data[0..size])?;
        debug!("[#{}] Wrote data to client", id);

        if let Err(e) = stream.shutdown(Shutdown::Both) {
            warn!("[#{}] Error while shutting client down: {}", id, e)
        };

        Ok(())
    }

    /// Checks if handler is joineable without blocking
    pub fn joineable(&self) -> bool {
        self.finished.load(Ordering::Relaxed)
    }

    /// Joins client handler, blocking if it has not finished.
    /// 
    /// (nit: you might want to use `joineable` to be sure it can be joined
    /// without blocking!)
    pub fn join(self) {
        trace!("[#{}] Joining...", self.id);

        match self.joiner {
            Some(joiner) => {
                if let Err(e) = joiner.join() {
                    warn!("[#{}] Error while joining thread: {:?}", self.id, e);
                };
                debug!("[#{}] Joined successfully", self.id)
            }
            None => warn!(
                "[#{}] Attempt to join a ClientHandler without joiner",
                self.id
            ),
        }
    }
}
