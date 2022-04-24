use crate::opcodes::*;
use distribuidos_types::BoxResult;
use std::{io::Write, net::TcpStream};

pub fn send_event_received_res(stream: &mut TcpStream) -> BoxResult<()> {
    stream.write_all(&[OP_EVENT_RECEIVED])?;

    Ok(())
}

pub fn send_invalid_format_res(stream: &mut TcpStream) -> BoxResult<()> {
    stream.write_all(&[OP_INVALID_FORMAT])?;

    Ok(())
}

pub fn send_server_at_capacity_res(stream: &mut TcpStream) -> BoxResult<()> {
    stream.write_all(&[OP_SERVER_AT_CAPACITY])?;

    Ok(())
}

pub fn send_internal_server_error_res(stream: &mut TcpStream) -> BoxResult<()> {
    stream.write_all(&[OP_INTERNAL_SERVER_ERROR])?;

    Ok(())
}
