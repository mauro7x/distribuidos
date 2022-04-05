use log::{debug, info, trace, warn};
use std::{
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

#[derive(Debug)]
pub struct ClientHandler {
    id: u16,
    finished: Arc<AtomicBool>,
    joiner: Option<JoinHandle<()>>,
}

impl ClientHandler {
    pub fn new(id: u16, stream: TcpStream) -> ClientHandler {
        trace!("Creating ClientHandler for client #{}", id);
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
        client_handler
    }

    fn handle(id: u16, finished: Arc<AtomicBool>, mut stream: TcpStream) {
        trace!("[#{}] Starting handler execution", id);

        let mut data = [0 as u8; MAX_LEN];
        trace!("[#{}] Receiving data from client...", id);
        let received = stream.read(&mut data);
        match received {
            Ok(size) => {
                info!(
                    "[#{}] Received data from client: {:?}",
                    id,
                    str::from_utf8(&data[0..size]).unwrap_or("could not convert data to string")
                );

                trace!("[#{}] Writing data to client...", id);
                if let Err(e) = stream.write(&data[0..size]) {
                    warn!("[#{}] Error while writing data to client: {}", id, e);
                };
            }
            Err(e) => warn!("[#{}] Error while receiving data from client: {}", id, e),
        }

        if let Err(e) = stream.shutdown(Shutdown::Both) {
            warn!("[#{}] Error while shutting client down: {}", id, e)
        };

        finished.store(true, Ordering::Relaxed);
        trace!("[#{}] Handler execution finished", id);
    }

    pub fn joineable(&self) -> bool {
        self.finished.load(Ordering::Relaxed)
    }

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
