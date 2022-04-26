use super::constants::*;
use distribuidos_types::BoxResult;
use std::env::var;

use log::*;
use serde::Deserialize;

#[derive(Debug, Deserialize, Default)]
struct FileConfig {
    server_host: Option<String>,
    server_port: Option<u16>,
}

#[derive(Debug, Deserialize)]
pub struct Config {
    pub server_host: String,
    pub server_port: u16,
}

impl Config {
    /// Reads configuration file and then overrides values present in
    /// environment variables.
    pub fn new() -> BoxResult<Config> {
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

    fn read_config_file() -> BoxResult<FileConfig> {
        let data = std::fs::read_to_string(CONFIG_FILE_PATH)?;
        let file_config: FileConfig = serde_json::from_str(&data)?;

        Ok(file_config)
    }

    /// Overrides config read from file with values present
    /// in environment values, or default values if they are not
    /// present in either place.
    fn override_with_envvars(file_config: FileConfig) -> BoxResult<Config> {
        let config = Config {
            server_host: var(SERVER_HOST_ENV).unwrap_or_else(|_| {
                file_config
                    .server_host
                    .unwrap_or_else(|| DEFAULT_SERVER_HOST.to_string())
            }),
            server_port: var(SERVER_PORT_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .server_port
                        .unwrap_or(DEFAULT_SERVER_PORT)
                        .to_string()
                })
                .parse()?,
        };

        Ok(config)
    }
}
