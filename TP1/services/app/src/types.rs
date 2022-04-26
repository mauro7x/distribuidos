use distribuidos_tp1_protocols::types::Event;
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Row {
    metric_id: String,
    value: f32,
}

impl From<Row> for Event {
    fn from(row: Row) -> Event {
        Event {
            metric_id: row.metric_id,
            value: row.value,
        }
    }
}
