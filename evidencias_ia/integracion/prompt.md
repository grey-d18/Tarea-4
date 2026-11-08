# Prompt de la ejecución integrada (Parte 3)

Se pega **tal cual** en una sesión nueva de Claude Code abierta en la raíz del repositorio (`claude`), con el servidor
`bcrp` conectado (`/mcp` debe mostrarlo «connected»). Antes de empezar, para que se vea la cadena completa:

```bash
rm -f salidas/indicadores.csv salidas/*.parquet figuras/*.png figuras/*.csv mapas/*.png
```

Al terminar, exportar la conversación (`/export evidencias_ia/integracion/sesion_integracion.md`) y revisar que no
contenga datos personales.

---

```text
Quiero responder esta pregunta de investigación con datos oficiales:

«¿La recuperación del PBI peruano entre 2019 y 2024 se reflejó en una menor pobreza monetaria y desigualdad en los
departamentos del país?»

Trabaja así, sin hacer cuentas a mano:

1. BCRP (servidor MCP bcrp):
   - Busca la serie del PBI mensual en índice (2007 = 100) con buscar_series y justifica la elección.
   - Compara el promedio de 2019 con el de 2024 con comparar_periodos.
   - Usa resumen para el periodo 2019-01 a 2024-12 (mínimo de la pandemia y nivel final).
   - Guarda el gráfico con graficar_serie marcando los promedios de 2019 y 2024 (archivo bcrp_pbi_2019_2024).
   - Revisa la ficha de la serie con el recurso bcrp://serie/{codigo}.
2. ENAHO (Skills del proyecto):
   - Limpia y valida la ENAHO 2024 y la sumaria 2019 con la skill limpiando-enaho. Si una validación esencial falla,
     detente y explícame por qué.
   - Con graficando-enaho genera la comparación de pobreza 2019 vs. 2024 por ámbito, la del Gini y el cambio por
     departamento.
   - Con mapeando-enaho genera el mapa de pobreza departamental 2024 y el del cambio 2019→2024.
3. Redacta informes/informe_final.md con estas secciones:
   1. Pregunta de investigación
   2. Metodología (fuentes, códigos de serie, módulos ENAHO, ponderación, definición de pobreza y del Gini,
      herramientas MCP y Skills usadas)
   3. Hallazgos: al menos 3, cada uno con su cifra y su fuente (código BCRP + URL de la API, o archivo de salidas/)
   4. Gráficos: el del BCRP (figuras/bcrp_pbi_2019_2024.png), al menos uno de ENAHO y el mapa, insertados con su
      ruta relativa y una oración que diga qué muestra cada uno
   5. Interpretación: responde la pregunta en un párrafo, sin afirmar causalidad
   6. Limitaciones (nivel macro vs. hogares, error muestral, pobreza monetaria vs. bienestar, comparabilidad 2019-2024,
      cobertura departamental de la ENAHO)
   7. Reproducibilidad (comandos exactos para regenerar todo)
   8. Verificación manual: deja una tabla vacía con columnas «cifra | valor del informe | cómo la verifiqué | ¿coincide?»
      para que yo la complete con 3 cifras.
4. Al final, dime qué herramientas MCP y qué Skills usaste.
```

---

## Verificación manual (se hace a mano, no la hace el agente)

Elegir 3 cifras del informe, de ambas fuentes, y comprobarlas fuera de Claude:

| Cifra | Cómo verificarla |
|---|---|
| PBI promedio 2024 vs. 2019 (+7.1 %) | Abrir `https://estadisticas.bcrp.gob.pe/estadisticas/series/api/PN01770AM/json/2019-1/2024-12` en el navegador, copiar los 24 valores a una hoja de cálculo y comparar los promedios |
| Pobreza nacional 2024 (27.6 %) | Informe técnico «Evolución de la pobreza monetaria 2015-2024» del INEI, o `uv run evaluacion/verificar_respuestas.py` (recalcula desde los `.dta` con otro código) |
| Pobreza de un departamento (p. ej. Cajamarca 45.0 %) | `referencias/pobreza_departamento_2024.csv` (Sesión 16) o el informe técnico del INEI |

Completar la tabla de la sección 8 del informe y anotar la fecha.
