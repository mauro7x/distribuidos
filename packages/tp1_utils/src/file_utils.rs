use chrono::{Date, DateTime, Datelike, Timelike, Utc};

pub fn dirpath(date: &Date<Utc>, database_path: &String, metric_id: &String) -> String {
    format!(
        "{}/{}/{:0>4}{:0>2}{:0>2}",
        database_path,
        metric_id,
        date.year(),
        date.month(),
        date.day()
    )
}

pub fn filepath(dirpath: &String, partition_number: u32, ro: bool) -> String {
    let suffix = match ro {
        true => "",
        false => ".w",
    };

    format!("{}/{}.csv{}", &dirpath, partition_number, suffix)
}

pub fn abs_partition_number(datetime: &DateTime<Utc>, partition_secs: u32) -> i64 {
    let secs = datetime.timestamp();
    secs / i64::from(partition_secs)
}

pub fn partition_number(datetime: &DateTime<Utc>, partition_secs: u32) -> u32 {
    let secs = datetime.num_seconds_from_midnight();
    secs / partition_secs
}
