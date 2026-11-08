# Evidencias de la evaluación (Parte 4)

Las 20 sesiones de Claude Code de la evaluación (10 preguntas × modos A y B, Sonnet, 7 de noviembre de 2026) se
guardaron automáticamente con `evaluacion/evaluar.py`. Están en [`evaluacion/registros/`](../../evaluacion/registros/)
como JSON línea por línea (`stream-json` de `claude -p`):

- `registros/A/<id>.jsonl`: modo A, sin MCP, Skills ni herramientas.
- `registros/B/<id>.jsonl`: modo B, con el servidor MCP `bcrp` y las Skills.

Cada archivo contiene la configuración de la sesión (herramientas y servidores MCP disponibles), cada llamada a
herramientas con su resultado y la respuesta final. En las rutas se reemplazó el nombre de usuario.

El resumen está en [`evaluacion/resultados.csv`](../../evaluacion/resultados.csv) y el análisis en
[`evaluacion/comparacion.md`](../../evaluacion/comparacion.md).
