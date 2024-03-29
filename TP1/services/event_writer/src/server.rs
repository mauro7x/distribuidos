use crate::{EventDispatchers, WriteWorkerPool};
use distribuidos_ingress::Server;
use distribuidos_sync::QueueError;
use distribuidos_tp1_protocols::{
    requests, responses,
    types::{errors::RecvError, Event},
};
use distribuidos_types::BoxResult;
use std::net::TcpStream;

use log::*;

#[derive(Clone)]
pub struct Context {
    dispatchers: EventDispatchers,
}

pub fn new(write_worker_pool: &WriteWorkerPool) -> BoxResult<Server> {
    let server_context = Context {
        dispatchers: write_worker_pool.get_dispatchers(),
    };
    let server = Server::new(server_context, connection_handler)?;

    Ok(server)
}

fn connection_handler(Context { dispatchers }: &mut Context, stream: TcpStream) {
    if let Err(err) = inner_connection_handler(dispatchers, stream) {
        warn!("Connection handler failed - {:?}", err);
    }
}

fn inner_connection_handler(
    dispatchers: &EventDispatchers,
    mut stream: TcpStream,
) -> BoxResult<()> {
    trace!("Handling connection from {:?}", stream);
    match requests::recv_event(&mut stream) {
        Ok(event) => dispatch_event(dispatchers, stream, event),
        Err(RecvError::Invalid) => {
            warn!("Invalid format while receiving event");
            responses::send_invalid_format(&mut stream).map_err(|e| e.into())
        }
        Err(RecvError::Terminated) => Ok(()),
        Err(RecvError::IOError(e)) => Err(e.into()),
    }
}

fn dispatch_event(
    dispatchers: &EventDispatchers,
    mut stream: TcpStream,
    event: Event,
) -> BoxResult<()> {
    debug!("Event received: {:?}", event);

    match WriteWorkerPool::dispatch(dispatchers, event) {
        Ok(()) => {
            trace!("Event dispatched");
            responses::send_event_received(&mut stream)?
        }
        Err(QueueError::Full(_)) => {
            warn!("Event rejected: server at capacity");
            responses::send_server_at_capacity(&mut stream)?
        }
    };

    Ok(())
}
