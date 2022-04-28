pub fn filepath(dirpath: &str, partition: i64, ro: bool) -> String {
    let suffix = match ro {
        true => "",
        false => ".w",
    };

    format!("{}/{}.csv{}", &dirpath, partition, suffix)
}

pub fn dirpath(metric_id: &str, database_path: &str) -> String {
    format!("{}/{}", database_path, metric_id)
}
