mod constants;
mod messages;

use crate::{manual::messages::*, parse::parse_row, types::Row};
use distribuidos_tp1_gateway::Gateway;
use distribuidos_tp1_protocols::types::{errors::SendError, Query};
use distribuidos_types::BoxResult;
use std::io;

use log::*;

fn send_query(gateway: &Gateway, query: Query) -> BoxResult<()> {
    match gateway.send_query(query) {
        Ok(query_result) => info!("Result: {:?}", query_result),
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

    print_expected();
    prompt();
    for input in rdr.deserialize::<Row>() {
        match input {
            Ok(row) => {
                match parse_row(row) {
                    Ok(query) => send_query(&gateway, query)?,
                    Err(_) => invalid_input(),
                };
            }
            Err(_) => invalid_input(),
        };
        prompt();
    }

    Ok(())
}
