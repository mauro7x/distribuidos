use distribuidos_tp1_protocols::types::{DateTime, Event};
use std::{
    fs::{self, File},
    io::{Error, Write},
};

use chrono::{Date, Datelike, Timelike, Utc};
use fs2::FileExt;
use log::*;

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
        self.flush_if_needed()?;
        let secs = self.datetime.num_seconds_from_midnight();
        let secs_rem = secs % self.partition_secs;

        // CRITICAL SECTION
        self.file.lock_exclusive()?;
        if let Err(e) = writeln!(self.file, "{},{}", secs_rem, event.value) {
            error!("Couldn't write to file: {}", e);
        }
        self.file.unlock()?;

        Ok(())
    }

    pub fn flush_if_needed(&mut self) -> Result<(), Error> {
        let now = Utc::now();
        let new_abs_part_number = MetricFile::abs_partition_number(&now, self.partition_secs);
        let current_abs_part_number =
            MetricFile::abs_partition_number(&self.datetime, self.partition_secs);

        if new_abs_part_number != current_abs_part_number {
            self.flush(now)?;
        };

        Ok(())
    }

    fn flush(&mut self, now: DateTime) -> Result<(), Error> {
        let new_file = MetricFile::create_file(
            &now,
            self.partition_secs,
            &self.metric_id,
            &self.database_path,
        )?;

        self.file.lock_exclusive()?;
        let partition_number = MetricFile::partition_number(&self.datetime, self.partition_secs);
        let dirpath =
            MetricFile::dirpath(&self.datetime.date(), &self.database_path, &self.metric_id);
        let from = MetricFile::filepath(&dirpath, partition_number, false);
        let to = MetricFile::filepath(&dirpath, partition_number, true);
        if let Err(err) = fs::rename(from, to) {
            error!("Failed to rename MetricFile - {}", err);
        };
        self.file.unlock()?;

        // Swap
        self.file = new_file;
        self.datetime = now;

        Ok(())
    }

    fn dirpath(date: &Date<Utc>, database_path: &String, metric_id: &String) -> String {
        format!(
            "{}/{}/{}{}{}",
            database_path,
            metric_id,
            date.year(),
            date.month(),
            date.day()
        )
    }

    fn filepath(dirpath: &String, partition_number: u32, ro: bool) -> String {
        let suffix = match ro {
            true => "",
            false => ".w",
        };

        format!("{}/{}.csv{}", &dirpath, partition_number, suffix)
    }

    fn abs_partition_number(datetime: &DateTime, partition_secs: u32) -> i64 {
        let secs = datetime.timestamp();
        secs / i64::from(partition_secs)
    }

    fn partition_number(datetime: &DateTime, partition_secs: u32) -> u32 {
        let secs = datetime.num_seconds_from_midnight();
        secs / partition_secs
    }

    fn create_file(
        datetime: &DateTime,
        partition_secs: u32,
        metric_id: &String,
        database_path: &String,
    ) -> Result<File, Error> {
        let partition_number = MetricFile::partition_number(datetime, partition_secs);
        let dirpath = MetricFile::dirpath(&datetime.date(), database_path, metric_id);
        let filepath = MetricFile::filepath(&dirpath, partition_number, false);

        fs::create_dir_all(&dirpath)?;

        fs::OpenOptions::new()
            .create(true)
            .write(true)
            .append(true)
            .open(filepath)
    }
}
