---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI, une hogares y personas, construye pobreza, departamento y área, y valida contra las cifras oficiales. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza, desigualdad o Gini por departamento, área, sexo o edad.
argument-hint: [año]
---
# Limpiar la ENAHO

<!-- BORRADOR: completar cuando exista scripts/limpiar.py -->

1. Si faltan los zip en `datos/`, pide al usuario bajarlos del INEI (código 966 = 2024; 687 = 2019).
2. Corre exactamente: `uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio $0`
3. Lee `salidas/validacion_$0.txt`. Si alguna validación esencial falló, detente y explica cuál.
4. Responde con `salidas/personas_$0.parquet`; toda cifra va ponderada con `facpob07`.
5. Antes de usar una variable que no está en la base, lee `reference.md`.
