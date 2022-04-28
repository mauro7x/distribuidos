use distribuidos_types::BoxResult;

use crate::{constants::CHECKS_FILE_PATH, types::Check};

pub fn read_checks() -> BoxResult<Vec<Check>> {
    let checks_str = std::fs::read_to_string(CHECKS_FILE_PATH)?;
    let checks: Vec<Check> = serde_json::from_str(&checks_str)?;

    Ok(checks)
}
