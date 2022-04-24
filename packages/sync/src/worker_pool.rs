pub use crate::types::{MessageSender, QueueError, SharedMessageReceiver};
use crate::{constants::CHANNEL_CLOSED, types::Message};
use std::{
    sync::{
        mpsc::{self, TrySendError},
        Arc, Mutex,
    },
    thread,
};

use log::{error, trace};

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

    pub fn execute(&self, job: T) -> Result<(), QueueError<T>> {
        Self::send(&self.sender, job)
    }

    pub fn send(sender: &MessageSender<T>, job: T) -> Result<(), QueueError<T>> {
        match sender.try_send(Message::NewJob(job)) {
            Ok(()) => {
                trace!("Job added to the queue");
                Ok(())
            }
            Err(TrySendError::Full(t)) => match t {
                Message::NewJob(job) => Err(QueueError::Full(job)),
                Message::Terminate => panic!("Should never get here"),
            },
            Err(TrySendError::Disconnected(_)) => {
                error!("{}", CHANNEL_CLOSED);
                panic!("{}", CHANNEL_CLOSED);
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
