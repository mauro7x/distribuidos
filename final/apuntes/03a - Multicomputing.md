# Multicomputing

## Muchos procesadores

-   **Comparten** mediante BUS:
    -   Network Interface Controller.
    -   Main Memory.
    -   Disk Controller.
    -   GPU (Memory).
-   **Taxonomía de Flynn:**
    -   SISD: Single Instruction Single Data.
    -   SIMD: Array processors.
    -   MISD: No son usuales.
    -   **MIMD.**

## MIMD

### Multiprocessors

-   CPUs **comparten** memoria y/o clocks.
-   **Simétrico vs. Asimétrico** (distintos niveles, conectados por _bridges_).
-   **Memory Access:**
    -   **Uniform** (UMA, non-NUMA): tiempo identico p/ todos.
    -   **Non Uniform** (NUMA): c/ CPU controla un bloque de memoria y se transforma en su _'Home Agent'_.

### Multicomputers

-   No comparten nada.
-   Fallos **independientes**.
-   **No hay reloj central** de ejecución de instrucciones.
-   **Requieren comunicación** por networking.
-   Sincronización mediante mensajes ad-hoc.
-   Características:
    -   Problemas de comunicación por red _(ancho de banda, latencia, pérdida de mensajes)_.
    -   **Comunicación** es compleja y central al diseño del sistema.
    -   Alta escalabilidad.
    -   Tolerantes a fallos.
