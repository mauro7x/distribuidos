use super::config::Config;
use std::{error::Error, net::TcpListener};

pub fn new_listener() -> Result<TcpListener, Box<dyn Error>> {
    let Config { host, port } = Config::new()?;

    let listener_addr = format!("{}:{}", host, port);
    let listener = TcpListener::bind(listener_addr)?;

    Ok(listener)
}
