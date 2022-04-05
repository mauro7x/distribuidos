use app::{config::Config, server::Server};
use log::{error, trace};
use std::{error::Error, process};

extern crate pretty_env_logger;

fn run() -> Result<(), Box<dyn Error>> {
    trace!("Starting execution");
    let config = Config::new()?;
    let mut server = Server::new(config)?;
    server.run()?;

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
