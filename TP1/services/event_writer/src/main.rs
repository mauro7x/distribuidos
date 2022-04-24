use distribuidos_types::BoxResult;
use std::process::exit;

use event_writer::{server, WriteWorkerPool};
use log::*;
extern crate pretty_env_logger;

fn run() -> BoxResult<()> {
    let mut write_worker_pool = WriteWorkerPool::new()?;
    let mut server = server::new(&write_worker_pool)?;
    server.run()?;
    write_worker_pool.join();

    Ok(())
}

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("Failed - {}", err);
        exit(1);
    }
}
