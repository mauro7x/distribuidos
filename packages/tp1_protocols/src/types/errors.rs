use super::Event;

#[derive(Debug)]
pub enum RecvError {
    Terminated,
    Invalid,
}
pub type RecvResult = Result<Event, RecvError>;

#[derive(Debug)]
pub enum SendError {
    Invalid,
    ServerAtCapacity,
    InternalServerError,
}
pub type SendResult = Result<(), SendError>;
