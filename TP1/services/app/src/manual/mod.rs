mod constants;

use crate::{manual::constants::*, types::Row};
use distribuidos_tp1_gateway::Gateway;
use distribuidos_tp1_protocols::types::{errors::SendError, Event};
use distribuidos_types::BoxResult;
use std::io::{self, Write};

use log::*;
extern crate pretty_env_logger;

fn prompt() {
    print!("\nIngress event: ");
    std::io::stdout().flush().unwrap();
}

fn send_event_from_row(gateway: &Gateway, row: Row) -> BoxResult<()> {
    let event = Event::from(row);
    match gateway.send_event(event) {
        Ok(()) => info!("Event sent successfully"),
        Err(SendError::Invalid) => warn!("Server responded: Invalid Format (404)"),
        Err(SendError::ServerAtCapacity) => error!("Server responded: Server At Capacity (503)"),
        Err(SendError::InternalServerError) => {
            error!("Server responded: Internal Server Error (500)")
        }
        Err(SendError::IOError(err)) => return Err(err.into()),
    };

    Ok(())
}

pub fn run() -> BoxResult<()> {
    let mut rdr = csv::ReaderBuilder::new()
        .has_headers(false)
        .from_reader(io::stdin());
    let gateway = Gateway::new()?;

    println!("Event format: {}", EXPECTED_FORMAT);
    prompt();
    for input in rdr.deserialize::<Row>() {
        match input {
            Ok(row) => send_event_from_row(&gateway, row)?,
            Err(_) => error!(
                "Client: invalid input. Expected format: {}",
                EXPECTED_FORMAT
            ),
        };
        prompt();
    }

    Ok(())
}
