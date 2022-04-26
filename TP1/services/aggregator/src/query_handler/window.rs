use std::f32;

use distribuidos_tp1_protocols::types::AggregationOpcode;

pub struct Window {
    pub sum: f32,
    pub count: usize,
    pub max: Option<f32>,
    pub min: Option<f32>,
}

impl Window {
    pub fn create_with_size(n: usize) -> Vec<Window> {
        (0..n).map(|_| Window::default()).collect()
    }

    pub fn aggregate(&self, aggregation: AggregationOpcode) -> Option<f32> {
        match aggregation {
            AggregationOpcode::AVG => match self.count == 0 {
                true => None,
                false => Some(self.sum / (self.count as f32)),
            },
            AggregationOpcode::MIN => self.min,
            AggregationOpcode::MAX => self.max,
            AggregationOpcode::COUNT => Some(self.count as f32),
        }
    }

    pub fn push(&mut self, value: f32) {
        self.sum += value;
        self.count += 1;
        self.max = match self.max {
            None => Some(value),
            Some(a) if a < value => Some(value),
            a => a,
        };
        self.min = match self.min {
            None => Some(value),
            Some(a) if a > value => Some(value),
            a => a,
        };
    }
}

impl Default for Window {
    fn default() -> Window {
        Window {
            sum: 0.0,
            count: 0,
            max: None,
            min: None,
        }
    }
}
