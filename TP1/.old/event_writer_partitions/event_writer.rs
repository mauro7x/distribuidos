use distribuidos_tp1_protocols::types::Event;
use std::{collections::HashMap, io::Error};

use super::metric_file::MetricFile;

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
        let file = match self.file_map.get_mut(&event.metric_id) {
            Some(file) => file,
            None => {
                let file =
                    MetricFile::new(self.partition_secs, &event.metric_id, &self.database_path)?;
                self.file_map.insert(event.metric_id.clone(), file);
                self.file_map.get_mut(&event.metric_id).unwrap()
            }
        };

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
