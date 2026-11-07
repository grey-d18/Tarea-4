---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI (2024, y sumaria 2019), une hogares y personas, construye pobreza, departamento, área y gasto real per cápita, calcula el Gini y valida contra las cifras oficiales. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza, pobreza extrema, desigualdad o Gini por departamento, área urbana/rural, Lima Metropolitana, sexo o edad, o comparar 2019 con 2024.
argument-hint: [2024 | 2019]
---
# Limpiar la ENAHO

## Pasos

1. Revisa que existan los zip en `datos/`: `966-Modulo34.zip` y `966-Modulo02.zip` (2024), `687-Modulo34.zip` (2019).
   Si faltan, **no los inventes**: pide al usuario bajarlos con los enlaces de la sección 5 del README.
2. Corre exactamente (desde la raíz del repositorio), una vez por año que haga falta:
   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio 2024
   uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio 2019
   ```
   Si no se pasa año, usa 2024.
3. Lee `salidas/validacion.txt` (2024) o `salidas/validacion_2019.txt`. Si el script terminó con «DETENIDO» o hay
   alguna línea `[FALLÓ]`, **detente**, informa qué validación falló y no presentes cifras. Nunca ajustes resultados
   para que coincidan con la referencia.
4. Responde a partir de las salidas, citando el archivo:
   - `salidas/indicadores.csv`: pobreza, pobreza extrema, Gini y gasto real per cápita por año (2019, 2024) y nivel
     (`nacional`, `area` U/R, `dominio` 8 = Lima Metropolitana, `departamento` con código `ubigeo[:2]`).
   - `salidas/hogares_<año>.parquet`: un registro por hogar; ponderar por personas con `peso_personas`
     (= `factor07 × mieperho`).
   - `salidas/personas_2024.parquet`: residentes habituales 2024; ponderar con `facpob07`. Úsala para sexo y edad.
5. Si piden algo que no está en `indicadores.csv`, calcúlalo con pandas sobre los parquet, **siempre ponderado**.
   Antes de usar una variable nueva, lee `reference.md`.

## Reglas

- Las cifras salen del script o de un cálculo ponderado sobre sus salidas, nunca de memoria.
- No presentes asociaciones como causalidad.
- Las estimaciones departamentales tienen error muestral (muestras de cientos a pocos miles de hogares):
  diferencias pequeñas entre departamentos o años deben presentarse con cautela, no como cambios seguros.
- Para comparar 2019 y 2024 usa la sumaria de ambos años (mismo método: `factor07 × mieperho`).
