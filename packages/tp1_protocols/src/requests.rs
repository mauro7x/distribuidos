use crate::{
    opcodes::*,
    reader::Reader,
    types::{
        errors::{RecvError, SendError},
        Event, Query,
    },
    writer::Writer,
};
use std::{
    io::{Error, Write},
    net::TcpStream,
};

// Send

pub fn send_close(stream: &mut TcpStream) -> Result<(), Error> {
    stream.write_all(&[OP_TERMINATE])?;

    Ok(())
}

pub fn send_event(stream: &TcpStream, event: Event) -> Result<(), SendError> {
    let mut writer = Writer::new(stream);
    writer.event(event)?;

    Ok(())
}

pub fn send_query(stream: &TcpStream, query: Query) -> Result<(), SendError> {
    let mut writer = Writer::new(stream);
    writer.query(query)?;

    Ok(())
}

// Receive

pub fn recv_event(stream: &mut TcpStream) -> Result<Event, RecvError> {
    let mut reader = Reader::new(stream);
    reader.event()
}

pub fn recv_query(stream: &mut TcpStream) -> Result<Query, RecvError> {
    let mut reader = Reader::new(stream);
    reader.query()
}
