use distribuidos_tp1_protocols::{
    requests, responses,
    types::{errors::SendError, Event},
};
use distribuidos_types::BoxResult;
use std::{
    io::{self, Write},
    net::TcpStream,
    process::exit,
};

use log::*;
use serde::Deserialize;
extern crate pretty_env_logger;

const EXPECTED_FORMAT: &str = "metric,value";

#[derive(Debug, Deserialize)]
struct Row {
    metric_id: String,
    value: f32,
}

impl From<Row> for Event {
    fn from(row: Row) -> Event {
        Event {
            metric_id: row.metric_id,
            value: row.value,
        }
    }
}

fn prompt() {
    print!(
        "\nPlease ingress event to be sent (format: {}): ",
        EXPECTED_FORMAT
    );
    std::io::stdout().flush().unwrap();
}

pub fn run() -> BoxResult<()> {
    let mut rdr = csv::ReaderBuilder::new()
        .has_headers(false)
        .from_reader(io::stdin());

    prompt();
    for input in rdr.deserialize::<Row>() {
        match input {
            Ok(row) => send_event(row.into())?,
            Err(_) => error!("Invalid input"),
        };

        prompt();
    }

    Ok(())
}

fn send_event(event: Event) -> BoxResult<()> {
    let addr = "0.0.0.0:3000";
    let stream = TcpStream::connect(addr)?;

    if let Err(err) = requests::send_event(&stream, event) {
        let msg = format!("Failed to send event - {:?}", err);
        return Err(msg.into());
    };

    match responses::recv_event_ack(&stream) {
        Ok(_) => {
            info!("Event sent successfully");
            Ok(())
        }
        Err(SendError::IOError(e)) => Err(e.into()),
        Err(err) => {
            error!("Error received from server: {:?}", err);
            Ok(())
        }
    }
}

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("{}", err);
        exit(1);
    }
}
