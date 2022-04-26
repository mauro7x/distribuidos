use std::net::TcpStream;

use distribuidos_tp1_protocols::types::Query;

#[derive(Debug)]
pub struct QueryRequest {
    pub stream: TcpStream,
    pub query: Query,
}
