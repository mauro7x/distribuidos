use crate::constants::{
    CONFIG_FILE_PATH, DEFAULT_HOST, DEFAULT_LISTEN_BACKLOG, DEFAULT_PORT, HOST_ENV,
    LISTEN_BACKLOG_ENV, PORT_ENV,
};
use log::{debug, trace};
use serde::Deserialize;
use std::{env::var, error::Error};

#[derive(Debug, Deserialize)]
struct FileConfig {
    server_ip: Option<String>,
    server_port: Option<u16>,
    server_listen_backlog: Option<u16>,
}

#[derive(Debug, Deserialize)]
pub struct Config {
    pub host: String,
    pub port: u16,
    pub listen_backlog: u16,
}

impl Config {
    pub fn new() -> Result<Config, Box<dyn Error>> {
        trace!("Reading config file...");
        let data = std::fs::read_to_string(CONFIG_FILE_PATH)?;
        let file_config: FileConfig = serde_json::from_str(&data)?;
        trace!("Read config file: {:#?}", data);
        trace!("Overriding config with environment vars...");
        let config = Config::override_with_envvars(file_config)?;

        debug!("Created successfully: {:#?}", config);
        Ok(config)
    }

    fn override_with_envvars(file_config: FileConfig) -> Result<Config, Box<dyn Error>> {
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
        };

        Ok(config)
    }
}
