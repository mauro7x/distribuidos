use crate::manual::constants::*;
use std::io::Write;

use log::*;

pub fn print_expected() {
    println!(
        "Expected format: {}\n(leave blank for optional: metric_id,,,,aggregation)",
        EXPECTED_FORMAT
    )
}

pub fn prompt() {
    print!("\nIngress query: ");
    std::io::stdout().flush().unwrap();
}

pub fn invalid_input() {
    error!("Client: invalid input.");
    print_expected();
}
