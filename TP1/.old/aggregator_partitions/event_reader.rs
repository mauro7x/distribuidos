use std::{fs, io::Error, path::Path};

use super::{types::QueryError, window_aggregator::WindowAggregator};
use chrono::{Date, Utc};
use distribuidos_tp1_protocols::types::{DateTime, DateTimeRange, Query, QueryResult};
use distribuidos_tp1_utils::file_utils;

#[derive(Clone)]
pub struct EventReader {
    database_path: String,
    partition_secs: u32,
}

impl EventReader {
    pub fn new(database_path: String, partition_secs: u32) -> EventReader {
        EventReader {
            database_path,
            partition_secs,
        }
    }

    pub fn resolve(&self, query: Query) -> Result<QueryResult, QueryError> {
        let Query {
            metric_id,
            range,
            aggregation,
            aggregation_window_secs,
        } = query;
        EventReader::validate_range(&range)?;
        let aggregation_window_secs = EventReader::parse_aggr_window_secs(aggregation_window_secs)?;
        self.check_if_metric_exists(&metric_id)?;

        let (range, padding_secs) = match range {
            Some(range) => {
                let (from, padding_secs) = self.get_first_datetime_from(&metric_id, range.from);
                let range = DateTimeRange { from, to: range.to };
                (range, padding_secs)
            }
            None => {
                let range = DateTimeRange {
                    from: self.get_first_datetime(&metric_id),
                    to: Utc::now(),
                };
                (range, 0)
            }
        };

        let window = WindowAggregator::new(aggregation, range.to, aggregation_window_secs);
        let result = self._resolve(metric_id, range, window)?;

        Ok(result)
    }

    fn _resolve(
        &self,
        metric_id: String,
        range: DateTimeRange,
        window: WindowAggregator,
    ) -> Result<QueryResult, Error> {
        Ok(window.result)
    }

    fn get_first_datetime(&self, _metric_id: &String) -> DateTime {
        todo!()
    }

    fn get_first_datetime_from(&self, metric_id: &String, from: DateTime) -> (DateTime, i64) {
        // First, we fetch all dirs in metric directory (we know it exists because)
        // it has been validated in creation time

        match self.get_first_directory(metric_id, &from.date()) {
            Some(first_directory) => {}
            None => {}
        };

        (from, 0)
    }

    fn get_first_directory(&self, metric_id: &String, from: &Date<Utc>) -> Option<String> {
        let from_dirname = file_utils::date_dirname(&from);
        let metric_dirpath = format!("{}/{}", self.database_path, metric_id);
        let dirs =
            file_utils::directories(Path::new(&metric_dirpath)).expect("Failed to ls in database");

        let mut first_directory: Option<String> = None;
        for dir in dirs {
            let dirname_str = dir.file_name().unwrap().to_str().unwrap();
            let dirname = String::from(dirname_str);

            first_directory = match first_directory {
                Some(current) if (dirname < current && from_dirname <= dirname) => Some(dirname),
                Some(current) => Some(current),
                None => match from_dirname <= dirname {
                    true => Some(dirname),
                    false => None,
                },
            };
        }

        first_directory
    }

    fn check_if_metric_exists(&self, metric_id: &String) -> Result<(), QueryError> {
        let metric_dirpath = format!("{}/{}", self.database_path, metric_id);
        match Path::new(&metric_dirpath).exists() {
            true => Ok(()),
            false => Err(QueryError::MetricNotFound),
        }
    }

    // Static

    fn validate_range(range: &Option<DateTimeRange>) -> Result<(), QueryError> {
        if let Some(range) = range {
            if range.from >= range.to || range.to > Utc::now() {
                return Err(QueryError::InvalidRange);
            };
        }

        Ok(())
    }

    fn parse_aggr_window_secs(
        aggregation_window_secs: Option<f32>,
    ) -> Result<Option<i64>, QueryError> {
        if let Some(aggr_window_secs) = aggregation_window_secs {
            return match aggr_window_secs >= 0.0 {
                true => Ok(Some(aggr_window_secs as i64)),
                false => Err(QueryError::InvalidAggrWindow),
            };
        };

        Ok(None)
    }
}
