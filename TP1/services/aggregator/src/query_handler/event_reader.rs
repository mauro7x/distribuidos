use super::{types::ConcreteQuery, window::Window};
use chrono::Utc;
use csv::ReaderBuilder;
use distribuidos_tp1_protocols::types::{
    errors::QueryError, AggregationOpcode, DateTimeRange, Query, QueryResult,
};
use distribuidos_tp1_utils::{constants::METRIC_FIRST_PARTITION_FILE, types::PartitionRow};
use fs2::FileExt;
use std::{
    collections::HashMap,
    fs::{self, File},
    io::{Error, Read},
    mem::size_of,
    path::Path,
};

enum OpenFileResult {
    ReadOnly(File),
    RWLocked(File),
    Inexistent,
}

#[derive(Clone)]
pub struct EventReader {
    database_path: String,
    partition_secs: i64,
    first_timestamp_cache: HashMap<String, i64>,
}

impl EventReader {
    pub fn new(database_path: String, partition_secs: i64) -> EventReader {
        EventReader {
            database_path,
            partition_secs,
            first_timestamp_cache: HashMap::new(),
        }
    }

    pub fn resolve(&mut self, query: Query) -> Result<QueryResult, QueryError> {
        self.check_if_metric_exists(&query.metric_id)?;
        EventReader::validate_range(&query.range)?;
        let aggr_window_secs = EventReader::parse_aggr_window_secs(query.aggregation_window_secs)?;
        let (from, to) = self.parse_range(query.range, &query.metric_id)?;
        let concrete_query = ConcreteQuery {
            metric_id: query.metric_id,
            from,
            to,
        };

        match aggr_window_secs {
            Some(0) => self.collect(concrete_query), // Particular case, no aggregation
            Some(n) => self.aggregate(concrete_query, query.aggregation, n * 1000),
            None => self.aggregate(concrete_query, query.aggregation, to - from + 1),
        }
    }

    // Private

    fn aggregate(
        &self,
        ConcreteQuery {
            metric_id,
            from,
            to,
        }: ConcreteQuery,
        aggregation: AggregationOpcode,
        window_size: i64,
    ) -> Result<QueryResult, QueryError> {
        let time_range = to - from;
        let n_windows = (time_range / window_size) + 1; // last window is incomplete
        let mut results = Window::create_with_size(n_windows.try_into().unwrap());
        let dirpath = format!("{}/{}", &self.database_path, &metric_id);
        let mut current_partition = self.ms_timestamp_to_partition(from);
        let last_partition = self.ms_timestamp_to_partition(to);

        while current_partition <= last_partition {
            let filepath = format!("{}/{}.csv", &dirpath, current_partition);
            let open_file_result = self.open_file_ro(&filepath);
            match open_file_result {
                OpenFileResult::ReadOnly(file) => self.process_file_aggr(
                    &file,
                    current_partition,
                    from,
                    window_size,
                    &mut results,
                )?,
                OpenFileResult::RWLocked(file) => {
                    self.process_file_aggr(
                        &file,
                        current_partition,
                        from,
                        window_size,
                        &mut results,
                    )?;
                    file.unlock().unwrap();
                }
                OpenFileResult::Inexistent => {}
            };

            current_partition += 1;
        }

        Ok(results.iter().map(|w| w.aggregate(aggregation)).collect())
    }

    fn process_file_aggr(
        &self,
        file: &File,
        partition: i64,
        from: i64,
        window_size: i64,
        results: &mut [Window],
    ) -> Result<(), Error> {
        let mut rdr = ReaderBuilder::new().has_headers(false).from_reader(file);
        for partition_row in rdr.deserialize::<PartitionRow>() {
            let PartitionRow { ms_rem, value } = partition_row?;
            let timestamp = (partition * self.partition_secs * 1000) + ms_rem;
            if timestamp < from {
                continue;
            }
            let assigned_window_idx = ((timestamp - from) / window_size) as usize;
            results[assigned_window_idx].push(value);
        }

        Ok(())
    }

    fn collect(
        &self,
        ConcreteQuery {
            metric_id,
            from,
            to,
        }: ConcreteQuery,
    ) -> Result<QueryResult, QueryError> {
        let mut results = Vec::new();
        let dirpath = format!("{}/{}", &self.database_path, &metric_id);
        let mut current_partition = self.ms_timestamp_to_partition(from);
        let last_partition = self.ms_timestamp_to_partition(to);

        while current_partition <= last_partition {
            let filepath = format!("{}/{}.csv", &dirpath, current_partition);
            let open_file_result = self.open_file_ro(&filepath);
            match open_file_result {
                OpenFileResult::ReadOnly(file) => self.process_file_collect(&file, &mut results)?,
                OpenFileResult::RWLocked(file) => {
                    self.process_file_collect(&file, &mut results)?;
                    file.unlock().unwrap();
                }
                OpenFileResult::Inexistent => {}
            };

            current_partition += 1;
        }

        Ok(results)
    }

    fn process_file_collect(&self, file: &File, results: &mut QueryResult) -> Result<(), Error> {
        let mut rdr = ReaderBuilder::new().has_headers(false).from_reader(file);
        for partition_row in rdr.deserialize::<PartitionRow>() {
            let PartitionRow { ms_rem: _, value } = partition_row?;
            results.push(Some(value))
        }

        Ok(())
    }

    fn parse_range(
        &mut self,
        range: Option<DateTimeRange>,
        metric_id: &str,
    ) -> Result<(i64, i64), Error> {
        match range {
            Some(range) => Ok((range.from.timestamp_millis(), range.to.timestamp_millis())),
            None => {
                let from = self.get_first_timestamp(metric_id)?;
                let to = Utc::now().timestamp_millis();

                Ok((from, to))
            }
        }
    }

    fn open_file_ro(&self, filepath: &str) -> OpenFileResult {
        if let Ok(file) = fs::File::open(&filepath) {
            return OpenFileResult::ReadOnly(file);
        };

        // File not exist. Two posibilities:
        // 1. File is being written, so is in rw mode (.w).
        //    Here, we check if RW file exists:
        //      a. if it exists, we lock it.
        //      b. if it does not exist, we have to check again to see
        //         if it has been marked as RO or if it does not exist.
        // 2. File does not exist.

        let rw_filepath = format!("{}.w", filepath);
        match fs::File::open(&rw_filepath) {
            Ok(rw_file) => {
                rw_file.lock_shared().unwrap();
                OpenFileResult::RWLocked(rw_file)
            }
            Err(_) => match fs::File::open(&filepath) {
                Ok(ro_file) => OpenFileResult::ReadOnly(ro_file),
                Err(_) => OpenFileResult::Inexistent,
            },
        }
    }

    fn ms_timestamp_to_partition(&self, ms_timestamp: i64) -> i64 {
        (ms_timestamp / 1000) / self.partition_secs
    }

    fn get_first_timestamp(&mut self, metric_id: &str) -> Result<i64, Error> {
        if let Some(first_timestamp) = self.first_timestamp_cache.get(metric_id) {
            return Ok(*first_timestamp);
        };

        // Compute result
        let partition = self.read_first_partition(metric_id)?;
        let timestamp = self.read_first_timestamp_from(metric_id, partition)?;

        // Save result in cache
        self.first_timestamp_cache
            .insert(metric_id.to_string(), timestamp);

        Ok(timestamp)
    }

    fn read_first_timestamp_from(&self, metric_id: &str, partition: i64) -> Result<i64, Error> {
        let filepath = format!("{}/{}/{}.csv", &self.database_path, metric_id, partition);

        match self.open_file_ro(&filepath) {
            OpenFileResult::ReadOnly(file) => self.read_first_timestamp_from_file(&file, partition),
            OpenFileResult::RWLocked(file) => {
                let timestamp = self.read_first_timestamp_from_file(&file, partition)?;
                file.unlock().unwrap();
                Ok(timestamp)
            }
            OpenFileResult::Inexistent => unreachable!(),
        }
    }

    fn read_first_timestamp_from_file(&self, file: &File, partition: i64) -> Result<i64, Error> {
        let mut rdr = ReaderBuilder::new().has_headers(false).from_reader(file);
        let PartitionRow { ms_rem, value: _ } = rdr
            .deserialize::<PartitionRow>()
            .next()
            .expect("Invalid first partition metadata file")?;
        let timestamp = (partition * self.partition_secs * 1000) + ms_rem;

        Ok(timestamp)
    }

    fn read_first_partition(&self, metric_id: &str) -> Result<i64, Error> {
        let filepath = format!(
            "{}/{}/{}",
            &self.database_path, metric_id, METRIC_FIRST_PARTITION_FILE
        );
        let mut file = fs::File::open(filepath)?;
        let mut buf = [0u8; size_of::<i64>()];
        file.read_exact(&mut buf)?;

        Ok(i64::from_le_bytes(buf))
    }

    fn check_if_metric_exists(&self, metric_id: &str) -> Result<(), QueryError> {
        let first_partition_filepath = format!(
            "{}/{}/{}",
            self.database_path, metric_id, METRIC_FIRST_PARTITION_FILE
        );
        match Path::new(&first_partition_filepath).exists() {
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
