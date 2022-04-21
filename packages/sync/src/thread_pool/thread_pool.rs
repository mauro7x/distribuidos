use super::{
    types::{Message, MessageSender},
    worker::Worker,
};
use std::sync::{mpsc, Arc, Mutex};

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
        assert!(size > 0);

        let (sender, receiver) = mpsc::channel();
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);

        for id in 0..size {
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }

        ThreadPool { workers, sender }
    }

    /// Queues a task for execution in the ThreadPool.
    pub fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        let job = Box::new(f);
        self.sender.send(Message::NewJob(job)).unwrap();
    }

    /// Joins every worker gracefully, waiting for them to finish their work.
    ///
    /// ## Blocking operation
    /// This will block the invoking thread to wait every task to be completed.
    fn join(&mut self) {
        for _ in &mut self.workers {
            self.sender.send(Message::Terminate).unwrap();
        }

        for worker in &mut self.workers {
            if let Some(thread) = worker.thread.take() {
                thread.join().unwrap();
            }
        }
    }
}

impl Drop for ThreadPool {
    /// **Warning:** since this calls join, function will block the invoking thread to wait every task to be completed.
    fn drop(&mut self) {
        self.join();
    }
}
