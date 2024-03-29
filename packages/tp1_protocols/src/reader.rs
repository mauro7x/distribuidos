use chrono::Utc;

use crate::{
    constants::*,
    opcodes::*,
    types::{
        errors::{QueryError, RecvError},
        AggregationOpcode, DateTime, DateTimeRange, Event, Query, QueryResult,
    },
};
use std::{
    io::{BufReader, Read},
    mem::size_of,
    net::TcpStream,
};

type TcpReader<'a> = BufReader<&'a TcpStream>;
type ReaderResult<T> = Result<T, RecvError>;

pub struct Reader<'a> {
    reader: TcpReader<'a>,
}

impl Reader<'_> {
    pub fn new(stream: &TcpStream) -> Reader {
        Reader {
            reader: TcpReader::new(stream),
        }
    }

    fn read_exact(&mut self, buf: &mut [u8]) -> ReaderResult<()> {
        self.reader.read_exact(buf)?;
        Ok(())
    }

    // API

    pub fn query(&mut self) -> ReaderResult<Query> {
        self.particular_opcode(OP_QUERY)?;
        let metric_id = self.metric_id()?;
        let range = self.range()?;
        let aggregation = self.aggregation()?;
        let aggregation_window_secs = self.aggr_window()?;

        let query = Query {
            metric_id,
            range,
            aggregation,
            aggregation_window_secs,
        };

        Ok(query)
    }

    pub fn event(&mut self) -> ReaderResult<Event> {
        self.particular_opcode(OP_EVENT)?;
        let metric_id = self.metric_id()?;
        let value = self.metric_value()?;

        let event = Event { metric_id, value };

        Ok(event)
    }

    pub fn query_result(&mut self) -> Result<QueryResult, QueryError> {
        let mut opcode_buf = [0u8; 1];
        self.reader.read_exact(&mut opcode_buf)?;

        match opcode_buf[0] {
            OP_QUERY_RESPONSE => self.query_result_values(),
            OP_INVALID_FORMAT => Err(QueryError::Invalid),
            OP_SERVER_AT_CAPACITY => Err(QueryError::ServerAtCapacity),
            OP_INTERNAL_SERVER_ERROR => Err(QueryError::InternalServerError),
            OP_METRIC_NOT_FOUND => Err(QueryError::MetricNotFound),
            OP_INVALID_RANGE => Err(QueryError::InvalidRange),
            OP_INVALID_AGGR_WINDOW => Err(QueryError::InvalidAggrWindow),
            op => panic!("Received unexpected opcode: {:?}", op),
        }
    }

    pub fn opcode(&mut self) -> ReaderResult<Opcode> {
        self.u8()
    }

    // Static

    fn _read_n<R>(reader: &mut R, bytes_to_read: usize) -> Result<Vec<u8>, std::io::Error>
    where
        R: Read,
    {
        let mut buf = Vec::with_capacity(bytes_to_read);
        let mut chunk = reader.take(bytes_to_read.try_into().unwrap());
        let n = chunk.read_to_end(&mut buf)?;
        assert_eq!(bytes_to_read as usize, n);

        Ok(buf)
    }

    // Generic

    fn read_n(&mut self, bytes_to_read: usize) -> ReaderResult<Vec<u8>> {
        Ok(Reader::_read_n(&mut self.reader, bytes_to_read)?)
    }

    fn u8(&mut self) -> ReaderResult<u8> {
        let mut buf = [0; 1];
        self.read_exact(&mut buf)?;

        Ok(buf[0])
    }

    fn f32(&mut self) -> ReaderResult<f32> {
        let mut value_buf = [0; size_of::<f32>()];
        self.read_exact(&mut value_buf)?;

        Ok(f32::from_le_bytes(value_buf))
    }

    fn string(&mut self, max_length: Option<u8>) -> ReaderResult<String> {
        let length = self.u8()?;
        if length == 0 {
            return Err(RecvError::Invalid);
        }

        if let Some(max_length) = max_length {
            if length > max_length {
                return Err(RecvError::Invalid);
            }
        }

        let buf = self.read_n(length.into())?;

        match std::str::from_utf8(&buf) {
            Ok(parsed_str) => Ok(parsed_str.to_string()),
            Err(_) => Err(RecvError::Invalid),
        }
    }

    // Wrappers

    fn particular_opcode(&mut self, expected: Opcode) -> ReaderResult<()> {
        match self.opcode()? {
            opcode if opcode == expected => Ok(()),
            OP_TERMINATE => Err(RecvError::Terminated),
            _ => Err(RecvError::Invalid),
        }
    }

    fn metric_id(&mut self) -> ReaderResult<String> {
        self.string(Some(MAX_EVENT_ID_LENGTH))
    }

    fn metric_value(&mut self) -> ReaderResult<f32> {
        self.f32()
    }

    fn range(&mut self) -> ReaderResult<Option<DateTimeRange>> {
        match self.opcode()? {
            INCLUDES_RANGE => {
                let from = self.datetime()?;
                let to = self.datetime()?;
                let range = DateTimeRange { from, to };

                Ok(Some(range))
            }
            DOES_NOT_INCLUDE_RANGE => Ok(None),
            _ => Err(RecvError::Invalid),
        }
    }

    fn datetime(&mut self) -> ReaderResult<DateTime> {
        let date_string = self.string(None)?;
        let date = chrono::DateTime::parse_from_rfc3339(&date_string)
            .map_err(|_| RecvError::Invalid)?
            .with_timezone(&Utc);

        Ok(date)
    }

    fn aggregation(&mut self) -> ReaderResult<AggregationOpcode> {
        match self.u8()? {
            0 => Ok(AggregationOpcode::AVG),
            1 => Ok(AggregationOpcode::MIN),
            2 => Ok(AggregationOpcode::MAX),
            3 => Ok(AggregationOpcode::COUNT),
            _ => Err(RecvError::Invalid),
        }
    }

    fn aggr_window(&mut self) -> ReaderResult<Option<f32>> {
        match self.opcode()? {
            INCLUDES_AGGR_WINDOW => Ok(Some(self.f32()?)),
            DOES_NOT_INCLUDE_AGGR_WINDOW => Ok(None),
            _ => Err(RecvError::Invalid),
        }
    }

    fn query_result_values(&mut self) -> Result<QueryResult, QueryError> {
        let mut result = vec![];
        let mut opcode_buf = [0u8; 1];
        let mut value_buf = [0u8; size_of::<f32>()];

        loop {
            self.reader.read_exact(&mut opcode_buf)?;
            match opcode_buf[0] {
                SOME => {
                    self.reader.read_exact(&mut value_buf)?;
                    let value = f32::from_le_bytes(value_buf);
                    result.push(Some(value))
                }
                NONE => result.push(None),
                EOF => break,
                _ => return Err(QueryError::InternalServerError),
            }
        }

        Ok(result)
    }
}
