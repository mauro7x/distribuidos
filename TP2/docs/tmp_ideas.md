# Temporal ideas

## Documentation

- Multiple views of DAG diagram, showing filters with different colors by:
  - CPU usage.
  - RAM usage.
  - Traffic:
    - Bytes received.
    - Bytes sent.
- Use this as an argument to talk about optimization, and multi-computing architecture decisions.
  - e.g.: as "Body parser" involves high CPU usage, it should be easy to scale...

## Implementation

- Middleware:
  - Generic, using a .json for **defining** our system.
  - Particular, using specific middlewares for each node.
- MOM:
  - Define interfaces first, without thinking in MOM.
  - Start with the simplest (RabbitMQ?).
  - If its possible, abstract it as much as possible to allow changing between Rabbit and ZMQ, to perform tests with both implementations.
