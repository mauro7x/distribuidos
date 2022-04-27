use alert_service::dispatcher::Dispatcher;
use distribuidos_types::BoxResult;
use std::process::exit;
use std::sync::mpsc;

use ctrlc;
use log::*;
extern crate pretty_env_logger;

fn run() -> BoxResult<()> {
    let (tx, rx) = mpsc::channel();
    ctrlc::set_handler(move || tx.send(()).expect("Could not send signal on channel."))
        .expect("Error setting Ctrl-C handler");

    let dispatcher = Dispatcher::new(rx)?;
    dispatcher.run()?;

    Ok(())
}

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("Failed - {}", err);
        exit(1);
    }
}
