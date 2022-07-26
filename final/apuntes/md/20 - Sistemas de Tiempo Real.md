# Sistemas de Tiempo Real

-   Sistemas cuya evolución se específica en términos de **requerimientos temporales** requeridos por el entorno.
    -   Lo importante es que se indica el paso a paso.
    -   Cual es el tiempo definido para ejecutar cada paso.
-   **Correctitud** del sistema = **respuestas correctas** en **tiempo correcto**.
-   Ejemplos: electrodomésticos digitales, medidores de señales, mediciones por sensores, control de automóviles, control en aeronaves, marcapasos, etc.
-   Sistema **previsible**, NO performante.
    -   Sobre temporalidad.
    -   Correcto **scheduling**.

## Tipos

-   **Hard RT:** se debe evitar todo fallo relacionado con el tiempo de delivery.
    -   Perder un deadline es fallo total.
-   **Soft RT:** pueden ser admitidos ocasionalmente / nivel de tolerancia.
    -   Utilidad de resultado disminuye tras deadline.

## Comunicación

-   Requiere comunicación **fiable** y **sincrónica**.
    -   **Deadlines** definidos.
    -   TCP no cumple. No hay garantías de tiempo.
-   Comunicación Serial: **Profibus**.
-   Utilizar **Ethernet**: rediseñar protocolo de capas superiores.
    -   **Profinet**.

## Fault Tolerance

-   **Previsibilidad.** Todo tiene que estar escrito y bien definido.
-   En hard RT, **hard resets**.
    -   Muy importante revisar **maintainability**: recuperarse de forma barata, rápida y consistente.

## Paradigmas de Trabajo

-   **Event-Triggered.**
    -   El cliente lo espera de forma **bloqueante**.
    -   El cliente debe poder controlar tiempos de inactividad.
-   **Time-Triggered.**
    -   Definición de **time slots**.
    -   En c/ time slot se pueden emitir eventos.
    -   Cuándo tengo respuesta?

# Sistemas de Control

Escenarios donde un sistema intenta **controlar** de forma manual o automática alguna **realidad del medio físico**.

-   **Compatibilidad** entre especificaciones.
-   No todo sistema RT es de control.
-   Ejemplos.
    -   En la industria: procesos químicos, líneas de producción, etc.
    -   En la vida: termostatos, ascensores, control de luminosidad, etc.

## Nociones

-   **Control.** Capacidad de actuar para mover cosas y buscar que algo pase.
-   **Proceso.** Sucesión de cosas que quiero controlar.
-   **Variable controlada.** Valor/cantidad que mido/controlo. **Salida del sistema.**
-   **Variable manipulada.** Cantidad/condicion que modifico para afectar el valor de la controlada.
-   **Perturbación.** Señal que afecta negativamente al valor de la salida del sistema.
-   **Planta.** Sistema físico sobre el cual se trabaja.
-   **Controlador (referencia).** Sistema encargado de determinar qué hay que hacer.
-   **Actuador.** Sensores físicos.

## Ciclos

-   **Lazo Abierto.** Manual, no automatizado.
    -   No hay feedback.
    -   No hay retroalimentación.
    -   No considera lo que pasa en la realidad.
-   **Lazo Cerrado.** Realimentado, feedback.
    -   Medir error entre lo que quería hacer y lo que obtuve.

## Programación

-   Arquitecturas dirigidas por eventos o por tiempo.
-   Scheduling importante.
    -   Non-preemptive, esquema de prioridades => garantizar deadlines.
-   Protocolos de comunicación específicos.
