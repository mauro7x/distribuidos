use crate::{opcodes::*, reader::Reader, types::errors::SendError};
use std::{
    io::{Error, Write},
    net::TcpStream,
};

// Send

pub fn send_event_received(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_EVENT_RECEIVED])?;

    Ok(())
}

pub fn send_invalid_format(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_INVALID_FORMAT])?;

    Ok(())
}

pub fn send_server_at_capacity(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_SERVER_AT_CAPACITY])?;

    Ok(())
}

pub fn send_internal_server_error(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_INTERNAL_SERVER_ERROR])?;

    Ok(())
}

// Receive

pub fn recv_event_ack(stream: &TcpStream) -> Result<(), SendError> {
    let mut reader = Reader::new(stream);

    match reader.opcode()? {
        OP_EVENT_RECEIVED => Ok(()),
        OP_INVALID_FORMAT => Err(SendError::Invalid),
        OP_SERVER_AT_CAPACITY => Err(SendError::ServerAtCapacity),
        OP_INTERNAL_SERVER_ERROR => Err(SendError::InternalServerError),
        op => panic!("Received unexpected opcode: {:?}", op),
    }
}

pub fn recv_query_ack(stream: &TcpStream) -> Result<(), SendError> {
    let mut reader = Reader::new(stream);

    match reader.opcode()? {
        OP_QUERY_ACCEPTED => Ok(()),
        OP_INVALID_FORMAT => Err(SendError::Invalid),
        OP_SERVER_AT_CAPACITY => Err(SendError::ServerAtCapacity),
        OP_INTERNAL_SERVER_ERROR => Err(SendError::InternalServerError),
        op => panic!("Received unexpected opcode: {:?}", op),
    }
}
