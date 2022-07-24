# Arquitecturas orientadas a Servicio

## Monolíticas

`-Request-> ReverseProxy (<-> Static Files) -> WebServer -Query-> DBServer`

### Escalables

-   Web Requests: **+Web Servers**.
    -   (+) Routeo y Escalabilidad
    -   (-) SPOF.
-   Data Queries: **+DB Servers**.
    -   (+) Throughput lectura.
    -   (-) Throughput escritura.

## Service Oriented (SOA)

-   **Paradigma** orientado al **ámbito corporativo**.
-   **Business Process Management (BPM).** Disciplina involucrando modelado, automatización, ejecución, control, métricas y optimización de los flujos de negocio p/ objetivos de empresa.

### Características

-   **Tecnologías:**
    -   Web Services (SOAP + HTTP).
    -   **Enterprise Service Bus** para **eventos**.
    -   Service **Repository** & **Discovery**.
        -   Comunicación punto a punto.
-   **Servicios y Procesos:**
    -   Interfaces.
    -   Contratos.
    -   Implementación: business logic + data management.

## Microservicios

-   +Granularidad.
-   Escalabilidad Horizontal.
-   Flexibilidad de Negocio.
-   Monitoreo y Disponibilidad parcial.

## Serverless

# Cloud

-   Todo lo que se puede consumir más allá del firewall.
-   `Networking + Infra + Nuevas plataformas + Servicios`

## Niveles de abstracción

-   **IaaS.**
    -   Almacenamiento y **virtualización de equipos**.
    -   Definir redes y adaptación frente a carga.
    -   **Customer Managed:** Apps, Security, Databases, OS.
    -   _Ej. Google Cloud Storage._
-   **PaaS.**
    -   Frameworks y plataformas p/ desarrollar aplicaciones _Cloud Ready_.
    -   Recursos expuestos como **servicios p/ desarrollo** y **manejo de ciclo de vida** (logs,monitoreo).
    -   **Customer Managed:** Apps.
    -   _Ej. Google App Engine._
-   **SaaS.**
    -   Alquiler de servicios, **software a demanda**.
    -   Soluciones **genéricas** y **adaptables**.
    -   Arquitecturas pensadas p/ **integración**.
    -   **Customer Managed:** NADA.
    -   _Ej. Google Apps._

## Beneficios

-   **Accesibilidad.** Movilidad y visibilidad constante.
-   **Time-to-Market.** Recursos instantaneos.
-   **Escalabilidad.** Capacidad _ilimitada_ de recursos.
-   **Costos.** Pay-as-you-go. Controles de gasto.

## Resistencia al cambio

-   Factores **políticos**:
    -   Locación y jurisdicción de datos,
    -   Incapacidad de influir sobre decisiones de HW.
-   Factores **técnicos**:
    -   Costos p/ migraciones,
    -   Exposición de datos sensibles,

# PaaS
