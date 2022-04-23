use super::types::{Message, SharedMessageReceiver};
use std::thread;

use log::trace;

pub struct Worker {
    pub id: usize,
    pub thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    pub fn new(id: usize, receiver: SharedMessageReceiver) -> Worker {
        let thread = thread::spawn(move || Worker::run(id, receiver));

        Worker {
            id,
            thread: Some(thread),
        }
    }

    fn run(id: usize, receiver: SharedMessageReceiver) {
        loop {
            let message = receiver.lock().unwrap().recv().unwrap();

            match message {
                Message::NewJob(job) => {
                    trace!("Worker #{} received job", id);
                    job.call_box();
                }
                Message::Terminate => {
                    trace!("Worker #{} was told to terminate", id);
                    break;
                }
            }
        }
    }
}
