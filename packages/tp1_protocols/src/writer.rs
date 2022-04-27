use crate::{
    opcodes::*,
    types::{
        errors::SendError, AggregationOpcode, DateTime, DateTimeRange, Event, Query, QueryResult,
    },
};
use std::{
    io::{BufWriter, Error, Write},
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

    pub fn query_result(&mut self, query_result: QueryResult) -> Result<(), Error> {
        self.writer.write_all(&[OP_QUERY_RESPONSE])?;
        for value in query_result {
            self.query_result_value(value)?;
        }
        self.writer.write_all(&[EOF])?;

        self.writer.flush()?;

        Ok(())
    }

    pub fn opcode(&mut self, opcode: Opcode) -> WriterResult {
        self.u8(opcode)
    }

    // Generic

    fn u8(&mut self, value: u8) -> WriterResult {
        self.write_all(&[value])
    }

    fn f32(&mut self, value: f32) -> WriterResult {
        self.write_all(&value.to_le_bytes())
    }

    fn string(&mut self, string: String) -> WriterResult {
        let length = string.len().try_into().map_err(|_| SendError::Invalid)?;
        self.write_all(&[length])?;
        self.write_all(string.as_bytes())
    }

    // Wrappers

    fn metric_id(&mut self, metric_id: String) -> WriterResult {
        self.string(metric_id)
    }

    fn metric_value(&mut self, metric_value: f32) -> WriterResult {
        self.f32(metric_value)
    }

    fn range(&mut self, range: Option<DateTimeRange>) -> WriterResult {
        match range {
            Some(range) => {
                self.opcode(INCLUDES_RANGE)?;
                self.datetime(range.from)?;
                self.datetime(range.to)
            }
            None => self.opcode(DOES_NOT_INCLUDE_RANGE),
        }
    }

    fn datetime(&mut self, datetime: DateTime) -> WriterResult {
        self.string(datetime.to_rfc3339())
    }

    fn aggregation(&mut self, aggregation: AggregationOpcode) -> WriterResult {
        self.u8(aggregation as u8)
    }

    fn aggr_window(&mut self, aggr_window: Option<f32>) -> WriterResult {
        match aggr_window {
            Some(aggr_window) => {
                self.opcode(INCLUDES_AGGR_WINDOW)?;
                self.f32(aggr_window)
            }
            None => self.opcode(DOES_NOT_INCLUDE_AGGR_WINDOW),
        }
    }

    fn query_result_value(&mut self, value: Option<f32>) -> Result<(), Error> {
        match value {
            Some(value) => {
                self.writer.write_all(&[SOME])?;
                self.writer.write_all(&value.to_le_bytes())
            }
            None => self.writer.write_all(&[NONE]),
        }
    }
}
