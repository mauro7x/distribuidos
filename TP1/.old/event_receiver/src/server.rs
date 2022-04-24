use crate::{types::EventRequest, Dispatcher};
use distribuidos_ingress::Server;
use distribuidos_sync::{QueueError, WorkerPool};
use distribuidos_tp1_protocols::{
    events, responses,
    types::{errors::RecvError, Event},
};
use distribuidos_types::BoxResult;
use std::net::TcpStream;

use log::*;

#[derive(Clone)]
pub struct Context {
    dispatcher: Dispatcher,
}

pub fn new(dispatcher: Dispatcher) -> BoxResult<Server> {
    let server_context = Context { dispatcher };
    let server = Server::new(server_context, connection_handler)?;

    Ok(server)
}

fn connection_handler(context: &mut Context, stream: TcpStream) {
    if let Err(err) = inner_connection_handler(&context.dispatcher, stream) {
        warn!("Connection handler failed - {:?}", err);
    }
}

fn inner_connection_handler(dispatcher: &Dispatcher, mut stream: TcpStream) -> BoxResult<()> {
    trace!("Handling connection from {:?}", stream);
    match events::recv(&mut stream)? {
        Ok(event) => dispatch_event(dispatcher, stream, event),
        Err(RecvError::Invalid) => {
            warn!("Invalid format while receiving event");
            responses::send_invalid_format_res(&mut stream)
        }
        Err(RecvError::Terminated) => Ok(()),
    }
}

fn dispatch_event(dispatcher: &Dispatcher, stream: TcpStream, event: Event) -> BoxResult<()> {
    debug!("Event received: {:?}", event);
    let event_request = EventRequest { event, stream };

    match WorkerPool::<EventRequest>::send(dispatcher, event_request) {
        Ok(()) => {
            trace!("Event dispatched");
        }
        Err(QueueError::Full(mut req)) => {
            warn!("Event rejected: server at capacity");
            responses::send_server_at_capacity_res(&mut req.stream)?
        }
    };

    Ok(())
}
