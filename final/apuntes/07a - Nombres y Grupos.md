# Nombres y direccionamiento

## Nombres

-   **Identifican** unívocamente a una entidad.
-   **Describen** a la entidad.
-   **Abstraen** al recurso de propiedades que lo atan al sistema.

## Direccionamiento (Addressing)

-   **Mapeo** entre nombre y dirección.
-   Dirección cambia, nombre NO.
-   Dirección puede ser reutilizada.
-   Ejemplos:
    -   `IP -> Ethernet Address`. ARP (IPv4) y ND (IPv6).
    -   `Domain Name -> IP`. DNS.
    -   `Service -> Instances`. Service Discovery.

# Mensajes

## Formateo de paquetes

### Binario

-   **Alta performance:** tamaño eficiente, compresión _innecesaria_.
-   **Serialización:** autogeneración, no siempre existe soporte.
-   **Interacción:**
    -   Acoplamiento.
    -   Cliente específico p/ c/ app.
    -   Decoder p/ interpretar.

### Texto plano

-   **Baja performance:** bajo throughput, compresión -> overhead.
-   **Serialización:** básica, formatos human-readable.
-   **Interacción:** cliente único, fácil de debuggear.

## Longitud de paquetes

-   Pueden ser:
    -   **Bloques fijos.**
        -   Fácil de serializar.
        -   Subóptimo p/ datos de long. variable.
    -   **Bloques dinámicos.** Agrega:
        -   Separador p/ delimitar comienzo y terminación.
        -   Longitud del tipo p/ delimitar campos.
        -   Overhead.
    -   **Esquema mixto** (fijos sin delimitadores, variables con).
-   Formato: `Type-Length-Value`.

# Grupos

-   Abstracción p/ **colección de procesos**.
-   **Dinámicos**.
-   Procesos pueden suscribir y cancelar suscripción a grupos.
    -   Primitivas.

## Difusión de mensajes

-   **Uno a uno:**
    -   **Unicast.** Punto a punto.
    -   **Anycast.** Uno sólo recibe el mensaje (ej. el más cercano).
-   **Uno a muchos:**
    -   **Multicast.** Los de un determinado grupo reciben el mensaje.
    -   **Broadcast.** Todos.

## Atomicidad

-   Deben entregarse a todos o a ninguno.
-   Necesidad de **ACKs**.
-   Necesidad de **demorar delivery** de paquetes recibidos.
-   **Reintentos** frente a caídas/no recepción.
