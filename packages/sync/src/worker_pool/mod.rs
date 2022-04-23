pub mod types;
mod worker;

pub use self::types::MessageSender;
use self::{
    types::{ExecuteError, Message},
    worker::Worker,
};
use std::sync::{
    mpsc::{self, TrySendError},
    Arc, Mutex,
};

use log::{error, trace};

pub struct WorkerPool<T: Send> {
    workers: Vec<Worker>,
    sender: MessageSender<T>,
}

impl<T> WorkerPool<T>
where
    T: 'static + Send,
{
    pub fn new<C, F>(size: usize, max_jobs_queue: usize, context: C, handler: F) -> WorkerPool<T>
    where
        C: Clone + Send + 'static,
        F: Fn(&mut C, T) + Copy + Send + 'static,
    {
        trace!("Creating WorkerPool...");
        assert!(size > 0);
        assert!(max_jobs_queue > 0);

        let (sender, receiver) = mpsc::sync_channel(max_jobs_queue);
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);

        trace!("Creating WorkerPool with size {}...", size);
        for id in 0..size {
            let worker = Worker::new(id, Arc::clone(&receiver), context.clone(), handler);
            workers.push(worker);
        }
        trace!("WorkerPool created");

        Self { workers, sender }
    }

    pub fn execute(&self, job: T) -> Result<(), ExecuteError> {
        Self::send(&self.sender, job)
    }

    pub fn send(sender: &MessageSender<T>, job: T) -> Result<(), ExecuteError> {
        match sender.try_send(Message::NewJob(job)) {
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

    pub fn clone_sender(&self) -> MessageSender<T> {
        self.sender.clone()
    }

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
