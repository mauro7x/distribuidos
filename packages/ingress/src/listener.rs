use super::{config::Config, types::InitError};
use std::net::TcpListener;

pub fn new_listener() -> Result<TcpListener, InitError> {
    let Config { host, port } = Config::new().map_err(|_| InitError::ConfigError)?;

    let listener_addr = format!("{}:{}", host, port);
    let listener = TcpListener::bind(listener_addr).map_err(|_| InitError::BindError)?;

    Ok(listener)
}
