use std::{error::Error, process};

use app::{config::Config, server::Server};

fn run() -> Result<(), Box<dyn Error>> {
    let config = Config::new()?;
    println!("Config: {:?}", config);

    let server = Server::new();
    server.say_hi();

    Ok(())
}

fn main() {
    if let Err(err) = run() {
        println!("{}", err);
        process::exit(1);
    }
}
