use crate::{
    constants::*,
    types::{InputError, Row},
};
use chrono::{LocalResult, NaiveDateTime, TimeZone, Utc};
use distribuidos_tp1_protocols::types::{AggregationOpcode, DateTime, DateTimeRange, Query};

fn parse_aggr(aggregation: String) -> Result<AggregationOpcode, InputError> {
    match aggregation.to_lowercase().as_str() {
        "avg" => Ok(AggregationOpcode::AVG),
        "min" => Ok(AggregationOpcode::MIN),
        "max" => Ok(AggregationOpcode::MAX),
        "count" => Ok(AggregationOpcode::COUNT),
        _ => Err(InputError::InvalidAggr),
    }
}

fn parse_datetime(date: &str) -> Result<DateTime, InputError> {
    let naive = NaiveDateTime::parse_from_str(date, DATETIME_FORMAT)
        .map_err(|_| InputError::InvalidDateTime)?;

    match Utc.from_local_datetime(&naive) {
        LocalResult::Single(datetime) => Ok(datetime),
        LocalResult::None | LocalResult::Ambiguous(_, _) => Err(InputError::InvalidDateTime),
    }
}

fn parse_range(
    from: Option<String>,
    to: Option<String>,
) -> Result<Option<DateTimeRange>, InputError> {
    match (from, to) {
        (Some(from), Some(to)) => Ok(Some(DateTimeRange {
            from: parse_datetime(&from)?,
            to: parse_datetime(&to)?,
        })),
        (None, None) => Ok(None),
        _ => Err(InputError::OnlyOneRange),
    }
}

pub fn parse_row(row: Row) -> Result<Query, InputError> {
    let query = Query {
        metric_id: row.metric_id,
        range: parse_range(row.from, row.to)?,
        aggregation: parse_aggr(row.aggregation)?,
        aggregation_window_secs: row.aggr_window_secs,
    };

    Ok(query)
}
