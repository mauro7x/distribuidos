# Alta Disponibilidad

-   **SLA (Agreement):** disponibilidad pactada con cliente.
    -   Define qué sucede si no se cumple.
-   **SLO (Objectives):** lo que se debe cumplir para no invalidar SLA.
    -   Ej: availability > 99.95%
-   **SLI (Indicators):** métricas a comparar con SLOs.
    -   Plataforma de **observability**.
    -   Analizar **impacto del despliegue**.

## CAP

-   **Consistency.** Repetibilidad de respuesta de todos los nodos frente a mismo pedido.
-   **Availability.** Responder a todo.
-   **Partition Tolerance.** Lidiar con formación de grupos aislados de nodos.
