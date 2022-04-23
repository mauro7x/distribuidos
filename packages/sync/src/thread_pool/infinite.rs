use super::{
    types::{Message, MessageSender},
    worker::Worker,
};
use std::sync::{mpsc, Arc, Mutex};

use log::trace;

pub struct ThreadPool {
    workers: Vec<Worker>,
    sender: MessageSender,
}

/// Static thread pool to execute tasks with a fixed number of threads.
impl ThreadPool {
    /// Create a new ThreadPool.
    ///
    /// ## Arguments
    /// * `size`: number of threads in the pool.
    ///
    /// ## Panics
    /// Function will panic if the size is zero.
    pub fn new(size: usize) -> ThreadPool {
        trace!("Creating ThreadPool...");
        assert!(size > 0);

        let (sender, receiver) = mpsc::channel();
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);

        trace!("Creating ThreadPool with size {}...", size);
        for id in 0..size {
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }
        trace!("ThreadPool created");

        ThreadPool { workers, sender }
    }

    /// Queues a task for execution in the ThreadPool.
    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        let job = Box::new(f);
        self.sender.send(Message::NewJob(job)).unwrap();
        trace!("Job added to the queue");
    }

    /// Joins every worker gracefully, waiting for them to finish their work.
    ///
    /// ## Blocking operation
    /// This will block the invoking thread to wait every task to be completed.
    pub fn join(&mut self) {
        trace!("Joining workers...");
        for _ in &mut self.workers {
            self.sender.send(Message::Terminate).unwrap();
        }
        trace!("Terminate message sent to all workers");

        for worker in &mut self.workers {
            if let Some(thread) = worker.thread.take() {
                thread.join().unwrap();
                trace!("Worker #{} joined", worker.id);
            }
        }
        trace!("Workers joined");
    }
}
