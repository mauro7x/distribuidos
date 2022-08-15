# Sistemas Distribuidos I

Trabajo práctico integrador de la materia [**Sistemas Distribuidos I** (75.74)](https://campus.fi.uba.ar/course/view.php?id=2008), realizado en el primer cuatrimestre del año 2022, dictada en la Facultad de Ingeniería, Universidad de Buenos Aires.

## Integrantes

| Nombre   | Apellido | Padrón | Mail                | GitHub                                    |
| -------- | -------- | ------ | ------------------- | ----------------------------------------- |
| Mauro    | Parafati | 102749 | mparafati@fi.uba.ar | [mauro7x](https://github.com/mauro7x)     |
| Nicolás  | Aguerre  | 102145 | naguerre@fi.uba.ar  | [nicomatex](https://github.com/nicomatex) |
| Santiago | Klein    | 102192 | sklein@fi.uba.ar    | [sankle](https://github.com/sankle)       |

## Instrucciones de uso

1. Descargar los sets de datos desde [kaggle](https://www.kaggle.com/datasets/pavellexyr/the-reddit-irl-dataset) y moverlos al directorio `/data`. **Importante:** los nombres de los archivos deben ser `posts.csv` y `comments.csv`. Para más información sobre el formato esperado de los `csv`, [ver este documento](./data/README.md).
2. (Opcional) Modificar el archivo `/config/scale.json` a gusto para definir la cantidad de replicas de cada servicio, o `/config/monitor.json` si se desea modificar la cantidad de replicas pasivas del monitor.
3. Iniciar el sistema con `make run`. Este comando va a construir las imagenes, crear y poner a correr a todos los containers, _attachearse_ a los logs, para finalmente, al recibir `Ctrl + C`, terminar la ejecución y destruir los recursos de forma ordenada.
4. Los resultados pueden encontrarse en el directorio `/results`.

### Más comandos

Si bien con `make run` puede correrse el sistema, también se proveen distintos comandos de `make` para llevar a cabo tareas individuales en caso de que así se desee:

- `make build` para buildear las imágenes de docker.
  - `VERBOSE`: variable de entorno para decidir si mostrar output. _Default: false._
  - `PRETTY`: variable de entorno para colorear el output. _Default: true._
- `make up` para iniciar el sistema.
- `make down` para destruirlo.
- `make logs` para attachearse a los logs de todos los containers.


## Documentación

- [Enunciado](docs/Enunciado.pdf)
- [Informe](docs/Informe.pdf)
