use std::io::Error;

use distribuidos_tp1_protocols::types::errors::{QueryError, SendError};

#[derive(Debug)]
pub enum SendQueryError {
    Send(SendError),
    Query(QueryError),
    IO(Error),
}

impl From<SendError> for SendQueryError {
    fn from(error: SendError) -> SendQueryError {
        SendQueryError::Send(error)
    }
}

impl From<QueryError> for SendQueryError {
    fn from(error: QueryError) -> SendQueryError {
        SendQueryError::Query(error)
    }
}

impl From<Error> for SendQueryError {
    fn from(error: Error) -> SendQueryError {
        SendQueryError::IO(error)
    }
}
