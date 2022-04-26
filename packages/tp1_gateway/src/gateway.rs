use crate::config::Config;
use distribuidos_tp1_protocols::{
    requests, responses,
    types::{errors::SendError, Event, Query, QueryResult},
};
use distribuidos_types::BoxResult;
use std::net::TcpStream;

use log::*;

#[derive(Debug)]
pub struct Gateway {
    addr: String,
}

impl Gateway {
    pub fn new() -> BoxResult<Gateway> {
        trace!("Creating Gateway...");
        let Config {
            server_host,
            server_port,
        } = Config::new()?;
        let gateway = Gateway {
            addr: format!("{}:{}", server_host, server_port),
        };
        debug!("Gateway created: {:#?}", gateway);

        Ok(gateway)
    }

    pub fn send_event(&self, event: Event) -> Result<(), SendError> {
        let stream = TcpStream::connect(&self.addr)?;
        debug!("Sending event...");
        requests::send_event(&stream, event)?;
        debug!("Event sent, waiting ACK...");
        responses::recv_event_ack(&stream)?;
        debug!("ACK received, event sent successfully");

        Ok(())
    }

    pub fn send_query(&self, query: Query) -> Result<QueryResult, SendError> {
        let stream = TcpStream::connect(&self.addr)?;
        debug!("Sending query...");
        requests::send_query(&stream, query)?;
        debug!("Query sent, waiting ACK...");
        responses::recv_query_ack(&stream)?;
        debug!("ACK received, waiting query response...");
        let result = responses::recv_query_result(&stream)?;
        debug!("Query response received successfully");

        Ok(result)
    }
}
