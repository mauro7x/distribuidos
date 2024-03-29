// Paths
pub const CONFIG_FILE_PATH: &str = "./config/workers.json";

// Env vars
pub const THREAD_POOL_SIZE_ENV: &str = "HANDLER_THREAD_POOL_SIZE";
pub const QUEUE_SIZE_ENV: &str = "HANDLER_QUEUE_SIZE";
pub const PARTITION_SECS_ENV: &str = "PARTITION_SECS";
pub const DATABASE_PATH_ENV: &str = "DATABASE_PATH";

// Defaults
pub const DEFAULT_THREAD_POOL_SIZE: usize = 3;
pub const DEFAULT_QUEUE_SIZE: usize = 10;
pub const DEFAULT_PARTITION_SECS: i64 = 600; // 10 min
pub const DEFAULT_DATABASE_PATH: &str = "./events";
