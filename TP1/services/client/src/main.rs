use distribuidos_tp1_protocols::{events::send, types::Event};
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
    id: String,
    value: f32,
}

impl From<Row> for Event {
    fn from(row: Row) -> Event {
        Event {
            id: row.id,
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

    match send(&stream, event)? {
        Ok(_) => info!("Event sent successfully"),
        Err(err) => error!("Error received from server: {:?}", err),
    };

    Ok(())
}

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("{}", err);
        exit(1);
    }
}
