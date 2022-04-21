use super::types::{Message, SharedMessageReceiver};
use std::thread;

pub struct Worker {
    pub id: usize,
    pub thread: Option<thread::JoinHandle<()>>,
}

impl Worker {
    pub fn new(id: usize, receiver: SharedMessageReceiver) -> Worker {
        let thread = thread::spawn(move || Worker::run(receiver));

        Worker {
            id,
            thread: Some(thread),
        }
    }

    fn run(receiver: SharedMessageReceiver) {
        loop {
            let message = receiver.lock().unwrap().recv().unwrap();

            match message {
                Message::NewJob(job) => {
                    job.call_box();
                }
                Message::Terminate => {
                    break;
                }
            }
        }
    }
}
