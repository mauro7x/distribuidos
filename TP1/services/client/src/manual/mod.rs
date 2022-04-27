mod messages;

use crate::{
    manual::messages::*,
    parse::parse_row,
    types::{InputError, Row},
};
use distribuidos_tp1_gateway::{Gateway, SendQueryError};
use distribuidos_tp1_protocols::types::Query;
use distribuidos_types::BoxResult;
use std::io;

use log::*;

fn handle_errors(error: SendQueryError) -> BoxResult<()> {
    match error {
        // 4XX
        SendQueryError::Invalid => warn!("Response: Invalid format (400)"),
        SendQueryError::InvalidRange => warn!("Response: Invalid range (400)"),
        SendQueryError::InvalidAggrWindow => warn!("Response: Invalid aggregation window (400)"),
        SendQueryError::MetricNotFound => warn!("Response: Metric not found (404)"),
        // 5XX
        SendQueryError::ServerAtCapacity => error!("Response: Server at capacity (503)"),
        SendQueryError::InternalServerError => {
            error!("Response: Internal server error (500)")
        }
        // Self errors
        SendQueryError::IOError(err) => return Err(err.into()),
    };

    Ok(())
}

fn send_query(gateway: &Gateway, query: Query) -> BoxResult<()> {
    match gateway.send_query(query) {
        Ok(query_result) => info!("Result: {:?}", query_result),
        Err(e) => handle_errors(e)?,
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
                    Err(e) => invalid_input(e),
                };
            }
            Err(_) => invalid_input(InputError::InvalidCSV),
        };
        prompt();
    }

    Ok(())
}
