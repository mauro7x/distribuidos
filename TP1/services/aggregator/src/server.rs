use crate::{types::QueryRequest, QueryHandler};
use distribuidos_ingress::Server;
use distribuidos_sync::{MessageSender, QueueError, WorkerPool};
use distribuidos_tp1_protocols::{
    requests, responses,
    types::{errors::RecvError, Query},
};
use distribuidos_types::BoxResult;
use std::net::TcpStream;

use log::*;

type Dispatcher = MessageSender<QueryRequest>;

#[derive(Clone)]
pub struct Context {
    dispatcher: Dispatcher,
}

pub fn new(query_handler: &QueryHandler) -> BoxResult<Server> {
    let server_context = Context {
        dispatcher: query_handler.clone_sender(),
    };
    let server = Server::new(server_context, connection_handler)?;

    Ok(server)
}

fn connection_handler(Context { dispatcher }: &mut Context, stream: TcpStream) {
    if let Err(err) = inner_connection_handler(dispatcher, stream) {
        warn!("Connection handler failed - {:?}", err);
    }
}

fn inner_connection_handler(dispatcher: &Dispatcher, mut stream: TcpStream) -> BoxResult<()> {
    trace!("Handling connection from {:?}", stream);
    match requests::recv_query(&mut stream) {
        Ok(query) => dispatch_query(dispatcher, stream, query),
        Err(RecvError::Invalid) => {
            warn!("Invalid format while receiving query");
            responses::send_invalid_format(&mut stream).map_err(|e| e.into())
        }
        Err(RecvError::Terminated) => Ok(()),
        Err(RecvError::IOError(e)) => Err(e.into()),
    }
}

fn dispatch_query(dispatcher: &Dispatcher, mut stream: TcpStream, query: Query) -> BoxResult<()> {
    debug!("Query received: {:?}", query);

    // We could avoid this if we do not send ACK
    let cloned_stream = stream.try_clone().unwrap();

    let query_request = QueryRequest {
        stream: cloned_stream,
        query,
    };

    match WorkerPool::send(dispatcher, query_request) {
        Ok(()) => {
            trace!("Query dispatched");
            responses::send_query_accepted(&mut stream)?
        }
        Err(QueueError::Full(QueryRequest {
            mut stream,
            query: _,
        })) => {
            warn!("Event rejected: server at capacity");
            responses::send_server_at_capacity(&mut stream)?
        }
    };

    Ok(())
}
