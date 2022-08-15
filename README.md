# Sistemas Distribuidos I

Trabajos prácticos de la materia [**Sistemas Distribuidos I** (75.74)](https://campus.fi.uba.ar/course/view.php?id=2008) realizados en el primer cuatrimestre del año 2022, dictada en la Facultad de Ingeniería, Universidad de Buenos Aires.

## Índice

-   [TP0: Docker, Docker Compose](./TP0)
-   [TP1: Concurrencia y Comunicaciones](./TP1)
-   [TP2: Middleware y Coordinación de Procesos](./TP2)
-   [TP3: Tolerancia a Fallos](./TP3) _(trabajo grupal)_

## Alumno

-   Nombre: **Mauro Parafati**
-   Padrón: **102749**
-   Contacto: **mparafati** at **fi.uba.ar**

<details><summary><h2>¿Por qué un monorepo?</h2></summary>

Desde hace no mucho suelo tomar la decisión de organizar los trabajos de las distintas materias que curso en un sólo repositorio en lugar de utilizar un repositorio por cada proyecto.

¿Por qué? Las **ventajas** que encuentro en la práctica son varias: (lista no exhaustiva)

-   **Configurar el repositorio una única vez** (workflows, templates, labels, milestones).
-   **Tener todo en un mismo lugar.** Con un `git clone` me puedo poner a desarrollar código de la materia en cualquier lugar sin necesidad de andar buscando en otros repositorios
-   Compartir configuraciones **propias del lenguaje** de programación utilizado, como podrían ser librerías en común (loggers, por dar un ejemplo) o flujos automáticos de linting o testing.
-   Y por último, aprender buenas prácticas de Git, que se hace indispensable para mantener el repositorio organizado ante la adición de nuevos trabajos.

Como desventaja principal _(y diría única real)_ es que para trabajar sobre un trabajo en particular (o corregirlo) hay que clonar el repositorio entero, incluyendo el resto de trabajos. Pero sabiendo que se trata de un codebase didáctico y su tamaño nunca será comparable a uno productivo como para que esto pueda llegar a ser molesto, considero que las ventajas superan ampliamente este punto negativo.

</details>

## Pre-commit hooks (Outdated)

Para facilitar la integración continua, se habilitó un pre-commit hook, que puede ser instalado con el script proporcionado (`./install_hooks.sh`) para que justamente corra antes de cada commit. Este hook se asegurará de que el formato siga los estándares esperados, así como de chequear si existen warnings en tiempo de compilación.

**Actualización:** este hook se encuentra deshabilitado ya que fue pensado para los proyectos Rust (TP0 y TP1) pero no para los hechos en Python (TP2 y TP3).

## Links de interés

-   [Página de cátedra](https://campus.fi.uba.ar/course/view.php?id=2008)
-   [Aula virtual](https://campus.fi.uba.ar/course/view.php?id=761)
