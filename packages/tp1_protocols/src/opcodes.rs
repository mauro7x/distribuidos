pub type Opcode = u8;

// Request opcode domain: [0, 128)

pub const OP_TERMINATE: Opcode = 0;
pub const OP_EVENT: Opcode = 1;
// pub const OP_QUERY: Opcode = 2;

// Response opcode domain: [128, 256)

// 2XX
pub const OP_EVENT_RECEIVED: Opcode = 128;
// pub const OP_QUERY_RESPONSE: Opcode = 129;

// 4XX
pub const OP_INVALID_FORMAT: Opcode = 130;

// 5XX
pub const OP_SERVER_AT_CAPACITY: Opcode = 131;
pub const OP_INTERNAL_SERVER_ERROR: Opcode = 132;
