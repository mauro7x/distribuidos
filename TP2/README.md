# TP2: Reddit Memes Analyzer

Desarrollo de un sistema distribuido que realiza análisis de posts de Reddit sobre memes `#me_irl` y sus comentarios a fin de responder ciertas consultas sobre los mismos. Los comentarios son ingestados en el sistema a medida que se recolectan, por lo que se busca procesamiento _on-line_ de los datos (arquitectura orientada a _streaming_).

- **Temas:** Middleware y Coordinación de Procesos
- [Enunciado](./docs/Enunciado.pdf)
- [Informe](./docs/Informe.pdf)

# Instrucciones de uso

Se provee de un `Makefile` para poder levantar el sistema, con sus principales comandos:

- `make build` para buildear las imágenes de docker.
  - `VERBOSE`: variable de entorno para decidir si mostrar output. _Default: false._
  - `PRETTY`: variable de entorno para colorear el output. _Default: true._
- `make apply` para aplicar la configuración (ver [Configuración](#configuración)).
  - `LOG_LEVEL`: variable de entorno para controlar el nivel de logging. Valores posibles: `debug`, `info`, `warning`, `error`, `critical`. _Default: `warning`._
- `make run` para una corrida automatizada del sistema _(up + down)_.
- `make up` para iniciar el sistema.
- `make down` para destruirlo.
- `make logs` para attachearse a los logs de todos los containers.
- `make clean` para limpiar los archivos y las imágenes generadas.

## Configuración

El sistema queda definido por los archivos de configuración de `/config`:

- Archivos modificables
  - `scale.json`: permite escalar los servicios que lo soportan.
  - `ingestion.json`: permite modificar distintos parámetros del envío de información.
  - `common.json`: permite modificar distintos parámetros comunes como el tamaño de los batches.
- **Archivo sólo lectura** `filters.json`. Definición de los distintos filtros del pipeline y cómo se comunicacn entre sí. **Advertencia:** modificar este archivo probablemente resulte en un sistema que no funciona, ya que de tal archivo depende la correcta inicialización del pipeline.

Luego de cualquier modificación será necesario correr `make apply` para generar la nueva configuración del sistema.

## Datos de entrada

Se requiere un `.csv` con posts y un `.csv` con comentarios para que el sistema funcione. Estos deben ser ingestados al mismo, configurando el filepath desde `config/ingestion.json`. Por default, está configurado en `data/posts.csv` y `data/comments.csv`.

# Problemas conocidos

Finalizado el desarrollo el proyecto, quedaron pendientes dos problemas para los que no se encontró solución:

1. **Graceful quit con Ctrl-C:** a veces algún filtro no recibe la señal de salida. La primer linea del handler es un `logging.info` y no se observa este log en el container, por lo que por alguna razón que desconozco estoy perdiendo la señal.
2. **Graceful quit mediante propagación de EOF:** de manera indeterminística observé que en algunas corridas, sucedía un fenómeno que no debería ser posible según la documentación. Cuando un proceso recibe la cantidad de EOFs necesarios para saber que los filtros superiores terminaron, propaga un EOF por el pipeline y sale. Antes de salir, cierra todos los sockets abiertos y hace un `context.term()` del contexto de pyzmq. Según la documentación de esta función, debería bloquear hasta que todos los paquetes hayan sido correctamente transferidos a la capa de red. Sin embargo se observa que no siempre es así, que en ciertas ocasiones no conocidas la función no bloquea, por lo que el container se destruye antes de que el EOF sea enviado, generando que el resto se queden esperando el EOF también.
