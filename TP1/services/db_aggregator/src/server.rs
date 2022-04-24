use distribuidos_ingress::Server;
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

fn inner_connection_handler(stream: TcpStream) -> BoxResult<()> {
    trace!("Handling connection from {:?}", stream);

    Ok(())
}