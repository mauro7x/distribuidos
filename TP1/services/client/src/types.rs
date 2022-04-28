use distribuidos_tp1_protocols::types::AggregationOpcode;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Row {
    pub metric_id: String,
    pub from: Option<String>,
    pub to: Option<String>,
    pub aggr_window_secs: Option<f32>,
    pub aggregation: AggregationOpcode,
}
// metric_1,0,0,30,10,avg
#[derive(Debug, Deserialize)]
pub struct SimulatedRow {
    pub metric_id: String,
    pub hh: u32,
    pub mm: u32,
    pub ss: u32,
    pub aggr_window_secs: Option<f32>,
    pub aggregation: AggregationOpcode,
}

pub enum InputError {
    InvalidCSV,
    OnlyOneRange,
    InvalidDateTime,
}
