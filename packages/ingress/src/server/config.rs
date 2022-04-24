use super::constants::{
    CONFIG_FILE_PATH, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_QUEUE_SIZE, DEFAULT_THREAD_POOL_SIZE,
    HOST_ENV, PORT_ENV, QUEUE_SIZE_ENV, THREAD_POOL_SIZE_ENV,
};
use std::{env::var, error::Error};

use log::{trace, warn};
use serde::Deserialize;

#[derive(Debug, Deserialize, Default)]
struct FileConfig {
    host: Option<String>,
    port: Option<u16>,
    thread_pool_size: Option<usize>,
    queue_size: Option<usize>,
}

#[derive(Debug, Deserialize)]
pub struct Config {
    pub host: String,
    pub port: u16,
    pub thread_pool_size: usize,
    pub queue_size: usize,
}

impl Config {
    /// Reads configuration file and then overrides values present in
    /// environment variables.
    pub fn new() -> Result<Config, Box<dyn Error>> {
        trace!("Creating Config...");
        let file_config = Config::get_file_config();
        let config = Config::override_with_envvars(file_config)?;
        trace!("Config created: {:?}", config);

        Ok(config)
    }

    fn get_file_config() -> FileConfig {
        match Config::read_config_file() {
            Ok(file) => file,
            Err(_) => {
                warn!("Config file not found, using env vars or default values.");
                FileConfig::default()
            }
        }
    }

    fn read_config_file() -> Result<FileConfig, Box<dyn Error>> {
        let data = std::fs::read_to_string(CONFIG_FILE_PATH)?;
        let file_config: FileConfig = serde_json::from_str(&data)?;

        Ok(file_config)
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
            thread_pool_size: var(THREAD_POOL_SIZE_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .thread_pool_size
                        .unwrap_or(DEFAULT_THREAD_POOL_SIZE)
                        .to_string()
                })
                .parse()?,
            queue_size: var(QUEUE_SIZE_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .queue_size
                        .unwrap_or(DEFAULT_QUEUE_SIZE)
                        .to_string()
                })
                .parse()?,
        };

        Ok(config)
    }
}
