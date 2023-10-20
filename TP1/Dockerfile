# Shared Dockerfile for all services

FROM rust:1.73
WORKDIR /usr/app

# Weird hacky mechanism for avoiding re-build dependencies everytime
# (Idea from: https://stackoverflow.com/questions/58473606/cache-rust-dependencies-with-docker-build)
COPY Cargo.toml .
RUN mkdir -p src/bin && \
  echo "fn main() {}" > src/bin/dummy.rs && \
  cargo build --release --bin dummy && \
  rm -rf src

COPY . .
RUN cargo build --release
ENTRYPOINT ["/bin/sh"]
