use distribuidos_tp1_protocols::types::Event;
use std::net::TcpStream;

#[derive(Debug)]
pub struct EventRequest {
    pub event: Event,
    pub stream: TcpStream,
}
