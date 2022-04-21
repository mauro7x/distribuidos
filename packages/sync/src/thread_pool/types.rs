use super::traits::FnBox;
use std::sync::{mpsc, Arc, Mutex};

pub enum Message {
    NewJob(Job),
    Terminate,
}

pub type Job = Box<dyn FnBox + Send + 'static>;

pub type MessageSender = mpsc::Sender<Message>;
pub type MessageReceiver = mpsc::Receiver<Message>;
pub type SharedMessageReceiver = Arc<Mutex<MessageReceiver>>;
