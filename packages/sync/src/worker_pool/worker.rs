use super::types::{Message, SharedMessageReceiver};
use std::thread;

use log::trace;

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
        H: Fn(usize, &mut C, T) + Send + 'static,
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
        H: Fn(usize, &mut C, T) + Send + 'static,
        T: Send + 'static,
    {
        loop {
            let message = receiver.lock().unwrap().recv().unwrap();

            match message {
                Message::NewJob(job) => {
                    trace!("Worker #{} received job", id);
                    handler(id, &mut context, job);
                }
                Message::Terminate => {
                    trace!("Worker #{} was told to terminate", id);
                    break;
                }
            }
        }
    }
}
