use crate::opcodes::*;
use distribuidos_types::BoxResult;
use std::{io::Write, net::TcpStream};

pub fn send_close_req(stream: &mut TcpStream) -> BoxResult<()> {
    stream.write_all(&[OP_TERMINATE])?;

    Ok(())
}
