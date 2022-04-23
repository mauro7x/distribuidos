use super::{
    types::{ExecuteError, Message, MessageSyncSender},
    worker::Worker,
};
use std::sync::{
    mpsc::{self, TrySendError},
    Arc, Mutex,
};

use log::{error, trace};

pub struct BoundedThreadPool {
    workers: Vec<Worker>,
    sender: MessageSyncSender,
}

/// Static thread pool to execute tasks with a fixed number of threads.
impl BoundedThreadPool {
    /// Create a new BoundedThreadPool.
    ///
    /// ## Arguments
    /// * `size`: number of threads in the pool.
    /// * `max_jobs_queue`: max number of jobs waiting to be executed.
    ///
    /// ## Panics
    /// Function will panic if any parameter is zero.
    pub fn new(size: usize, max_jobs_queue: usize) -> BoundedThreadPool {
        trace!("Creating BoundedThreadPool...");
        assert!(size > 0);
        assert!(max_jobs_queue > 0);

        let (sender, receiver) = mpsc::sync_channel(max_jobs_queue);
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);

        trace!("Creating BoundedThreadPool with size {}...", size);
        for id in 0..size {
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }
        trace!("BoundedThreadPool created");

        BoundedThreadPool { workers, sender }
    }

    /// Queues a task for execution in the BoundedThreadPool.
    pub fn execute<F>(&self, f: F) -> Result<(), ExecuteError>
    where
        F: FnOnce() + Send + 'static,
    {
        let job = Box::new(f);

        match self.sender.try_send(Message::NewJob(job)) {
            Ok(()) => {
                trace!("Job added to the queue");
                Ok(())
            }
            Err(TrySendError::Full(_)) => Err(ExecuteError::Full),
            Err(TrySendError::Disconnected(_)) => {
                let msg = "Channel closed by receivers";
                error!("{}", msg);
                panic!("{}", msg);
            }
        }
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
