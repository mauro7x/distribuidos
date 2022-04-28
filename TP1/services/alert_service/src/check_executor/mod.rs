mod config;
mod constants;

use std::{
    fs,
    io::{Error, Write},
};

use crate::types::CheckRequest;

use self::config::Config;
use distribuidos_sync::{QueueError, WorkerPool};
use distribuidos_tp1_gateway::Gateway;
use distribuidos_tp1_protocols::types::{errors::QueryError, Query};
use distribuidos_types::BoxResult;

use fs2::FileExt;
use log::*;

#[derive(Clone)]
struct Context {
    gateway: Gateway,
    output_dirpath: String,
}

pub struct CheckExecutor {
    handlers: WorkerPool<CheckRequest>,
}

impl CheckExecutor {
    pub fn new() -> BoxResult<CheckExecutor> {
        let Config {
            thread_pool_size,
            queue_size,
            output_dirpath,
        } = Config::new()?;
        fs::create_dir_all(&output_dirpath)?;
        let context = Context {
            gateway: Gateway::new()?,
            output_dirpath,
        };
        let handlers = WorkerPool::new(
            thread_pool_size,
            queue_size,
            context,
            CheckExecutor::query_handler,
        );

        Ok(CheckExecutor { handlers })
    }

    pub fn join(&mut self) {
        self.handlers.join();
    }

    pub fn execute(&self, check_request: CheckRequest) -> Result<(), QueueError<CheckRequest>> {
        self.handlers.execute(check_request)
    }

    fn query_handler(context: &mut Context, CheckRequest { limit, query }: CheckRequest) {
        if let Err(err) = CheckExecutor::inner_handler(context, query, limit) {
            warn!("[CheckExecutor] Failed - {}", err);
        }
    }

    fn inner_handler(
        Context {
            gateway,
            output_dirpath,
        }: &mut Context,
        query: Query,
        limit: f32,
    ) -> Result<(), Error> {
        debug!("[CheckExecutor] Received query: {:?}", query);
        match gateway.send_query(query.clone()) {
            Ok(result) => {
                for value in result {
                    match value {
                        Some(value) if value > limit => {
                            info!("Alert triggered for {}", query.metric_id);
                            CheckExecutor::write_alert(query, limit, output_dirpath)?;
                            break;
                        }
                        Some(_) | None => {}
                    }
                }
            }
            Err(QueryError::ServerAtCapacity) => warn!("Server at capacity"),
            Err(QueryError::InternalServerError) => error!("Internal server error"),
            Err(QueryError::MetricNotFound) => warn!("Metric not found"),
            Err(QueryError::Invalid)
            | Err(QueryError::InvalidRange)
            | Err(QueryError::InvalidAggrWindow) => {
                error!("Received unexpected response from server")
            }
            Err(QueryError::IOError(e)) => error!("IOError:{}", e),
        };

        Ok(())
    }

    fn write_alert(query: Query, limit: f32, output_dirpath: &String) -> Result<(), Error> {
        let filepath = format!("{}/{}.csv", output_dirpath, query.metric_id);
        let mut file = fs::OpenOptions::new()
            .create(true)
            .write(true)
            .append(true)
            .open(filepath)?;

        // We can unwrap since all these fields must be present
        let range = query.range.unwrap();
        let (from, to) = (range.from.to_rfc3339(), range.to.to_rfc3339());
        let aggregation_window_secs = query.aggregation_window_secs.unwrap();

        // Safe write
        file.lock_exclusive().unwrap();
        write!(
            file,
            "{},{},{:?},{},{}",
            from, to, query.aggregation, aggregation_window_secs, limit
        )?;
        file.flush().map_err(|e| {
            file.unlock().unwrap();
            e
        })?;
        file.unlock().unwrap();

        Ok(())
    }
}
