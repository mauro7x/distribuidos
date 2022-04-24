use std::io::{Error, Read};

pub fn read_n<R>(reader: &mut R, bytes_to_read: usize) -> Result<Vec<u8>, Error>
where
    R: Read,
{
    let mut buf = Vec::with_capacity(bytes_to_read);
    let mut chunk = reader.take(bytes_to_read.try_into().unwrap());
    let n = chunk.read_to_end(&mut buf)?;
    assert_eq!(bytes_to_read as usize, n);

    Ok(buf)
}
