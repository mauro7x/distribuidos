use std::io::Error;

#[derive(Debug)]
pub enum QueryError {
    MetricNotFound,
    InvalidRange,
    InvalidAggrWindow,
    IOError(Error),
}

impl From<Error> for QueryError {
    fn from(e: Error) -> QueryError {
        QueryError::IOError(e)
    }
}

pub struct ConcreteQuery {
    pub metric_id: String,
    pub from: i64,
    pub to: i64,
}
