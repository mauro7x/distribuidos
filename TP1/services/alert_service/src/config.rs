use super::constants::*;
use distribuidos_types::BoxResult;
use std::env::var;

use log::*;
use serde::Deserialize;

#[derive(Debug, Deserialize, Default)]
struct FileConfig {
    frequency_secs: Option<u32>,
}

#[derive(Debug, Deserialize)]
pub struct Config {
    pub frequency_secs: u32,
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
            frequency_secs: var(FREQUENCY_SECS_ENV)
                .unwrap_or_else(|_| {
                    file_config
                        .frequency_secs
                        .unwrap_or(DEFAULT_FREQUENCY_SECS)
                        .to_string()
                })
                .parse()?,
        };

        Ok(config)
    }
}
