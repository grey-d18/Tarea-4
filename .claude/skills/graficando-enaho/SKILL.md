---
name: graficando-enaho
description: Grafica la pobreza monetaria de la ENAHO del INEI con estimaciones ponderadas, por área urbana y rural, sexo, edad o departamento. Úsala cuando pidan un gráfico, una figura o una comparación visual de pobreza o desigualdad con la ENAHO.
argument-hint: [area | sexo | edad | departamento]
---
# Graficar la ENAHO

<!-- BORRADOR: completar cuando existan los scripts -->

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Corre el script que corresponda al pedido (en `${CLAUDE_SKILL_DIR}/scripts/`).
3. Reglas: ponderar con `facpob07`; barras desde cero y ordenadas; valor escrito en cada barra;
   título que diga qué y cuándo; nota «Fuente: INEI, ENAHO 2024»; PNG a 200 dpi en `figuras/`.
