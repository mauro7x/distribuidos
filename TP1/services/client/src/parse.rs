use distribuidos_tp1_protocols::types::{AggregationOpcode, DateTimeRange, Query};
use distribuidos_types::BoxResult;

use crate::types::Row;

fn parse_aggr(aggr_op: u8) -> BoxResult<AggregationOpcode> {
    match aggr_op {
        0 => Ok(AggregationOpcode::AVG),
        1 => Ok(AggregationOpcode::MIN),
        2 => Ok(AggregationOpcode::MAX),
        3 => Ok(AggregationOpcode::COUNT),
        _ => Err("Invalid".into()),
    }
}

pub fn parse_row(row: Row) -> BoxResult<Query> {
    todo!();

    // let range = if let Some(from) = row.some && let Some(to) = row.to {
    //     DateTimeRange {}
    // }

    // let query = Query {
    //     metric_id: row.metric_id,
    //     range,
    //     aggregation: parse_aggr(row.aggregation)?,
    //     aggregation_window_secs: row.aggr_window_secs,
    // };

    // Ok(query)
}
