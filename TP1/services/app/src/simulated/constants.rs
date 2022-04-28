// Paths
pub const CONFIG_FILE_PATH: &str = "./config/simulated.json";
pub const EVENTS_FILE_PATH: &str = "./config/events.csv";

// Env vars
pub const THREAD_POOL_SIZE_ENV: &str = "THREAD_POOL_SIZE";
pub const REPEAT_EVERY_MS_ENV: &str = "REPEAT_EVERY_MS";
pub const BETWEEN_REQUESTS_MS_ENV: &str = "BETWEEN_REQUESTS_MS";

// Defaults
pub const DEFAULT_THREAD_POOL_SIZE: usize = 3;
pub const DEFAULT_REPEAT_EVERY_MS: u64 = 0;
pub const DEFAULT_BETWEEN_REQUESTS_MS: u64 = 100;
