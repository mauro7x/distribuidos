use distribuidos_sync::SingleWorker;
use distribuidos_types::BoxResult;

mod config;
mod constants;

use crate::{forker::config::Config, types::QueryRequest};

use log::*;

pub type Forker = SingleWorker<QueryRequest>;

#[derive(Clone)]
pub struct Context {}

pub fn new() -> BoxResult<Forker> {
    let config = Config::new()?;
    debug!("Running with {:?}", config);
    let Config { forker_queue_size } = config;

    let forker_context = Context {};
    let forker = SingleWorker::new(forker_queue_size, forker_context, request_handler);

    Ok(forker)
}

fn request_handler(_context: &mut Context, request: QueryRequest) {
    if let Err(err) = inner_request_handler(request) {
        warn!("Request handler failed - {:?}", err);
    }
}

fn inner_request_handler(QueryRequest { from, query: _ }: QueryRequest) -> BoxResult<()> {
    debug!("Handling request from {:?}", from);
    // match requests::recv_event(&mut stream) {
    //     Ok(event) => dispatch_event(dispatchers, stream, event),
    //     Err(RecvError::Invalid) => {
    //         warn!("Invalid format while receiving event");
    //         responses::send_invalid_format(&mut stream).map_err(|e| e.into())
    //     }
    //     Err(RecvError::Terminated) => Ok(()),
    //     Err(RecvError::IOError(e)) => Err(e.into()),
    // }

    Ok(())
}
