use crate::{
    opcodes::*,
    reader::Reader,
    types::{
        errors::{QueryError, SendError},
        QueryResult,
    },
    writer::Writer,
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

pub fn send_query_error(stream: &mut TcpStream, error: QueryError) -> Result<(), Error> {
    let opcode = match error {
        QueryError::MetricNotFound => OP_METRIC_NOT_FOUND,
        QueryError::InvalidRange => OP_INVALID_RANGE,
        QueryError::InvalidAggrWindow => OP_INVALID_AGGR_WINDOW,
        QueryError::IOError(_) | QueryError::InternalServerError => OP_INTERNAL_SERVER_ERROR,
    };
    stream.write_all(&[opcode])?;

    Ok(())
}

pub fn send_query_result(stream: &mut TcpStream, query_result: QueryResult) -> Result<(), Error> {
    let mut writer = Writer::new(stream);
    writer.query_result(query_result)?;

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

pub fn recv_query_result(stream: &TcpStream) -> Result<QueryResult, QueryError> {
    let mut reader = Reader::new(stream);
    reader.query_result()
}
