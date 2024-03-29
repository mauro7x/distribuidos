use chrono::{DateTime as DateTimeT, Utc};
use serde::{Deserialize, Serialize};

pub type DateTime = DateTimeT<Utc>;

#[derive(Serialize, Deserialize, Debug, Clone, Copy)]
#[repr(u8)]
pub enum AggregationOpcode {
    AVG = 0,
    MIN = 1,
    MAX = 2,
    COUNT = 3,
}

#[derive(Debug, Clone)]
pub struct DateTimeRange {
    pub from: DateTime,
    pub to: DateTime,
}

#[derive(Debug, Clone)]
pub struct Query {
    pub metric_id: String,
    pub range: Option<DateTimeRange>,
    pub aggregation: AggregationOpcode,
    pub aggregation_window_secs: Option<f32>,
}

pub type QueryResult = Vec<Option<f32>>;
