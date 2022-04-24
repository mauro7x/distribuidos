use db_event_writer::server;
use distribuidos_types::BoxResult;
use std::process::exit;

use log::*;
extern crate pretty_env_logger;

fn run() -> BoxResult<()> {
    let mut server = server::new()?;
    server.run()?;

    Ok(())
}

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("{}", err);
        exit(1);
    }
}
