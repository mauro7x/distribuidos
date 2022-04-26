mod config;
mod constants;
mod event_writer;
mod metric_file;

use self::{config::Config, event_writer::EventWriter};
use distribuidos_sync::{MessageSender, QueueError, SingleWorkerTimeout};
use distribuidos_tp1_protocols::types::Event;
use distribuidos_tp1_utils::hash;
use distribuidos_types::BoxResult;
use std::{io::Error, time::Duration};

use log::*;

struct Context {
    id: usize,
    event_writer: EventWriter,
}

pub type EventDispatcher = MessageSender<Event>;
pub type EventDispatchers = Vec<EventDispatcher>;

pub struct WriteWorkerPool {
    workers: Vec<SingleWorkerTimeout<Event>>,
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
            partition_secs,
            database_path,
        } = config;

        let mut workers = Vec::with_capacity(worker_pool_size);
        for id in 0..worker_pool_size {
            let event_writer = EventWriter::new(database_path.clone(), partition_secs);
            let context = Context { id, event_writer };
            let worker = SingleWorkerTimeout::<Event>::new(
                worker_queue_size,
                context,
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
        let worker_id = hash::assign_worker(&event.metric_id, dispatchers.len());
        let dispatcher = &dispatchers[worker_id];

        SingleWorkerTimeout::send(dispatcher, event)
    }

    fn worker_handler(context: &mut Context, job: Option<Event>) {
        if let Err(err) = WriteWorkerPool::inner_handler(context, job) {
            warn!("[WriteWorker #{}] Failed - {}", context.id, err);
        }
    }

    fn inner_handler(
        Context { id, event_writer }: &mut Context,
        job: Option<Event>,
    ) -> Result<(), Error> {
        match job {
            Some(event) => {
                debug!("[WriteWorker #{}] Received event: {:?}", id, event);
                event_writer.write(event)?;
                debug!("[WriteWorker #{}] Event written to database", id);
                Ok(())
            }
            None => event_writer.handle_timeout(),
        }
    }
}
