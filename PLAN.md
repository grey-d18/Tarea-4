# Plan de trabajo – Tarea 4

**Pregunta:** ¿La recuperación del PBI peruano entre 2019 y 2024 se reflejó en una menor pobreza monetaria y
desigualdad en los departamentos del país?

**Entrega:** domingo 8 de noviembre de 2026, 11:59 p. m. (Perú), como comentario en
https://github.com/d2cml-ai/Data-Science-Python/issues/201

---

## Paso 1 – Estructura ✅
- [x] Carpetas, `pyproject.toml`, `.gitignore`, `.mcp.json`
- [x] `mcp/server.py` (plantilla de la sesión 04) y `mcp/test_server.py` (8 pruebas originales, **sin modificar**)
- [x] Borradores de los tres `SKILL.md` y `reference.md`
- [x] `referencias/pobreza_departamento_2024.csv` (de la sesión 16)

## Paso 2 – Datos ✅
- [x] Descargar a `datos/`: `966-Modulo34.zip`, `966-Modulo02.zip`, `687-Modulo34.zip` (687 = 2019, confirmado: contiene `sumaria-2019.dta`)
- [x] Descargar el GeoJSON departamental a `datos/`
- [x] Variables confirmadas: sumaria 2024 (33,691 hogares) y 2019 (34,565) traen `gashog2d`, `inghog2d`, `ld`, `linea`, `factor07`; módulo 02 (117,721 personas) trae `p203`–`p208a` y `facpob07`. Llaves llegan como texto con ceros.
- [x] Chequeo rápido (aún no es la Skill): pobreza ponderada 2024 = 27.58 %, 2019 = 20.19 %

## Paso 3 – Servidor MCP del BCRP (Parte 1, 5 pts)
- [x] TODO 1: `serie(codigo, desde, hasta)` (fechas mensual/trimestral/anual/diaria, omite "n.d.", reintenta si la API limita)
- [x] TODO 2: `resumen(codigo, desde, hasta)`
- [x] TODO 3: herramienta propia `comparar_periodos(codigo, desde_a, hasta_a, desde_b, hasta_b)`
- [x] TODO 4: recurso `bcrp://serie/{codigo}` (ficha con unidad, origen y descripción)
- [x] TODO 5: prompt `informe(tema, desde, hasta)`
- [x] 2 pruebas propias para `comparar_periodos` (agregadas al final de `test_server.py`; las 8 originales sin cambios)
- [x] `uv run pytest -q` → **10 passed**
- [x] El servidor arranca por stdio desde `.mcp.json` (4 herramientas, 1 recurso, 1 prompt)
- [ ] **Tú:** probar en Claude Code: `/mcp`, recurso con `@bcrp:bcrp://serie/PN01770AM`, prompt con `/mcp__bcrp__informe PBI`; guardar la sesión en `evidencias_ia/mcp/`

Dato ya obtenido con la herramienta: PBI promedio 2024 vs. 2019 = **+7.14 %** (índice 183.18 vs. 170.98, `PN01770AM`); mínimo en 2020-04 (102.9).

Series candidatas (verificadas en la API del BCRP):
| Código | Serie |
|---|---|
| `PN01770AM` | PBI, índice 2007 = 100 (mensual) |
| `PN01728AM` | PBI, var. % interanual (mensual) |
| `PN01773AM` | PBI desestacionalizado, índice (mensual) |

## Paso 4 – Skills de ENAHO (Parte 2, 6 pts)
- [ ] `limpiando-enaho/scripts/limpiar.py --anio 2024|2019`
  - Leer Stata con llaves como texto; nombres en minúscula
  - Residentes habituales: `((p204==1)&(p205==2)) | ((p204==2)&(p206==1))`
  - `merge(..., validate="m:1")` y verificar que no duplique
  - `departamento = ubigeo[:2]`, `urbano = estrato <= 5`, `pobre = pobreza <= 2`
  - **Gini** del gasto per cápita (`gashog2d / mieperho / 12`, ponderado con `factor07 × mieperho`)
  - Validaciones → `salidas/validacion.txt`: 27.6 % (±0.1), 108,664 residentes, 25 departamentos; detenerse si falla
  - Para 2019: solo sumaria (pobreza y Gini nacional y por departamento)
- [ ] `graficando-enaho`: área urbana/rural, sexo, departamentos (+ pobreza y Gini 2019 vs. 2024)
- [ ] `mapeando-enaho`: mapa 2024 (y, si da el tiempo, mapa de cambio 2019→2024)
- [ ] Demostrar: invocación individual, activación por lenguaje natural, y que gráficos/mapa llaman antes a limpieza

## Paso 5 – Preguntas de evaluación (Parte 4, antes de probar el agente)
- [ ] `evaluacion/preguntas.csv`: 4 BCRP + 4 ENAHO + 2 combinadas, con respuesta esperada y **tolerancia fijada antes**
- [ ] Respuestas esperadas verificadas en la web del BCRP / cálculo independiente (no con el propio agente)

## Paso 6 – Ejecución del agente (Parte 3, 5 pts)
- [ ] Una sola sesión de Claude Code: ≥2 herramientas MCP + ≥2 Skills → guardar la conversación en `evidencias_ia/integracion/`
- [ ] `informes/informe_final.md`: pregunta, metodología, ≥3 hallazgos, gráfico BCRP + gráfico ENAHO + mapa, interpretación, limitaciones, reproducibilidad
- [ ] **Tú** verificas a mano ≥3 cifras (de ambas fuentes) y lo documentas

## Paso 7 – Evaluación Modo A vs. Modo B (Parte 4, 4 pts)
- [ ] Modo A (sin MCP ni Skills) y Modo B (con ambos), cada pregunta en sesión nueva, mismo modelo
- [ ] `evaluacion/resultados.csv` y `evaluacion/comparacion.md`

## Paso 8 – Cierre
- [ ] README completo (12 secciones)
- [ ] Exportar conversaciones a `evidencias_ia/` (¡incluida esta de planificación!) y ocultar datos sensibles
- [ ] Commits y push; revisar que todos los enlaces sean públicos
- [ ] Publicar el comentario de entrega en el issue

---

### Qué hace Claude y qué haces tú
| Claude puede | Solo tú |
|---|---|
| Programar el MCP, las pruebas y las Skills | Ejecutar y guardar las sesiones de Modo A / Modo B |
| Proponer las 10 preguntas y buscar las respuestas oficiales | Verificar a mano las 3 cifras del informe |
| Redactar informe y README | Exportar conversaciones a `evidencias_ia/` |
| | Publicar el comentario de entrega |
