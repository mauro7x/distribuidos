use aggregator::{server, QueryHandler};

use distribuidos_types::BoxResult;
use std::process::exit;

use log::*;
extern crate pretty_env_logger;

fn run() -> BoxResult<()> {
    let mut query_handler = QueryHandler::new()?;
    let mut server = server::new(&query_handler)?;
    server.run()?;
    query_handler.join();

    Ok(())
}

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("{}", err);
        exit(1);
    }
}
