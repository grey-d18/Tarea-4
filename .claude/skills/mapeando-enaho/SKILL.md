---
name: mapeando-enaho
description: Hace un mapa coroplético de la pobreza monetaria por departamento del Perú con la ENAHO del INEI y el GeoJSON departamental, o un mapa del cambio de la pobreza entre 2019 y 2024. Úsala cuando pidan un mapa o una comparación territorial, por departamento o por región.
argument-hint: [pobreza | cambio | todos]
---
# Mapear la ENAHO

## Pasos

1. Revisa que exista `salidas/indicadores.csv` con 2024 (y 2019 para el mapa de cambio). **Si no existe o le falta
   un año, usa primero la skill `limpiando-enaho`** y luego vuelve aquí.
2. Revisa que exista `datos/peru_departamental_simple.geojson`; si falta, pide al usuario descargarlo (enlace en la
   sección 5 del README).
3. Corre desde la raíz del repositorio:
   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py pobreza   # mapas/pobreza_departamento_2024.png
   uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py cambio    # mapas/cambio_pobreza_2019_2024.png
   ```
   Si se pide un argumento, usa `$ARGUMENTS`; sin argumento, `pobreza`.
4. Lee `salidas/validacion_mapa.txt`. Si hay un `[FALLÓ]` o el script terminó con «DETENIDO», informa el problema y
   no presentes el mapa como válido.
5. Responde con la ruta del mapa y las cifras de `salidas/indicadores.csv` o
   `salidas/comparacion_mapa_referencia.csv`.

## Reglas que el script ya cumple

- Une por **código oficial**: `ubigeo[:2]` con `FIRST_IDDP`, ambos como texto. **Nunca por nombre** de departamento.
- Exige las **25 unidades** con dato; Lima (15) y Callao (07) **separados**.
- Pobreza: escala secuencial de un solo tono (claro → oscuro) desde 0; leyenda «% de personas en pobreza».
- Cambio: escala divergente azul (bajó) ↔ rojo (subió), en puntos porcentuales.
- Compara la pobreza 2024 con `referencias/pobreza_departamento_2024.csv` (Sesión 16), con tolerancia de 0.1 pp.
- Los cambios departamentales pequeños pueden deberse al error muestral; no los presentes como causales.
