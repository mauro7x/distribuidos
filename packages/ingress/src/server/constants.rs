// Paths
pub const CONFIG_FILE_PATH: &str = "./config/ingress.json";

// Env vars
pub const HOST_ENV: &str = "INGRESS_HOST";
pub const PORT_ENV: &str = "INGRESS_PORT";
pub const THREAD_POOL_SIZE_ENV: &str = "ACCEPTOR_THREAD_POOL_SIZE";
pub const QUEUE_SIZE_ENV: &str = "ACCEPTOR_QUEUE_SIZE";
pub const READ_TIMEOUT_MS_ENV: &str = "READ_TIMEOUT_MS";

// Defaults
pub const DEFAULT_HOST: &str = "0.0.0.0";
pub const DEFAULT_PORT: u16 = 3000;
pub const DEFAULT_THREAD_POOL_SIZE: usize = 3;
pub const DEFAULT_QUEUE_SIZE: usize = 10;
pub const DEFAULT_READ_TIMEOUT_MS: u64 = 1000;
