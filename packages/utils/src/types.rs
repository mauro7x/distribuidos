use std::{
    io::{BufReader, BufWriter},
    net::TcpStream,
};

pub type TcpReader<'a> = BufReader<&'a TcpStream>;
pub type TcpWriter<'a> = BufWriter<&'a TcpStream>;
