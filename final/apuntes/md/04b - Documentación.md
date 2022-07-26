# Documentación

La **arquitectura** representa aquellas **decisiones de importancia** s/ el **costo de modificarlas**.

## Características deseadas

Diseño y documentación:

-   **Evolutivo:**
    -   Rápida adaptación.
    -   Tomar feedback.
    -   Valor iterativo.
    -   No buscar entender todo.
    -   No demorar arquitectura.
-   Necesario para **coordinación**, **coherencia** y **cohesión**.
    -   Diseño preliminar.

## Modelos de Documentación

### Vistas 4 + 1

-   **Vista Lógica:**
    -   Estructura y funcionalidad del sistema -> Clases, Estados.
-   **Vista de Procesos (o Dinámica):**
    -   Descripción de escenarios concurrentes (Actividades).
    -   Flujo de mensajes (Colaboración).
    -   Flujo temporal de mensajes (Secuencia).
-   **Vista de Desarrollo (o de Implementación):**
    -   Artefactos que componen al sistema (Componentes, Paquetes).
-   **Vista Física (o de Despliegue):**
    -   Topología y Conexiones entre componentes físicos (Despliegue).
    -   Arquitectura del sistema (Robustez).
-   **Escenarios:** Casos de Uso.

### C4 Model

1. Contexto.
2. Container.
3. Componente.
4. Código.
