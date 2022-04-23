use super::constants::{CONFIG_FILE_PATH, DEFAULT_HOST, DEFAULT_PORT, HOST_ENV, PORT_ENV};
use serde::Deserialize;
use std::{env::var, error::Error};

/// Config to be parsed from config file.
/// All parameters are optional since they may not be present in the file.
///
/// ## Arguments
///
/// * `server_ip` (self-descriptive).
/// * `server_port`: (self-descriptive).
/// * `server_listen_backlog`: size of the backlog listening queue.
#[derive(Debug, Deserialize)]
struct FileConfig {
    host: Option<String>,
    port: Option<u16>,
}

/// ## Arguments
///
/// * `host` (self-descriptive).
/// * `port`: (self-descriptive).
/// * `listen_backlog`: size of the backlog listening queue.
/// * `accept_sleep_time_ms`: time to sleep when there are no connections to accept.
#[derive(Debug, Deserialize)]
pub struct Config {
    pub host: String,
    pub port: u16,
}

impl Config {
    /// Reads configuration file and then overrides values present in
    /// environment variables.
    pub fn new() -> Result<Config, Box<dyn Error>> {
        let data = std::fs::read_to_string(CONFIG_FILE_PATH)?;
        let file_config: FileConfig = serde_json::from_str(&data)?;

        let config = Config::override_with_envvars(file_config)?;

        Ok(config)
    }

    /// Overrides config read from file with values present
    /// in environment values, or default values if they are not
    /// present in either place.
    fn override_with_envvars(file_config: FileConfig) -> Result<Config, Box<dyn Error>> {
        let config = Config {
            host: var(HOST_ENV)
                .unwrap_or_else(|_| file_config.host.unwrap_or_else(|| DEFAULT_HOST.to_string())),
            port: var(PORT_ENV)
                .unwrap_or_else(|_| file_config.port.unwrap_or(DEFAULT_PORT).to_string())
                .parse()?,
        };

        Ok(config)
    }
}
