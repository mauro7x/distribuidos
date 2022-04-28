use distribuidos_tp1_protocols::types::{AggregationOpcode, Query};
use serde::{Deserialize, Serialize};

#[derive(Deserialize, Serialize, Debug)]
pub struct Check {
    pub metric_id: String,
    pub aggregation: AggregationOpcode,
    pub aggregation_window_secs: f32,
    pub limit: f32,
    pub last_to_timestamp: Option<i64>,
}

#[derive(Debug)]
pub struct CheckRequest {
    pub limit: f32,
    pub query: Query,
}
