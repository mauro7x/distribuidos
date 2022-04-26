use crate::{
    opcodes::*,
    reader::Reader,
    types::{errors::SendError, QueryResult},
};
use std::{
    io::{Error, Write},
    net::TcpStream,
};

// Send

pub fn send_event_received(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_EVENT_RECEIVED])?;

    Ok(())
}

pub fn send_query_accepted(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_QUERY_ACCEPTED])?;

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

pub fn send_metric_not_found(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_METRIC_NOT_FOUND])?;

    Ok(())
}

pub fn send_invalid_range(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_INVALID_RANGE])?;

    Ok(())
}

pub fn send_invalid_aggr_window(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_INVALID_AGGR_WINDOW])?;

    Ok(())
}

pub fn send_query_response(
    _stream: &mut TcpStream,
    _query_result: QueryResult,
) -> Result<(), Error> {
    todo!();

    // Ok(())
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

pub fn recv_query_response(_stream: &mut TcpStream) -> Result<QueryResult, Error> {
    todo!();

    // Ok(())
}
