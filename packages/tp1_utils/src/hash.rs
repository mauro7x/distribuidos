use std::{
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
};

pub fn assign_worker(metric_id: &String, n_workers: usize) -> usize {
    hash(metric_id) % n_workers
}

fn hash(value: &String) -> usize {
    let mut hasher = DefaultHasher::new();
    value.hash(&mut hasher);
    hasher.finish() as usize
}
