use distribuidos_tp1_protocols::types::{DateTime, Event};
use distribuidos_tp1_utils::file_utils;
use std::{
    fs::{self, File},
    io::{Error, Write},
};

use chrono::{Timelike, Utc};
use fs2::FileExt;
use log::*;

#[derive(Debug)]
pub struct MetricFile {
    metric_id: String,
    database_path: String,
    partition_secs: u32,
    file: File,
    datetime: DateTime,
}

impl MetricFile {
    pub fn new(
        partition_secs: u32,
        metric_id: &String,
        database_path: &String,
    ) -> Result<MetricFile, Error> {
        let datetime = Utc::now();
        let file = MetricFile::create_file(&datetime, partition_secs, metric_id, database_path)?;

        Ok(MetricFile {
            metric_id: metric_id.clone(),
            database_path: database_path.clone(),
            partition_secs,
            file,
            datetime,
        })
    }

    pub fn write(&mut self, event: Event) -> Result<(), Error> {
        let secs = self.flush_if_needed()?;
        let secs_rem = secs % self.partition_secs;

        // CRITICAL SECTION
        self.file.lock_exclusive()?;
        if let Err(e) = writeln!(self.file, "{},{}", secs_rem, event.value) {
            error!("Couldn't write to file: {}", e);
        }
        self.file.unlock()?;

        Ok(())
    }

    pub fn flush_if_needed(&mut self) -> Result<u32, Error> {
        let now = Utc::now();
        let new_abs_part_number = file_utils::abs_partition_number(&now, self.partition_secs);
        let current_abs_part_number =
            file_utils::abs_partition_number(&self.datetime, self.partition_secs);
        let secs = now.num_seconds_from_midnight();

        if new_abs_part_number != current_abs_part_number {
            self.flush(now)?;
        };

        Ok(secs)
    }

    fn flush(&mut self, now: DateTime) -> Result<(), Error> {
        let new_file = MetricFile::create_file(
            &now,
            self.partition_secs,
            &self.metric_id,
            &self.database_path,
        )?;

        self._safe_flush()?;

        // Swap
        self.file = new_file;
        self.datetime = now;

        Ok(())
    }

    fn _safe_flush(&mut self) -> Result<(), Error> {
        self.file.lock_exclusive()?;
        let partition_number = file_utils::partition_number(&self.datetime, self.partition_secs);
        let dirpath =
            file_utils::dirpath(&self.datetime.date(), &self.database_path, &self.metric_id);
        let from = file_utils::filepath(&dirpath, partition_number, false);
        let to = file_utils::filepath(&dirpath, partition_number, true);
        if let Err(err) = fs::rename(from, to) {
            error!("Failed to rename MetricFile - {}", err);
        };
        self.file.unlock()?;

        Ok(())
    }

    fn create_file(
        datetime: &DateTime,
        partition_secs: u32,
        metric_id: &String,
        database_path: &String,
    ) -> Result<File, Error> {
        let partition_number = file_utils::partition_number(datetime, partition_secs);
        let dirpath = file_utils::dirpath(&datetime.date(), database_path, metric_id);
        let filepath = file_utils::filepath(&dirpath, partition_number, false);

        fs::create_dir_all(&dirpath)?;

        fs::OpenOptions::new()
            .create(true)
            .write(true)
            .append(true)
            .open(filepath)
    }
}

impl Drop for MetricFile {
    fn drop(&mut self) {
        if let Err(e) = self._safe_flush() {
            error!(
                "Metric file for {} could not be flushed when exiting - {}",
                self.metric_id, e
            )
        }
    }
}
