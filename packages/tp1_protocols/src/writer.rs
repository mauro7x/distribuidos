use crate::{
    opcodes::*,
    types::{errors::SendError, AggregationOpcode, DateTime, DateTimeRange, Event, Query},
};
use std::{
    io::{BufWriter, Write},
    net::TcpStream,
};

type TcpWriter<'a> = BufWriter<&'a TcpStream>;
type WriterResult = Result<(), SendError>;

pub struct Writer<'a> {
    writer: TcpWriter<'a>,
}

impl Writer<'_> {
    pub fn new(stream: &TcpStream) -> Writer {
        Writer {
            writer: TcpWriter::new(stream),
        }
    }

    pub fn flush(&mut self) -> WriterResult {
        self.writer.flush()?;
        Ok(())
    }

    fn write_all(&mut self, buf: &[u8]) -> WriterResult {
        self.writer.write_all(buf)?;
        Ok(())
    }

    // API

    pub fn query(&mut self, query: Query) -> WriterResult {
        self.opcode(OP_QUERY)?;
        self.metric_id(query.metric_id)?;
        self.range(query.range)?;
        self.aggregation(query.aggregation)?;
        self.aggr_window(query.aggregation_window_secs)?;

        self.flush()?;

        Ok(())
    }

    pub fn event(&mut self, event: Event) -> WriterResult {
        self.opcode(OP_EVENT)?;
        self.metric_id(event.metric_id)?;
        self.metric_value(event.value)?;

        self.flush()?;

        Ok(())
    }

    // Generic

    pub fn u8(&mut self, value: u8) -> WriterResult {
        self.write_all(&[value])
    }

    pub fn f32(&mut self, value: f32) -> WriterResult {
        self.write_all(&value.to_le_bytes())
    }

    pub fn string(&mut self, string: String) -> WriterResult {
        let length = string.len().try_into().map_err(|_| SendError::Invalid)?;
        self.write_all(&[length])?;
        self.write_all(string.as_bytes())
    }

    // Wrappers

    pub fn opcode(&mut self, opcode: Opcode) -> WriterResult {
        self.u8(opcode)
    }

    pub fn metric_id(&mut self, metric_id: String) -> WriterResult {
        self.string(metric_id)
    }

    pub fn metric_value(&mut self, metric_value: f32) -> WriterResult {
        self.f32(metric_value)
    }

    pub fn range(&mut self, range: Option<DateTimeRange>) -> WriterResult {
        if let Some(range) = range {
            self.datetime(range.from)?;
            self.datetime(range.to)?;
        }
        Ok(())
    }

    pub fn datetime(&mut self, datetime: DateTime) -> WriterResult {
        self.write_all(datetime.to_rfc3339().as_bytes())
    }

    pub fn aggregation(&mut self, aggregation: AggregationOpcode) -> WriterResult {
        self.u8(aggregation as u8)
    }

    pub fn aggr_window(&mut self, aggr_window: Option<f32>) -> WriterResult {
        if let Some(aggr_window) = aggr_window {
            self.f32(aggr_window)?;
        }
        Ok(())
    }
}
