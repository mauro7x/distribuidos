mod config;
mod constants;

use self::config::Config;
use crate::{simulated::constants::QUERIES_FILE_PATH, types::SimulatedRow};
use chrono::{Duration, Utc};
use distribuidos_sync::UnboundedWorkerPool;
use distribuidos_tp1_gateway::Gateway;
use distribuidos_tp1_protocols::types::{errors::QueryError, DateTimeRange, Query};
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

struct QueryWithId {
    id: usize,
    query: Query,
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

fn parse_query_row(query_row: &SimulatedRow) -> Query {
    let range = DateTimeRange {
        from: Utc::now()
            - Duration::hours(query_row.hh.into())
            - Duration::minutes(query_row.mm.into())
            - Duration::seconds(query_row.ss.into()),
        to: Utc::now(),
    };

    Query {
        metric_id: query_row.metric_id.clone(),
        range: Some(range),
        aggregation: query_row.aggregation,
        aggregation_window_secs: query_row.aggr_window_secs,
    }
}

fn loop_sending(query_rows: Vec<SimulatedRow>, rx: Receiver<()>) -> BoxResult<()> {
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

        for query_row in query_rows.iter() {
            let query = QueryWithId {
                query: parse_query_row(query_row),
                id: next_id,
            };
            next_id += 1;
            workers.execute(query);

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

fn handler(Context { gateway }: &mut Context, QueryWithId { id, query }: QueryWithId) {
    match gateway.send_query(query) {
        Ok(_) => info!("[Query #{}] Accepted by server", id),
        Err(QueryError::Invalid)
        | Err(QueryError::InvalidRange)
        | Err(QueryError::InvalidAggrWindow) => error!("[Query #{}] Received invalid format", id),
        Err(QueryError::ServerAtCapacity) => warn!("[Query #{}] Server at capacity", id),
        Err(QueryError::InternalServerError) => error!("[Query #{}] Internal Serve Error", id),
        Err(QueryError::MetricNotFound) => warn!("[Query #{}] Metric not found", id),
        Err(QueryError::IOError(e)) => error!("[Query #{}] IOError: {}", id, e),
    };
}

pub fn run() -> BoxResult<()> {
    let input = fs::File::open(QUERIES_FILE_PATH)?;
    let mut rdr = csv::ReaderBuilder::new()
        .has_headers(false)
        .from_reader(input);
    let mut query_rows = vec![];
    for input in rdr.deserialize::<SimulatedRow>() {
        query_rows.push(input?);
    }
    debug!("Running with queries: {:#?}", query_rows);

    let (tx, rx) = mpsc::channel();
    ctrlc::set_handler(move || tx.send(()).expect("Could not send signal on channel."))
        .expect("Error setting Ctrl-C handler");

    loop_sending(query_rows, rx)?;

    Ok(())
}
