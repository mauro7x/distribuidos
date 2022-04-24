use distribuidos_types::BoxResult;
use std::process::exit;

use event_receiver::{server, EventDispatcher};
use log::*;
extern crate pretty_env_logger;

fn run() -> BoxResult<()> {
    let mut event_dispatcher = EventDispatcher::new()?;
    let dispatcher = event_dispatcher.clone_dispatcher();
    let mut server = server::new(dispatcher)?;
    server.run()?;
    event_dispatcher.join();

    Ok(())
}

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("Failed - {}", err);
        exit(1);
    }
}
