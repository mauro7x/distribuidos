pub fn filepath(dirpath: &String, partition: i64, ro: bool) -> String {
    let suffix = match ro {
        true => "",
        false => ".w",
    };

    format!("{}/{}.csv{}", &dirpath, partition, suffix)
}

pub fn dirpath(metric_id: &String, database_path: &String) -> String {
    format!("{}/{}", database_path, metric_id)
}
