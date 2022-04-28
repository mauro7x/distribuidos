use crate::{
    check_executor::CheckExecutor,
    checks::read_checks,
    config::Config,
    types::{Check, CheckRequest},
};
use chrono::{Duration, TimeZone, Utc};
use distribuidos_sync::QueueError;
use distribuidos_tp1_protocols::types::{DateTimeRange, Query};
use distribuidos_types::BoxResult;
use std::{
    sync::mpsc::{Receiver, TryRecvError},
    thread,
};

use log::*;

pub struct Dispatcher {
    frequency_secs: i64,
    ctrlc_receiver: Receiver<()>,
    query_executor: CheckExecutor,
    checks: Vec<Check>,
    stopped: bool,
}

impl Dispatcher {
    pub fn new(rx: Receiver<()>) -> BoxResult<Dispatcher> {
        trace!("Creating Dispatcher for queries");
        let config = Config::new()?;
        let frequency_secs = i64::from(config.frequency_secs);
        let query_executor = CheckExecutor::new()?;
        let checks = read_checks()?;

        debug!(
            "Dispatcher created with frequency = {:?} secs and checks: {:#?}",
            frequency_secs, checks
        );
        let dispatcher = Dispatcher {
            frequency_secs,
            ctrlc_receiver: rx,
            query_executor,
            checks,
            stopped: false,
        };

        Ok(dispatcher)
    }

    pub fn run(&mut self) -> BoxResult<()> {
        self.first_run()?;

        while !self.stopped {
            for check in self.checks.iter_mut() {
                if Dispatcher::stopped(&self.ctrlc_receiver)? {
                    self.stopped = true;
                    break;
                }

                let from_ts = check
                    .last_to_timestamp
                    .expect("After first run, check should always have a last_to_timestamp");
                let to_ts = from_ts + self.frequency_secs;
                let sleep_time_secs = to_ts - Utc::now().timestamp();
                if sleep_time_secs > 0 {
                    trace!("Sleeping for {} until next check", sleep_time_secs);
                    let sleep_duration = Duration::seconds(sleep_time_secs);
                    thread::sleep(sleep_duration.to_std().unwrap());
                }

                let query = Dispatcher::build_query(check, from_ts, to_ts);
                let check_request = CheckRequest {
                    query,
                    limit: check.limit,
                };
                if let Err(QueueError::Full(query)) = self.query_executor.execute(check_request) {
                    warn!("Alert service at capacity, ignoring query: {:?}", query);
                }

                check.last_to_timestamp = Some(to_ts);
            }
        }

        Ok(())
    }

    fn first_run(&mut self) -> BoxResult<()> {
        let sleep_time = Duration::seconds(self.frequency_secs);
        let sleep_time_between_checks = sleep_time / self.checks.len().try_into().unwrap();

        for check in &mut self.checks.iter_mut() {
            if Dispatcher::stopped(&self.ctrlc_receiver)? {
                break;
            }

            let now_ts = Utc::now().timestamp();
            let (from_ts, to_ts) = (now_ts - self.frequency_secs, now_ts);
            let query = Dispatcher::build_query(check, from_ts, to_ts);
            debug!("Dispatching for the first time query: {:#?}", query);
            let check_request = CheckRequest {
                query,
                limit: check.limit,
            };
            self.query_executor
                .execute(check_request)
                .expect("First run should never fail");
            check.last_to_timestamp = Some(to_ts);

            trace!("Sleeping {:?} in the first run", sleep_time_between_checks);
            thread::sleep(sleep_time_between_checks.to_std().unwrap());
        }

        Ok(())
    }

    fn build_query(check: &Check, from_ts: i64, to_ts: i64) -> Query {
        Query {
            metric_id: check.metric_id.clone(),
            range: Some(DateTimeRange {
                from: Utc.timestamp(from_ts, 0),
                to: Utc.timestamp(to_ts, 0),
            }),
            aggregation: check.aggregation,
            aggregation_window_secs: Some(check.aggregation_window_secs),
        }
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
}

impl Drop for Dispatcher {
    fn drop(&mut self) {
        trace!("Joining query executor...");
        self.query_executor.join();
        trace!("Query executor joined");
    }
}
