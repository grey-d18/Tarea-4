# Referencia de variables ENAHO

<!-- BORRADOR: confirmar cada variable con el diccionario del INEI al descargar los datos -->

## Módulo 34 – sumaria (un registro por hogar)

| Variable | Descripción | Uso |
|---|---|---|
| `conglome`, `vivienda`, `hogar` | Llaves del hogar (texto, con ceros iniciales) | Unión con el módulo 02 |
| `ubigeo` | Ubicación geográfica; `ubigeo[:2]` = departamento | Mapa (`FIRST_IDDP`) |
| `dominio` | Dominio geográfico; 8 = Lima Metropolitana | Comparaciones territoriales |
| `estrato` | Tamaño del centro poblado; `<= 5` = urbano | Urbano / rural |
| `pobreza` | 1 = pobre extremo, 2 = pobre no extremo, 3 = no pobre | `pobre = pobreza <= 2` |
| `mieperho` | Miembros del hogar | Gasto per cápita y ponderación |
| `gashog2d` | Gasto anual del hogar | Gini del gasto per cápita |
| `factor07` | Factor de expansión del hogar | Ponderación (`factor07 × mieperho` para personas) |

## Módulo 02 – miembros (un registro por persona)

| Variable | Descripción | Uso |
|---|---|---|
| `codperso` | Número de orden de la persona | Llave de persona |
| `p203` | Parentesco con el jefe; 1 = jefe | Características del jefe de hogar |
| `p204`, `p205`, `p206` | Residencia habitual | Filtro de residentes |
| `p207` | Sexo | Gráficos por sexo |
| `p208a` | Edad en años | Gráficos por edad |
| `facpob07` | Factor de expansión de personas | Ponderación |
