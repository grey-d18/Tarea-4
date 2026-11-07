---
name: graficando-enaho
description: Grafica la pobreza monetaria y la desigualdad (Gini) de la ENAHO del INEI con estimaciones ponderadas, por área urbana y rural, sexo, edad, departamento o comparando 2019 con 2024. Úsala cuando pidan un gráfico, una figura, un chart o una comparación visual de pobreza o desigualdad con la ENAHO.
argument-hint: [area | sexo | edad | departamento | comparacion | gini | cambio | todos]
---
# Graficar la ENAHO

## Pasos

1. Revisa que existan `salidas/indicadores.csv` (con los años que necesita el gráfico) y, para `sexo` o `edad`,
   `salidas/personas_2024.parquet`. **Si falta alguno, usa primero la skill `limpiando-enaho`** (2024 y, para las
   comparaciones, también 2019) y luego vuelve aquí.
2. Elige el gráfico según el pedido y córrelo desde la raíz del repositorio:

   | Pedido | Comando |
   |---|---|
   | Pobreza urbana vs. rural (2024) | `uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py area` |
   | Pobreza por sexo de la persona y del jefe(a) de hogar (2024) | `... graficar.py sexo` |
   | Pobreza por grupo de edad (2024) | `... graficar.py edad` |
   | Pobreza en los 25 departamentos (2024) | `... graficar.py departamento` |
   | Pobreza 2019 vs. 2024 (nacional, urbano, rural, Lima Metropolitana) | `... graficar.py comparacion` |
   | Gini 2019 vs. 2024 | `... graficar.py gini` |
   | Cambio de la pobreza 2019→2024 por departamento | `... graficar.py cambio` |
   | Todos | `... graficar.py todos` |

   Si se pide un argumento, usa `$ARGUMENTS`.
3. Muestra la ruta del PNG (`figuras/<nombre>.png`) y resume las cifras **leyéndolas del CSV gemelo**
   (`figuras/<nombre>.csv`); no las copies de memoria.

## Reglas que el script ya cumple (no las rompas si lo modificas)

- Estimaciones ponderadas: `facpob07` para personas; `factor07 × mieperho` para indicadores de hogares.
- Barras desde cero, ordenadas cuando no hay un orden natural, con el valor escrito en cada barra.
- Título que dice el hallazgo con cifras calculadas en el momento; subtítulo con qué, dónde, cuándo y la unidad.
- Nota al pie con la fuente (INEI, ENAHO y año) y que las cifras son ponderadas.
- Un solo color por serie; 2019 en naranja y 2024 en azul siempre. PNG a 200 dpi en `figuras/`.
- No describas diferencias como causales. Diferencias pequeñas entre grupos pueden deberse al error muestral.
