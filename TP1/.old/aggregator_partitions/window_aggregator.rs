use std::f32;

use chrono::{Duration, Utc};
use distribuidos_tp1_protocols::types::{AggregationOpcode, DateTime};

struct Current {
    end: DateTime,
    sum: f32,
    count: usize,
    max: f32,
    min: f32,
}

impl Current {
    fn new(end: DateTime) -> Current {
        Current {
            end,
            sum: 0.0,
            count: 0,
            max: f32::NAN,
            min: f32::NAN,
        }
    }
}

pub struct WindowAggregator {
    pub result: Vec<f32>,
    aggregation: AggregationOpcode,
    current: Current,
    aggr_window_secs: Option<i64>,
}

impl WindowAggregator {
    pub fn new(
        aggregation: AggregationOpcode,
        end: DateTime,
        aggregation_window_secs: Option<i64>,
    ) -> WindowAggregator {
        let current_end = match aggregation_window_secs {
            Some(aggr_window_secs) => Utc::now() + Duration::seconds(aggr_window_secs),
            None => end,
        };
        let current = Current::new(current_end);

        WindowAggregator {
            result: Vec::new(),
            aggregation,
            current,
            aggr_window_secs: aggregation_window_secs,
        }
    }

    // fn push_current(&mut self) {
    //     self.result.push(self.aggregate());
    // }

    fn aggregate(&self) -> f32 {
        match self.aggregation {
            AggregationOpcode::AVG => self.current.sum / (self.current.count as f32),
            AggregationOpcode::MIN => self.current.min,
            AggregationOpcode::MAX => self.current.max,
            AggregationOpcode::COUNT => self.current.count as f32,
        }
    }
}
