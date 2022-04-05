use app::{config::Config, server::Server};
use log::{error, trace};
use std::{error::Error, process, sync::mpsc::channel};

extern crate pretty_env_logger;

fn run() -> Result<(), Box<dyn Error>> {
    trace!("Starting execution");
    let config = Config::new()?;
    let (tx, rx) = channel();
    ctrlc::set_handler(move || tx.send(()).expect("Could not send signal on channel."))?;
    let server = Server::new(config, rx)?;
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
