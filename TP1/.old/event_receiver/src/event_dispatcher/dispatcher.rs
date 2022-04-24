use super::config::Config;
use crate::types::EventRequest;
use distribuidos_sync::{MessageSender, QueueError, WorkerPool};
use distribuidos_tp1_protocols::{events, responses, types::errors::SendError};
use distribuidos_types::BoxResult;
use std::net::TcpStream;

use log::*;

pub type Dispatcher = MessageSender<EventRequest>;

#[derive(Clone)]
pub struct Context {
    db_addr: String, // Eventually, we could keep an opened TCP connection
}

pub struct EventDispatcher {
    pool: WorkerPool<EventRequest>,
}

impl EventDispatcher {
    pub fn new() -> BoxResult<EventDispatcher> {
        trace!("Creating EventDispatcher...");
        let config = Config::new()?;
        debug!("EventDispatcher config: {:?}", config);
        let Config {
            db_host,
            db_port,
            thread_pool_size,
            queue_size,
        } = config;
        let dispatcher_context = Context {
            db_addr: format!("{}:{}", db_host, db_port),
        };
        let pool = WorkerPool::new(
            thread_pool_size,
            queue_size,
            dispatcher_context,
            EventDispatcher::event_handler,
        );
        let dispatcher = EventDispatcher { pool };
        trace!("EventDispatcher created");

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

    fn event_handler(context: &mut Context, request: EventRequest) {
        if let Err(err) = EventDispatcher::inner_event_handler(&context.db_addr, request) {
            warn!("Event handler failed - {:?}", err);
        }
    }

    fn inner_event_handler(db_addr: &String, request: EventRequest) -> BoxResult<()> {
        let EventRequest { event, mut stream } = request;

        let db_stream = TcpStream::connect(db_addr).map_err(|err| {
            let _ = responses::send_internal_server_error_res(&mut stream);
            err
        })?;

        debug!("Event dispatched to Database");
        match events::send(&db_stream, event)? {
            Ok(_) => responses::send_event_received_res(&mut stream)?,
            Err(SendError::ServerAtCapacity) => {
                responses::send_server_at_capacity_res(&mut stream)?
            }
            Err(err) => {
                error!("Got {:?} event message from db", err);
                unreachable!()
            }
        };

        Ok(())
    }
}
