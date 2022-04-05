// PATHS
pub const CONFIG_FILE_PATH: &str = "config/default.json";

// ENV VARS
pub const HOST_ENV: &str = "SERVER_IP";
pub const PORT_ENV: &str = "SERVER_PORT";
pub const LISTEN_BACKLOG_ENV: &str = "SERVER_LISTEN_BACKLOG";
pub const LOGGING_LEVEL_ENV: &str = "LOGGING_LEVEL";

// DEFAULTS
pub const DEFAULT_HOST: &str = "localhost";
pub const DEFAULT_PORT: u16 = 3000;
pub const DEFAULT_LISTEN_BACKLOG: u16 = 5;
pub const DEFAULT_LOGGING_LEVEL: &str = "INFO";
