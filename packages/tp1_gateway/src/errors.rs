use std::io::Error;

use distribuidos_tp1_protocols::types::errors::{QueryError, SendError};

#[derive(Debug)]
pub enum SendQueryError {
    Invalid,
    ServerAtCapacity,
    MetricNotFound,
    InvalidRange,
    InvalidAggrWindow,
    InternalServerError,
    IOError(Error),
}

impl From<SendError> for SendQueryError {
    fn from(error: SendError) -> SendQueryError {
        match error {
            SendError::Invalid => SendQueryError::Invalid,
            SendError::ServerAtCapacity => SendQueryError::ServerAtCapacity,
            SendError::InternalServerError => SendQueryError::InternalServerError,
            SendError::IOError(e) => SendQueryError::IOError(e),
        }
    }
}

impl From<QueryError> for SendQueryError {
    fn from(error: QueryError) -> SendQueryError {
        match error {
            QueryError::MetricNotFound => SendQueryError::MetricNotFound,
            QueryError::InvalidRange => SendQueryError::InvalidRange,
            QueryError::InvalidAggrWindow => SendQueryError::InvalidAggrWindow,
            QueryError::InternalServerError => SendQueryError::InternalServerError,
            QueryError::IOError(e) => SendQueryError::IOError(e),
        }
    }
}

impl From<Error> for SendQueryError {
    fn from(error: Error) -> SendQueryError {
        SendQueryError::IOError(error)
    }
}
