#[macro_export]
macro_rules! not_reachable {
    ($($arg:tt)*) => {
      use log::error;
      {
        let msg = format!($($arg)*);
        error!("{}", msg);
        panic!("{}", msg);
      }
    };
}
