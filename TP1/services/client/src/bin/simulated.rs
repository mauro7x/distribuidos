use client::simulated::run;
use log::*;
use std::process::exit;

fn main() {
    pretty_env_logger::init();

    if let Err(err) = run() {
        error!("{}", err);
        exit(1);
    }
}
