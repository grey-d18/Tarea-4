---
name: mapeando-enaho
description: Hace un mapa coroplético de la pobreza monetaria por departamento con la ENAHO del INEI y el GeoJSON departamental del Perú. Úsala cuando pidan un mapa o una comparación territorial o por departamento o región.
---
# Mapear la ENAHO

<!-- BORRADOR: completar cuando existan los scripts -->

1. Si no existe `salidas/personas_2024.parquet`, usa primero la skill `limpiando-enaho`.
2. Corre el script de mapa (en `${CLAUDE_SKILL_DIR}/scripts/`).
3. Reglas: unir `ubigeo[:2]` con `FIRST_IDDP` como texto (nunca por nombre); exigir 25 departamentos
   con dato; Lima (15) y Callao (07) separados; escala de claro a oscuro desde 0; leyenda «% de personas»;
   comparar con `referencias/pobreza_departamento_2024.csv`; guardar en `mapas/`.
