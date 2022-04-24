use super::constants::*;
use distribuidos_types::BoxResult;
use std::env::var;

use log::*;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
struct FileConfig {
    thread_pool_size: Option<usize>,
    queue_size: Option<usize>,
}

#[derive(Debug, Deserialize)]
pub struct Config {
    pub thread_pool_size: usize,
    pub queue_size: usize,
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
                FileConfig {
                    thread_pool_size: None,
                    queue_size: None,
                }
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
