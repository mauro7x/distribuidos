use std::{
    sync::mpsc::{Receiver, TryRecvError},
    thread,
};

use crate::config::Config;
use distribuidos_types::BoxResult;

pub struct Dispatcher {
    frequency_secs: u32,
    ctrlc_receiver: Receiver<()>,
}

impl Dispatcher {
    pub fn new(rx: Receiver<()>) -> BoxResult<Dispatcher> {
        let Config { frequency_secs } = Config::new()?;
        let dispatcher = Dispatcher {
            frequency_secs,
            ctrlc_receiver: rx,
        };

        Ok(dispatcher)
    }

    pub fn run(&self) -> BoxResult<()> {
        loop {
            if self.stopped()? {
                break;
            }

            thread::sleep(std::time::Duration::from_millis(100));
        }
        Ok(())
    }

    fn stopped(&self) -> BoxResult<bool> {
        match self.ctrlc_receiver.try_recv() {
            Ok(_) => Ok(true),
            Err(TryRecvError::Empty) => Ok(false),
            Err(TryRecvError::Disconnected) => {
                Err("Ctrl-C signal receiver disconnected unexpectedly".into())
            }
        }
    }
}
