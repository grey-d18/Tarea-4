# Referencia de variables ENAHO

Confirmado con las etiquetas de los archivos `.dta` de 2019 y 2024 (mismas codificaciones en ambos años).

## Módulo 34 – sumaria (un registro por hogar)

| Variable | Descripción | Uso |
|---|---|---|
| `conglome`, `vivienda`, `hogar` | Llaves del hogar (texto, con ceros iniciales) | Unión con el módulo 02 |
| `ubigeo` | Ubicación geográfica; `ubigeo[:2]` = departamento (01–25) | Mapa (`FIRST_IDDP`) |
| `dominio` | 1 costa norte, 2 costa centro, 3 costa sur, 4 sierra norte, 5 sierra centro, 6 sierra sur, 7 selva, 8 Lima Metropolitana | Comparaciones territoriales |
| `estrato` | 1: 500 mil a más hab.; 2: 100–499 mil; 3: 50–99 mil; 4: 20–49 mil; 5: 2–19 mil; 6: 500–1,999; 7: AER compuesto; 8: AER simple | `urbano = estrato <= 5` |
| `pobreza` | 1 = pobre extremo, 2 = pobre no extremo, 3 = no pobre | `pobre = pobreza <= 2` |
| `mieperho` | Total de miembros del hogar | Per cápita y ponderación |
| `gashog2d` | Gasto total bruto anual del hogar (S/) | Gini del gasto |
| `inghog2d` | Ingreso neto total anual del hogar (S/) | Alternativa para el Gini |
| `ld` | Deflactor espacial (Lima Metropolitana = 1) | Gasto real comparable entre regiones |
| `linea` | Línea de pobreza | Referencia |
| `factor07` | Factor de expansión anual del hogar | Ponderación |

## Módulo 02 – miembros (un registro por persona; solo 2024)

| Variable | Descripción | Uso |
|---|---|---|
| `codperso` | Número de orden de la persona | Llave de persona |
| `p203` | Parentesco con el jefe; 1 = jefe(a) | `jefe_hogar` |
| `p204` | ¿Es miembro del hogar? 1 sí, 2 no | Residentes habituales |
| `p205` | ¿Ausente 30 días o más? 1 sí, 2 no | Residentes habituales |
| `p206` | ¿Presente 30 días o más? 1 sí, 2 no | Residentes habituales |
| `p207` | Sexo: 1 hombre, 2 mujer | `sexo` |
| `p208a` | Edad en años | `edad` |
| `facpob07` | Factor de expansión de personas | Ponderación |

## Variables construidas por `limpiar.py`

| Variable | Definición |
|---|---|
| `departamento` | `ubigeo[:2]` |
| `urbano` | `estrato <= 5` |
| `pobre`, `pobre_extremo` | `pobreza <= 2`, `pobreza == 1` |
| `peso_personas` | `factor07 × mieperho` (pondera hogares por número de personas) |
| `gasto_pc_real` | `gashog2d / (12 × mieperho × ld)`: S/ mensuales por persona a precios de Lima Metropolitana |
| `sexo`, `edad`, `jefe_hogar` | De `p207`, `p208a`, `p203 == 1` (solo personas 2024) |

## Gini

Gini ponderado del `gasto_pc_real`, con pesos `peso_personas`, calculado como 1 − Σ (pᵢ − pᵢ₋₁)(Lᵢ + Lᵢ₋₁) sobre la
curva de Lorenz. El INEI también mide la desigualdad con el gasto real per cápita de la ENAHO. Como el deflactor
temporal es común dentro de un año, no altera el Gini de ese año.
