use aggregator::{
    forker::{self, Forker},
    server,
};

use distribuidos_types::BoxResult;
use std::process::exit;

use log::*;
extern crate pretty_env_logger;

fn run() -> BoxResult<()> {
    let mut forker: Forker = forker::new()?;
    let mut server = server::new(&forker)?;
    server.run()?;
    forker.stop();
    forker.join();

    Ok(())
}

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("{}", err);
        exit(1);
    }
}
