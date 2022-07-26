# MOM

-   **Comunicación de grupo** de forma transparente.
-   Comunicar mensajes entre apps.
-   **Transparencia** respecto de: ubicación, fallos, performance y escalabilidad.

## Variantes

-   **Centralizado** (Broker) vs. **Distribuido** (Brokerless).
-   **BUS** vs. Message **Queues**.
-   **Sincrónico:** modelado como conexión punto a punto.
    -   No hay transparencia frente a errores.
-   **Asincrónico:** modelado con colas.
    -   Soporta períodos de discontinuidad del transporte.
    -   Complejo recibir respuestas.

## Operaciones comunes

-   `put`: publicar mensaje.
-   `get`: esperar por un mensaje, sacarlo de la cola y retornarlo.
-   `poll`: revisar mensajes sin bloquear.
-   `notify`: asociar un callback para ser ejecutado por el MOM frente a ciertos msjs.

## Brokers

-   Proveen **transparencia de localización**.
-   **Filtering, Routing.**
-   Punto de control y monitoreo.

## Ejemplos

### ZeroMQ

-   **Patrones:** Req-Rep, Pub-Sub, Pipeline (PUSH-PULL), Router-Dealer.
-   **Conexiones:** TCP, IPC, Inproc (multithreading).

### RabbitMQ

-   **Queues.**
    -   Nombradas vs. TaskQueues vs. **Anónimas**.
    -   ACK.
    -   Durabilidad opcional.
-   **Exchanges.**
    -   Estrategias para transmitir mensajes (`fanout`, `direct`, `topic`, `headers`).
-   **Patrones:** Pub-Sub, Routing, **Topics**.
