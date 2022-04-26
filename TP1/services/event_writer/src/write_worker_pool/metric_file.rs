use distribuidos_tp1_protocols::types::Event;
use distribuidos_tp1_utils::file_utils;
use std::{
    fs::{self, File},
    io::{Error, Write},
    path::Path,
};

use chrono::Utc;
use fs2::FileExt;
use log::*;

#[derive(Debug)]
pub struct MetricFile {
    dirpath: String,
    partition_secs: i64,
    partition: i64,
    file: File,
}

impl MetricFile {
    pub fn new(
        metric_id: &String,
        database_path: &String,
        partition_secs: i64,
    ) -> Result<MetricFile, Error> {
        let now = Utc::now().timestamp();
        let partition = now / partition_secs;
        let dirpath = file_utils::dirpath(metric_id, database_path);

        // If file exists in RO mode, we switch it back to RW
        MetricFile::restore_if_exists(&dirpath, partition)?;
        let file = MetricFile::create_file(&dirpath, partition)?;

        Ok(MetricFile {
            dirpath,
            partition_secs,
            partition,
            file,
        })
    }

    pub fn write(&mut self, event: Event) -> Result<(), Error> {
        let now_millis = Utc::now().timestamp_millis();
        let now_secs = now_millis / 1000;
        let partition = now_secs / self.partition_secs;
        let ms_rem = now_millis - (partition * self.partition_secs * 1000);
        if partition != self.partition {
            self.flush(partition)?;
        };

        // CRITICAL SECTION
        self.file.lock_exclusive()?;
        if let Err(e) = writeln!(self.file, "{},{}", ms_rem, event.value) {
            error!("Couldn't write to file: {}", e);
        }
        self.file.unlock()?;

        Ok(())
    }

    pub fn flush_if_needed(&mut self) -> Result<(), Error> {
        let partition = Utc::now().timestamp() / self.partition_secs;
        if partition != self.partition {
            self.flush(partition)?;
        };

        Ok(())
    }

    // Private

    fn flush(&mut self, partition: i64) -> Result<(), Error> {
        let new_file = MetricFile::create_file(&self.dirpath, partition)?;
        self.safe_flush()?;

        // Swap internal state
        self.file = new_file;
        self.partition = partition;

        Ok(())
    }

    fn safe_flush(&self) -> Result<(), Error> {
        self.file.lock_exclusive()?;
        let from = file_utils::filepath(&self.dirpath, self.partition, false);
        let to = file_utils::filepath(&self.dirpath, self.partition, true);

        if let Err(err) = fs::rename(from, to) {
            error!("Failed to rename MetricFile - {}", err);
        };

        self.file.unlock()?;

        Ok(())
    }

    // Static

    fn restore_if_exists(dirpath: &String, partition: i64) -> Result<(), Error> {
        let ro_filepath = file_utils::filepath(dirpath, partition, true);
        if Path::new(&ro_filepath).exists() {
            let ro_file = fs::OpenOptions::new()
                .write(true)
                .append(true)
                .open(&ro_filepath)?;

            ro_file.lock_exclusive()?;
            let rw_filepath = file_utils::filepath(dirpath, partition, false);
            fs::rename(ro_filepath, rw_filepath)?;
            ro_file.unlock()?;
        };

        Ok(())
    }

    fn create_file(dirpath: &String, partition: i64) -> Result<File, Error> {
        fs::create_dir_all(&dirpath)?;
        let filepath = file_utils::filepath(dirpath, partition, false);

        fs::OpenOptions::new()
            .create(true)
            .write(true)
            .append(true)
            .open(filepath)
    }
}

impl Drop for MetricFile {
    fn drop(&mut self) {
        if let Err(e) = self.safe_flush() {
            error!("Metric file could not be flushed when exiting - {}", e)
        }
    }
}
