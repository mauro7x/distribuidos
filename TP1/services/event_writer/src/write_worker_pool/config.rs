use super::constants::*;
use distribuidos_types::BoxResult;
use std::env::var;

use log::*;
use serde::Deserialize;

#[derive(Debug, Deserialize, Default)]
struct FileConfig {
    flush_timeout_ms: Option<u64>,
    worker_pool_size: Option<usize>,
    worker_queue_size: Option<usize>,
    partition_secs: Option<i64>,
    database_path: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct Config {
    pub flush_timeout_ms: u64,
    pub worker_pool_size: usize,
    pub worker_queue_size: usize,
    pub partition_secs: i64,
    pub database_path: String,
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
            flush_timeout_ms: var(FLUSH_TIMEOUT_MS_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .flush_timeout_ms
                        .unwrap_or(DEFAULT_FLUSH_TIMEOUT_MS)
                        .to_string()
                })
                .parse()?,
            worker_pool_size: var(WORKER_POOL_SIZE_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .worker_pool_size
                        .unwrap_or(DEFAULT_WORKER_POOL_SIZE)
                        .to_string()
                })
                .parse()?,
            worker_queue_size: var(WORKER_QUEUE_SIZE_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .worker_queue_size
                        .unwrap_or(DEFAULT_WORKER_QUEUE_SIZE)
                        .to_string()
                })
                .parse()?,
            partition_secs: var(PARTITION_SECS_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .partition_secs
                        .unwrap_or(DEFAULT_PARTITION_SECS)
                        .to_string()
                })
                .parse()?,
            database_path: var(DATABASE_PATH_ENV).unwrap_or_else(|_| {
                file_config
                    .database_path
                    .unwrap_or_else(|| DEFAULT_DATABASE_PATH.to_string())
            }),
        };

        Ok(config)
    }
}
