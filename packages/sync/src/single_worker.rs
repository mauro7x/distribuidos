use crate::{
    constants::CHANNEL_CLOSED,
    types::{Message, MessageReceiver},
    MessageSender, QueueError,
};
use std::{
    sync::mpsc::{self, TrySendError},
    thread,
    time::Duration,
};

use log::{error, trace, warn};

pub struct SingleWorker<T: Send> {
    thread: Option<thread::JoinHandle<()>>,
    sender: MessageSender<T>,
}

impl<T> SingleWorker<T>
where
    T: 'static + Send,
{
    pub fn new<C, F>(
        max_jobs_queue: usize,
        context: C,
        handler: F,
        timeout: Duration,
    ) -> SingleWorker<T>
    where
        C: Send + 'static,
        F: Fn(&mut C, Option<T>) + Send + 'static,
    {
        trace!("Creating WorkerPool...");
        assert!(max_jobs_queue > 0);

        let (sender, receiver) = mpsc::sync_channel(max_jobs_queue);
        let worker = thread::spawn(move || SingleWorker::run(receiver, context, handler, timeout));

        trace!("SingleWorker created");

        SingleWorker {
            thread: Some(worker),
            sender,
        }
    }

    pub fn send(sender: &MessageSender<T>, job: T) -> Result<(), QueueError<T>> {
        match sender.try_send(Message::NewJob(job)) {
            Ok(()) => {
                trace!("Job added to the queue");
                Ok(())
            }
            Err(TrySendError::Full(t)) => match t {
                Message::NewJob(job) => Err(QueueError::Full(job)),
                Message::Terminate => unreachable!(),
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

    pub fn stop(&self) {
        self.sender.send(Message::Terminate).unwrap();
    }

    pub fn join(&mut self) {
        trace!("Joining SingleWorker...");
        match self.thread.take() {
            Some(joiner) => match joiner.join() {
                Ok(_) => trace!("Worker joined"),
                Err(e) => error!("Error while joining Worker - {:?}", e),
            },
            None => {
                warn!("Attempt to already joined worker, ignoring");
            }
        }
    }

    fn run<C, F>(receiver: MessageReceiver<T>, mut context: C, handler: F, timeout: Duration)
    where
        C: Send + 'static,
        F: Fn(&mut C, Option<T>) + Send + 'static,
    {
        loop {
            let message = receiver.recv_timeout(timeout);

            match message {
                Ok(Message::NewJob(job)) => {
                    trace!("SingleWorker received job");
                    handler(&mut context, Some(job));
                }
                Ok(Message::Terminate) => {
                    trace!("SingleWorker was told to terminate");
                    break;
                }
                Err(_) => {
                    handler(&mut context, None);
                }
            }
        }
    }
}
