use crate::config::Config;
use log::{debug, trace};

#[derive(Debug)]
pub struct Server {}

impl Server {
    pub fn new(config: Config) -> Self {
        trace!("Creating server with config: {:#?}", config);
        let server = Server {};

        debug!("Created successfully: {:#?}", server);
        server
    }
}
