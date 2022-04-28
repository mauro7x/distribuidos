// Paths
pub const CONFIG_FILE_PATH: &str = "./config/workers.json";

// Env vars
pub const THREAD_POOL_SIZE_ENV: &str = "HANDLER_THREAD_POOL_SIZE";
pub const QUEUE_SIZE_ENV: &str = "HANDLER_QUEUE_SIZE";
pub const OUTPUT_DIRPATH_ENV: &str = "OUTPUT_DIRPATH";

// Defaults
pub const DEFAULT_THREAD_POOL_SIZE: usize = 3;
pub const DEFAULT_QUEUE_SIZE: usize = 10;
pub const DEFAULT_OUTPUT_DIRPATH: &str = "./alerts";
