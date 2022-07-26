# Middlewares

**Capa de software entre el SO y la capa de aplicación/usuario para proveer una vista única del sistema.**

## Definiciones

-   Software de conectividad.
-   Ofrece conjunto de servicios.
-   Permite operar sobre plataformas heterogeneas.
-   Módulo intermedio como conductor entre sistemas.
-   Capa de software entre SO y aplicaciones de sistema.
-   Permite que múltiples procesos interactúen de un lado a otro (de la red).

## Objetivos

-   **Transparencia** (respecto de acceso, ubicación, migración, replicación, concurrencia, fallos, persistencia).
-   **Tolerancia a Fallos** (availability, reliability, safety, maintainability).
-   **Acceso a recursos compartidos** (eficiente, transparente y controlado).
-   **Sistemas distribuidos abiertos (Interfaces).**
    -   Estándares claros sobre servicios ofrecidos.
    -   Interoperabilidad y portabilidad.
-   **Comunicación de grupos.**
    -   Broadcasting y multicasting.
    -   Facilita localización de elementos y coordinación de tareas.

## Clasificación

-   **Transactional Procedure.** Transaccionalidad respecto a datos.
    -   Conectan muchas fuentes de datos.
    -   Acceso transparente al grupo.
    -   Políticas de retries y tolerancia a fallos.
-   **Procedure Oriented.** Servidor de funciones que se pueden invocar.
    -   Servicios stateless entre invocaciones (idempotencia).
-   **Object Oriented.** Servidor de objetos distribuidos.
    -   Marshalling p/ transmitir info.
-   **Message Oriented.** Sistema de mensajería.
    -   Modo **Information Bus**: tópicos.
    -   Modo **Queue**: destinatario definido.
-   Reflective Middlewares (config. dinámica).
