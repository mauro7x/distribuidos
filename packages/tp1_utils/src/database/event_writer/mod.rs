mod metric_file;

use distribuidos_tp1_protocols::types::Event;
use metric_file::MetricFile;
use std::{collections::HashMap, io::Error};

pub struct EventWriter {
    database_path: String,
    partition_secs: u32,
    file_map: HashMap<String, MetricFile>,
}

impl EventWriter {
    pub fn new(database_path: String, partition_secs: u32) -> EventWriter {
        EventWriter {
            database_path,
            partition_secs,
            file_map: HashMap::new(),
        }
    }

    pub fn write(&mut self, event: Event) -> Result<(), Error> {
        let file = self
            .file_map
            .entry(event.metric_id.clone())
            .or_insert(MetricFile::new(
                self.partition_secs,
                &event.metric_id,
                &self.database_path,
            )?);

        file.write(event)?;

        Ok(())
    }

    pub fn handle_timeout(&mut self) -> Result<(), Error> {
        for file in self.file_map.values_mut() {
            file.flush_if_needed()?;
        }

        Ok(())
    }
}
