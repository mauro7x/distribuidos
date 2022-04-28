mod config;
mod constants;

use self::config::Config;
use crate::{simulated::constants::EVENTS_FILE_PATH, types::Row};
use distribuidos_sync::UnboundedWorkerPool;
use distribuidos_tp1_gateway::Gateway;
use distribuidos_tp1_protocols::types::{errors::SendError, Event};
use distribuidos_types::BoxResult;
use std::{
    fs,
    sync::mpsc::{self, Receiver, TryRecvError},
    thread, time,
};

use log::*;

#[derive(Clone)]
struct Context {
    gateway: Gateway,
}

struct EventWithId {
    id: usize,
    event: Event,
}

fn stopped(rx: &Receiver<()>) -> BoxResult<bool> {
    match rx.try_recv() {
        Ok(_) => Ok(true),
        Err(TryRecvError::Empty) => Ok(false),
        Err(TryRecvError::Disconnected) => {
            Err("Ctrl-C signal receiver disconnected unexpectedly".into())
        }
    }
}

fn loop_sending(events: Vec<Event>, rx: Receiver<()>) -> BoxResult<()> {
    let Config {
        thread_pool_size,
        repeat_every_ms,
        between_requests_ms,
    } = Config::new()?;
    let gateway = Gateway::new()?;
    let context = Context { gateway };
    let mut workers = UnboundedWorkerPool::new(thread_pool_size, context, handler);
    let mut next_id = 0;

    loop {
        if stopped(&rx)? {
            break;
        }

        for event in events.iter() {
            let event = EventWithId {
                event: event.clone(),
                id: next_id,
            };
            next_id += 1;
            workers.execute(event);

            if between_requests_ms > 0 {
                thread::sleep(time::Duration::from_millis(between_requests_ms));
            }
        }

        if repeat_every_ms == 0 {
            break;
        }

        thread::sleep(time::Duration::from_millis(repeat_every_ms));
    }

    workers.join();

    Ok(())
}

fn handler(Context { gateway }: &mut Context, EventWithId { id, event }: EventWithId) {
    match gateway.send_event(event) {
        Ok(_) => info!("[Event #{}] Accepted by server", id),
        Err(SendError::Invalid) => error!("[Event #{}] Received invalid format", id),
        Err(SendError::ServerAtCapacity) => warn!("[Event #{}] Server at capacity", id),
        Err(SendError::InternalServerError) => error!("[Event #{}] Internal Server Error", id),
        Err(SendError::IOError(e)) => error!("[Event #{}] IOError: {}", id, e),
    };
}

pub fn run() -> BoxResult<()> {
    let input = fs::File::open(EVENTS_FILE_PATH)?;
    let mut rdr = csv::ReaderBuilder::new()
        .has_headers(false)
        .from_reader(input);
    let mut events = vec![];
    for input in rdr.deserialize::<Row>() {
        let event = Event::from(input?);
        events.push(event);
    }
    debug!("Running with events: {:#?}", events);

    let (tx, rx) = mpsc::channel();
    ctrlc::set_handler(move || tx.send(()).expect("Could not send signal on channel."))
        .expect("Error setting Ctrl-C handler");

    loop_sending(events, rx)?;

    Ok(())
}
