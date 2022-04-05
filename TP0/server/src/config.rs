use crate::constants::{
    CONFIG_FILE_PATH, DEFAULT_HOST, DEFAULT_LISTEN_BACKLOG, DEFAULT_LOGGING_LEVEL, DEFAULT_PORT,
    HOST_ENV, LISTEN_BACKLOG_ENV, LOGGING_LEVEL_ENV, PORT_ENV,
};
use serde::Deserialize;
use std::{env::var, error::Error};

#[derive(Debug, Deserialize)]
struct PartialConfig {
    server_ip: Option<String>,
    server_port: Option<u16>,
    server_listen_backlog: Option<u16>,
    logging_level: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct Config {
    pub host: String,
    pub port: u16,
    pub listen_backlog: u16,
    pub logging_level: String,
}

impl Config {
    pub fn new() -> Result<Self, Box<dyn Error>> {
        let data = std::fs::read_to_string(CONFIG_FILE_PATH)?;
        let file_config: PartialConfig = serde_json::from_str(&data)?;
        let config = Config {
            host: var(HOST_ENV)
                .unwrap_or_else(|_| file_config.server_ip.unwrap_or(DEFAULT_HOST.to_string())),
            port: var(PORT_ENV)
                .unwrap_or_else(|_| file_config.server_port.unwrap_or(DEFAULT_PORT).to_string())
                .parse()?,
            listen_backlog: var(LISTEN_BACKLOG_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .server_listen_backlog
                        .unwrap_or(DEFAULT_LISTEN_BACKLOG)
                        .to_string()
                })
                .parse()?,
            logging_level: var(LOGGING_LEVEL_ENV).unwrap_or_else(|_| {
                file_config
                    .logging_level
                    .unwrap_or(DEFAULT_LOGGING_LEVEL.to_string())
            }),
        };

        Ok(config)
    }
}
