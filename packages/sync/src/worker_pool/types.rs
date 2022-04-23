use std::sync::{mpsc, Arc, Mutex};

pub enum Message<T>
where
    T: Send,
{
    NewJob(T),
    Terminate,
}

#[derive(Debug)]
pub enum ExecuteError {
    Full,
}

pub type MessageSender<T> = mpsc::SyncSender<Message<T>>;
pub type MessageReceiver<T> = mpsc::Receiver<Message<T>>;
pub type SharedMessageReceiver<T> = Arc<Mutex<MessageReceiver<T>>>;
