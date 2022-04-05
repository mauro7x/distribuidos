FROM rust:1.59
WORKDIR /usr/app

# Weird hacky mechanism for avoiding re-build dependencies everytime
# (Idea from: https://stackoverflow.com/questions/58473606/cache-rust-dependencies-with-docker-build)
COPY Cargo.toml .
RUN echo "fn main() {}" > dummy.rs && \
  sed -i 's#src/main.rs#dummy.rs#' Cargo.toml && \
  cargo build --release && \
  rm dummy.rs

COPY . .
RUN cargo build --release
ENTRYPOINT ["/bin/sh"]
