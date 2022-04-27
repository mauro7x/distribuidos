use std::io::Error;

#[derive(Debug)]
pub enum RecvError {
    Terminated,
    Invalid,
    IOError(Error),
}

impl From<SendError> for RecvError {
    fn from(e: SendError) -> RecvError {
        match e {
            SendError::IOError(e) => RecvError::IOError(e),
            _ => unreachable!(),
        }
    }
}

impl From<Error> for RecvError {
    fn from(e: Error) -> RecvError {
        RecvError::IOError(e)
    }
}

#[derive(Debug)]
pub enum SendError {
    Invalid,
    ServerAtCapacity,
    InternalServerError,
    IOError(Error),
}

impl From<RecvError> for SendError {
    fn from(e: RecvError) -> SendError {
        match e {
            RecvError::IOError(e) => SendError::IOError(e),
            _ => unreachable!(),
        }
    }
}

impl From<Error> for SendError {
    fn from(e: Error) -> SendError {
        SendError::IOError(e)
    }
}

#[derive(Debug)]
pub enum QueryError {
    Invalid,
    ServerAtCapacity,
    InternalServerError,
    MetricNotFound,
    InvalidRange,
    InvalidAggrWindow,
    IOError(Error),
}

impl From<SendError> for QueryError {
    fn from(error: SendError) -> QueryError {
        match error {
            SendError::Invalid => QueryError::Invalid,
            SendError::ServerAtCapacity => QueryError::ServerAtCapacity,
            SendError::InternalServerError => QueryError::InternalServerError,
            SendError::IOError(e) => QueryError::IOError(e),
        }
    }
}

impl From<Error> for QueryError {
    fn from(error: Error) -> QueryError {
        QueryError::IOError(error)
    }
}
