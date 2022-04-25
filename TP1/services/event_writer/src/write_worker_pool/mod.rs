mod config;
mod constants;

use self::config::Config;
use distribuidos_sync::{MessageSender, QueueError, SingleWorker};
use distribuidos_tp1_protocols::types::Event;
use distribuidos_types::BoxResult;
use std::{
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
    time::Duration,
};

use log::*;

#[derive(Clone)]
struct Context {
    id: usize,
}

pub type EventDispatcher = MessageSender<Event>;
pub type EventDispatchers = Vec<EventDispatcher>;

pub struct WriteWorkerPool {
    workers: Vec<SingleWorker<Event>>,
}

impl WriteWorkerPool {
    pub fn new() -> BoxResult<WriteWorkerPool> {
        trace!("Creating WriteWorkerPool...");
        let config = Config::new()?;
        debug!("WriteWorkerPool - {:?}", config);
        let Config {
            flush_timeout_ms,
            worker_pool_size,
            worker_queue_size,
        } = config;
        let mut workers = Vec::with_capacity(worker_pool_size);
        for id in 0..worker_pool_size {
            let worker = SingleWorker::<Event>::new(
                worker_queue_size,
                Context { id },
                WriteWorkerPool::worker_handler,
                Duration::from_millis(flush_timeout_ms),
            );
            workers.push(worker);
        }
        let pool = WriteWorkerPool { workers };
        trace!("WriteWorkerPool created");

        Ok(pool)
    }

    pub fn join(&mut self) {
        trace!("Joining workers. Sending terminate message...");
        for worker in &mut self.workers {
            worker.stop();
        }
        trace!("Terminate message sent to all workers. Joining...");
        for worker in &mut self.workers {
            worker.join();
        }
        trace!("Workers joined");
    }

    pub fn get_dispatchers(&self) -> EventDispatchers {
        self.workers
            .iter()
            .map(|worker| worker.clone_sender())
            .collect()
    }

    pub fn dispatch(dispatchers: &EventDispatchers, event: Event) -> Result<(), QueueError<Event>> {
        let mut hasher = DefaultHasher::new();
        event.metric_id.hash(&mut hasher);
        let hashed_event_id = hasher.finish() as usize;
        let n_workers = dispatchers.len();
        let worker_id = hashed_event_id % n_workers;
        let dispatcher = &dispatchers[worker_id];

        SingleWorker::send(dispatcher, event)
    }

    fn worker_handler(Context { id }: &mut Context, job: Option<Event>) {
        if let Err(err) = WriteWorkerPool::inner_handler(*id, job) {
            warn!("Write Worker failed - {}", err);
        }
    }

    fn inner_handler(id: usize, job: Option<Event>) -> BoxResult<()> {
        match job {
            Some(event) => WriteWorkerPool::handle_event(id, event),
            None => WriteWorkerPool::handle_timeout(),
        }
    }

    fn handle_event(id: usize, event: Event) -> BoxResult<()> {
        debug!("[WriteWorker #{}] Received event: {:?}", id, event);
        Ok(())
    }

    fn handle_timeout() -> BoxResult<()> {
        Ok(())
    }
}
