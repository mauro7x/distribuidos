use crate::types::Message;
pub use crate::types::{MessageSender, QueueError, SharedMessageReceiver};
use std::thread;

use log::*;

pub struct Worker {
    pub id: usize,
    pub thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    pub fn new<C, H, T>(
        id: usize,
        receiver: SharedMessageReceiver<T>,
        context: C,
        handler: H,
    ) -> Worker
    where
        C: Send + 'static,
        H: Fn(&mut C, T) + Send + 'static,
        T: Send + 'static,
    {
        let thread = thread::spawn(move || Self::run(id, receiver, context, handler));

        Self {
            id,
            thread: Some(thread),
        }
    }

    fn run<C, H, T>(id: usize, receiver: SharedMessageReceiver<T>, mut context: C, handler: H)
    where
        H: Fn(&mut C, T) + Send + 'static,
        T: Send + 'static,
    {
        loop {
            let message = receiver.lock().unwrap().recv().unwrap();

            match message {
                Message::NewJob(job) => {
                    trace!("Worker #{} received job", id);
                    handler(&mut context, job);
                }
                Message::Terminate => {
                    trace!("Worker #{} was told to terminate", id);
                    break;
                }
            }
        }
    }
}
