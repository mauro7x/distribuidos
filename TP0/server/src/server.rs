pub struct Server {}

impl Server {
    pub fn new() -> Self {
        Server {}
    }

    pub fn say_hi(&self) {
        println!("Hello World from Server!");
    }
}
