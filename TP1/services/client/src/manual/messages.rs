use crate::{constants::*, types::InputError};
use std::io::Write;

use log::*;

pub fn print_expected() {
    println!(
        "Expected format: {}\n  - Leave blank for optional args (example: metric_id,,,,aggregation)\n  - DateTime format: {} (example: {})\n  - Aggregation options: avg, min, max, count",
        EXPECTED_QUERY_FORMAT, DATETIME_FORMAT, DATETIME_FORMAT_EXAMPLE
    )
}

pub fn prompt() {
    print!("\nIngress query: ");
    std::io::stdout().flush().unwrap();
}

pub fn invalid_input(error: InputError) {
    match error {
        InputError::InvalidCSV => error!("Client input error: invalid csv line"),
        InputError::OnlyOneRange => error!("Client input error: 1 datetime found (expected 0 or 2"),
        InputError::InvalidDateTime => error!("Client input error: invalid datetime"),
        InputError::InvalidAggr => error!("Client input error: invalid aggregation"),
    };
    print_expected();
}
