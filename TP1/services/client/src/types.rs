use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Row {
    pub metric_id: String,
    pub from: Option<String>,
    pub to: Option<String>,
    pub aggr_window_secs: Option<f32>,
    pub aggregation: String,
}

pub enum InputError {
    InvalidCSV,
    OnlyOneRange,
    InvalidDateTime,
    InvalidAggr,
}
