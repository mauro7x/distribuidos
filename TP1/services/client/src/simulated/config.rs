use super::constants::*;
use distribuidos_types::BoxResult;
use std::env::var;

use log::*;
use serde::Deserialize;

#[derive(Debug, Deserialize, Default)]
struct FileConfig {
    thread_pool_size: Option<usize>,
    repeat_every_ms: Option<u64>,
    between_requests_ms: Option<u64>,
}

#[derive(Debug, Deserialize)]
pub struct Config {
    pub thread_pool_size: usize,
    pub repeat_every_ms: u64,
    pub between_requests_ms: u64,
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
            thread_pool_size: var(THREAD_POOL_SIZE_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .thread_pool_size
                        .unwrap_or(DEFAULT_THREAD_POOL_SIZE)
                        .to_string()
                })
                .parse()?,
            repeat_every_ms: var(REPEAT_EVERY_MS_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .repeat_every_ms
                        .unwrap_or(DEFAULT_REPEAT_EVERY_MS)
                        .to_string()
                })
                .parse()?,
            between_requests_ms: var(BETWEEN_REQUESTS_MS_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .between_requests_ms
                        .unwrap_or(DEFAULT_BETWEEN_REQUESTS_MS)
                        .to_string()
                })
                .parse()?,
        };

        Ok(config)
    }
}
