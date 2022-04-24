// Paths
pub const CONFIG_FILE_PATH: &str = "config/dispatcher.json";

// Env vars
pub const DB_HOST_ENV: &str = "DB_HOST";
pub const DB_PORT_ENV: &str = "DB_PORT";
pub const THREAD_POOL_SIZE_ENV: &str = "DISPATCHER_THREAD_POOL_SIZE";
pub const QUEUE_SIZE_ENV: &str = "DISPATCHER_QUEUE_SIZE";

// Defaults
pub const DB_HOST_DEFAULT: &str = "db_event_writer";
pub const DB_PORT_DEFAULT: u16 = 3000;
pub const DEFAULT_THREAD_POOL_SIZE: usize = 3;
pub const DEFAULT_QUEUE_SIZE: usize = 10;
