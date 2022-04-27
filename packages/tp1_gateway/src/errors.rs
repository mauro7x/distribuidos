use std::io::Error;

use distribuidos_tp1_protocols::types::errors::{QueryError, SendError};

#[derive(Debug)]
pub enum SendQueryError {
    SendError(SendError),
    QueryError(QueryError),
    IOError(Error),
}

impl From<SendError> for SendQueryError {
    fn from(error: SendError) -> SendQueryError {
        SendQueryError::SendError(error)
    }
}

impl From<QueryError> for SendQueryError {
    fn from(error: QueryError) -> SendQueryError {
        SendQueryError::QueryError(error)
    }
}

impl From<Error> for SendQueryError {
    fn from(error: Error) -> SendQueryError {
        SendQueryError::IOError(error)
    }
}
