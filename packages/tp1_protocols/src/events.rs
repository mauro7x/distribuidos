use crate::{
    opcodes::*,
    types::{
        errors::{RecvError, RecvResult, SendError, SendResult},
        Event,
    },
};
use distribuidos_types::BoxResult;
use distribuidos_utils::{
    read_n,
    types::{TcpReader, TcpWriter},
};
use std::{
    io::{BufReader, Read, Write},
    mem::size_of,
    net::TcpStream,
};

pub const MAX_EVENT_ID_LENGTH: u8 = 16;

// Send

pub fn send(stream: &TcpStream, event: Event) -> BoxResult<SendResult> {
    let mut writer = TcpWriter::new(stream);

    match send_event(&mut writer, event)? {
        Ok(_) => {
            let mut reader: TcpReader = BufReader::new(stream);
            let opcode = read_n(&mut reader, 1)?;

            let ret = match opcode[0] {
                OP_EVENT_RECEIVED => Ok(()),
                OP_INVALID_FORMAT => Err(SendError::Invalid),
                OP_SERVER_AT_CAPACITY => Err(SendError::ServerAtCapacity),
                OP_INTERNAL_SERVER_ERROR => Err(SendError::InternalServerError),
                op => panic!("Received unexpected opcode: {:?}", op),
            };

            Ok(ret)
        }
        Err(err) => Ok(Err(err)),
    }
}

fn send_event(writer: &mut TcpWriter, event: Event) -> BoxResult<SendResult> {
    writer.write_all(&[OP_EVENT])?;

    match event.id.len().try_into() {
        Ok(event_id_length) => {
            writer.write_all(&[event_id_length])?;
            writer.write_all(event.id.as_bytes())?;
            writer.write_all(&event.value.to_le_bytes())?;
            writer.flush()?;

            Ok(Ok(()))
        }
        Err(_) => Ok(Err(SendError::Invalid)),
    }
}

// Receive

pub fn recv(stream: &mut TcpStream) -> BoxResult<RecvResult> {
    let mut reader: TcpReader = BufReader::new(stream);
    let opcode = read_n(&mut reader, 1)?;

    match opcode[0] {
        OP_EVENT => recv_event(&mut reader),
        OP_TERMINATE => Ok(Err(RecvError::Terminated)),
        _ => Ok(Err(RecvError::Invalid)),
    }
}

fn recv_event(reader: &mut TcpReader) -> BoxResult<RecvResult> {
    match recv_event_id(reader)? {
        Ok(id) => {
            let value = recv_event_value(reader)?;
            Ok(Ok(Event { id, value }))
        }
        Err(err) => Ok(Err(err)),
    }
}

fn recv_event_id(reader: &mut TcpReader) -> BoxResult<Result<String, RecvError>> {
    let length_buf = read_n(reader, 1)?;

    let event_id_length = length_buf[0];
    if event_id_length == 0 || event_id_length > MAX_EVENT_ID_LENGTH {
        return Ok(Err(RecvError::Invalid));
    }

    let event_id_buf = read_n(reader, event_id_length.into())?;
    match std::str::from_utf8(&event_id_buf) {
        Ok(event_id) => Ok(Ok(event_id.to_string())),
        Err(_) => Ok(Err(RecvError::Invalid)),
    }
}

fn recv_event_value(reader: &mut TcpReader) -> BoxResult<f32> {
    let mut value_buf = [0; size_of::<f32>()];
    reader.read_exact(&mut value_buf)?;

    Ok(f32::from_le_bytes(value_buf))
}
