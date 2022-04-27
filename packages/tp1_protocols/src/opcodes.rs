pub type Opcode = u8;

// Request opcode domain: [0, 128)

pub const OP_TERMINATE: Opcode = 0;
pub const OP_EVENT: Opcode = 1;
pub const OP_QUERY: Opcode = 2;

// Response opcode domain: [128, 256)

// 2XX
pub const OP_EVENT_RECEIVED: Opcode = 128;
pub const OP_QUERY_ACCEPTED: Opcode = 129;
pub const OP_QUERY_RESPONSE: Opcode = 130;

// 4XX
pub const OP_INVALID_FORMAT: Opcode = 130;
pub const OP_INVALID_RANGE: Opcode = 131;
pub const OP_INVALID_AGGR_WINDOW: Opcode = 132;
pub const OP_METRIC_NOT_FOUND: Opcode = 133;

// 5XX
pub const OP_SERVER_AT_CAPACITY: Opcode = 134;
pub const OP_INTERNAL_SERVER_ERROR: Opcode = 135;

// More

// Query request
pub const INCLUDES_RANGE: Opcode = 0;
pub const DOES_NOT_INCLUDE_RANGE: Opcode = 1;
pub const INCLUDES_AGGR_WINDOW: Opcode = 0;
pub const DOES_NOT_INCLUDE_AGGR_WINDOW: Opcode = 1;

// Query response
pub const NONE: Opcode = 0;
pub const SOME: Opcode = 1;
pub const EOF: Opcode = 2;
