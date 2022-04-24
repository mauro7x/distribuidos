// Paths
pub const CONFIG_FILE_PATH: &str = "config/workers.json";

// Env vars
pub const FLUSH_TIMEOUT_MS_ENV: &str = "FLUSH_TIMEOUT_MS";
pub const WORKER_POOL_SIZE_ENV: &str = "WORKER_POOL_SIZE";
pub const WORKER_QUEUE_SIZE_ENV: &str = "WORKER_QUEUE_SIZE";

// Defaults
pub const DEFAULT_FLUSH_TIMEOUT_MS: u64 = 100;
pub const DEFAULT_WORKER_POOL_SIZE: usize = 3;
pub const DEFAULT_WORKER_QUEUE_SIZE: usize = 10;
