use distribuidos_ingress::Server;
use distribuidos_tp1_protocols::{
    events,
    responses::{self, send_event_received_res},
    types::{errors::RecvError, Event},
};
use distribuidos_types::BoxResult;
use std::net::TcpStream;

use log::*;

#[derive(Clone)]
pub struct Context {}

pub fn new() -> BoxResult<Server> {
    let server_context = Context {};
    let server = Server::new(server_context, connection_handler)?;

    Ok(server)
}

fn connection_handler(_context: &mut Context, stream: TcpStream) {
    if let Err(err) = inner_connection_handler(stream) {
        warn!("Connection handler failed - {:?}", err);
    }
}

fn inner_connection_handler(mut stream: TcpStream) -> BoxResult<()> {
    trace!("Handling connection from {:?}", stream);
    match events::recv(&mut stream)? {
        Ok(event) => dispatch_event(stream, event),
        Err(RecvError::Invalid) => {
            warn!("Invalid format while receiving event in database");
            responses::send_invalid_format_res(&mut stream)
        }
        Err(RecvError::Terminated) => Ok(()),
    }
}

fn dispatch_event(mut stream: TcpStream, event: Event) -> BoxResult<()> {
    debug!("Event received: {:?}", event);
    send_event_received_res(&mut stream)?;

    Ok(())
}
