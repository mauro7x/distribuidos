use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct PartitionRow {
    pub ms_rem: i64,
    pub value: f32,
}
