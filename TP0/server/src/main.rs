use app::{config::Config, server::Server};
use std::{error::Error, process};

extern crate pretty_env_logger;
use log::{error, trace};

fn run() -> Result<(), Box<dyn Error>> {
    trace!("Starting execution");
    let config = Config::new()?;
    let _server = Server::new(config);

    trace!("Finishing execution gracefully");
    Ok(())
}

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("{}", err);
        process::exit(1);
    }
}
