mod config;
mod constants;
mod event_reader;
mod types;
mod window;

use crate::{query_handler::config::Config, types::QueryRequest};
use distribuidos_sync::{MessageSender, QueueError, WorkerPool};
use distribuidos_tp1_protocols::{responses, types::errors::QueryError};
use distribuidos_types::BoxResult;
use std::io::Error;

use log::*;

use self::event_reader::EventReader;

pub type Dispatcher = MessageSender<QueryRequest>;

#[derive(Clone)]
struct Context {
    event_reader: EventReader,
}

pub struct QueryHandler {
    pool: WorkerPool<QueryRequest>,
}

impl QueryHandler {
    pub fn new() -> BoxResult<QueryHandler> {
        trace!("Creating QueryHandler...");
        let config = Config::new()?;
        debug!("QueryHandler config: {:?}", config);
        let Config {
            thread_pool_size,
            queue_size,
            partition_secs,
            database_path,
        } = config;
        let event_reader = EventReader::new(database_path, partition_secs);
        let context = Context { event_reader };
        let pool = WorkerPool::new(
            thread_pool_size,
            queue_size,
            context,
            QueryHandler::query_handler,
        );
        let dispatcher = QueryHandler { pool };
        trace!("QueryHandler created");

        Ok(dispatcher)
    }

    pub fn clone_sender(&self) -> Dispatcher {
        self.pool.clone_sender()
    }

    pub fn join(&mut self) {
        self.pool.join();
    }

    pub fn dispatch(
        dispatcher: Dispatcher,
        request: QueryRequest,
    ) -> Result<(), QueueError<QueryRequest>> {
        WorkerPool::send(&dispatcher, request)
    }

    fn query_handler(context: &mut Context, request: QueryRequest) {
        if let Err(err) = QueryHandler::inner_handler(context, request) {
            warn!("[QueryHandler] Failed - {}", err);
        }
    }

    fn inner_handler(
        Context { event_reader }: &mut Context,
        QueryRequest { mut stream, query }: QueryRequest,
    ) -> Result<(), Error> {
        debug!("[QueryHandler] Received query: {:?}", query);

        match event_reader.resolve(query) {
            Ok(query_result) => {
                info!("Query resolved: {:?}", query_result);
                responses::send_query_result(&mut stream, query_result)
            }
            Err(QueryError::IOError(e)) => {
                responses::send_query_error(&mut stream, QueryError::InternalServerError)?;
                Err(e)
            }
            Err(e) => responses::send_query_error(&mut stream, e),
        }
    }
}
