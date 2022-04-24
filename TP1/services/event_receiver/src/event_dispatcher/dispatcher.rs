use super::config::Config;
use crate::types::EventRequest;
use distribuidos_sync::{MessageSender, QueueError, WorkerPool};
use distribuidos_tp1_protocols::responses;
use distribuidos_types::BoxResult;

use log::*;

pub type Dispatcher = MessageSender<EventRequest>;

#[derive(Clone)]
pub struct Context {}

pub struct EventDispatcher {
    pool: WorkerPool<EventRequest>,
}

impl EventDispatcher {
    pub fn new() -> BoxResult<EventDispatcher> {
        trace!("Creating EventDispatcher...");
        let config = Config::new()?;
        let Config {
            thread_pool_size,
            queue_size,
        } = config;
        let pool = WorkerPool::new(
            thread_pool_size,
            queue_size,
            Context {},
            EventDispatcher::event_handler,
        );
        let dispatcher = EventDispatcher { pool };
        trace!("EventDispatcher created with config: {:?}", config);

        Ok(dispatcher)
    }

    pub fn clone_dispatcher(&self) -> Dispatcher {
        self.pool.clone_sender()
    }

    pub fn join(&mut self) {
        self.pool.join();
    }

    // Static

    pub fn dispatch(
        dispatcher: Dispatcher,
        request: EventRequest,
    ) -> Result<(), QueueError<EventRequest>> {
        WorkerPool::send(&dispatcher, request)
    }

    fn event_handler(_context: &mut Context, request: EventRequest) {
        if let Err(err) = EventDispatcher::inner_event_handler(request) {
            warn!("Event handler failed - {:?}", err);
        }
    }

    fn inner_event_handler(request: EventRequest) -> BoxResult<()> {
        let EventRequest {
            event: _,
            mut stream,
        } = request;

        // Temp: until we have database, we ack event received.
        // Here we should send event to db and wait for answer.
        responses::send_event_received_res(&mut stream)?;
        debug!("Event dispatcher to db (NOT YET)");

        Ok(())
    }
}
