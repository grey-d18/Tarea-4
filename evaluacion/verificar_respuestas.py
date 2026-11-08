"""Verificación independiente de las respuestas esperadas de evaluacion/preguntas.csv.

    uv run evaluacion/verificar_respuestas.py

No usa el servidor MCP ni las Skills del proyecto: consulta la API del BCRP directamente y recalcula la ENAHO desde
los .dta originales con un código mínimo propio. Compara además con las cifras oficiales publicadas (INEI / material
del curso). Escribe evaluacion/verificacion_respuestas.csv.
"""
import time
import zipfile
from pathlib import Path

import httpx
import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
API = "https://estadisticas.bcrp.gob.pe/estadisticas/series/api"


def bcrp(codigo, desde, hasta):
    url = f"{API}/{codigo}/json/{desde}/{hasta}"
    for i in range(6):
        try:
            d = httpx.get(url, timeout=60).json()
            return [float(p["values"][0]) for p in d["periods"] if p["values"][0] != "n.d."], url
        except ValueError:
            time.sleep(3 * (i + 1))
    raise RuntimeError(f"El BCRP no respondió: {url}")


def sumaria(zip_name, dta):
    with zipfile.ZipFile(RAIZ / "datos" / zip_name) as z, z.open(dta) as f:
        d = pd.read_stata(f, convert_categoricals=False, columns=["ubigeo", "dominio", "estrato", "pobreza",
                                                                 "mieperho", "factor07"])
    d["w"] = d.factor07 * d.mieperho
    d["pobre"] = d.pobreza <= 2
    return d


def pob(d):
    return round(100 * np.average(d.pobre, weights=d.w), 2)


filas = []
def anotar(id_, valor, procedimiento, oficial=None, fuente_oficial=""):
    filas.append({"id": id_, "valor_verificado": round(valor, 4), "procedimiento": procedimiento,
                  "valor_oficial": oficial, "fuente_oficial": fuente_oficial,
                  "coincide": "" if oficial is None else abs(round(valor, 1) - oficial) <= 0.1})


# BCRP
v, u = bcrp("PN01273PM", "2024-12", "2024-12"); anotar("bcrp_inflacion_dic24", v[0], u)
v, u = bcrp("PM04923AA", "2024", "2024"); anotar("bcrp_pbi_2024", v[0], u)
v, u = bcrp("PN01728AM", "2020-4", "2020-4"); anotar("bcrp_pbi_abr20", v[0], u)
a, ua = bcrp("PN01770AM", "2019-1", "2019-12"); b, ub = bcrp("PN01770AM", "2024-1", "2024-12")
pbi_var = (np.mean(b) / np.mean(a) - 1) * 100
anotar("bcrp_pbi_2024_vs_2019", pbi_var, f"promedio de 12 meses: {ua} y {ub}")

# ENAHO
s24 = sumaria("966-Modulo34.zip", "966-Modulo34/sumaria-2024.dta")
s19 = sumaria("687-Modulo34.zip", "687-Modulo34/sumaria-2019.dta")
P = "sumaria {a}, pobreza<=2, ponderado factor07*mieperho"
anotar("enaho_pobreza_2024", pob(s24), P.format(a=2024), 27.6, "Consigna de la Tarea 4 (INEI)")
anotar("enaho_rural_2024", pob(s24[s24.estrato > 5]), P.format(a=2024) + ", estrato>5", 39.3,
       "Consigna de la Tarea 4 (INEI)")
anotar("enaho_lima_2024", pob(s24[s24.dominio == 8]), P.format(a=2024) + ", dominio==8", 28.2,
       "README Sesión 16")
anotar("enaho_cajamarca_2024", pob(s24[s24.ubigeo.str[:2] == "06"]), P.format(a=2024) + ", ubigeo[:2]=='06'", 45.0,
       "referencias/pobreza_departamento_2024.csv (Sesión 16)")

# Combinadas
d_nac = pob(s24) - pob(s19)
anotar("mix_pobreza_vs_pbi", d_nac, "pobreza 2024 − 2019 (sumarias, mismo método)",
       round(27.6 - 20.2, 1), "INEI: 20.2 % (2019) y 27.6 % (2024)")
anotar("mix_pobreza_vs_pbi__2", pbi_var, "igual que bcrp_pbi_2024_vs_2019")
d_urb = pob(s24[s24.estrato <= 5]) - pob(s19[s19.estrato <= 5])
anotar("mix_urbana_vs_pbi", d_urb, "pobreza urbana (estrato<=5) 2024 − 2019",
       round(24.8 - 14.6, 1), "INEI: urbana 14.6 % (2019) y 24.8 % (2024)")
v, u = bcrp("PM04923AA", "2024", "2024"); anotar("mix_urbana_vs_pbi__2", v[0], u)

res = pd.DataFrame(filas)
res.to_csv(RAIZ / "evaluacion" / "verificacion_respuestas.csv", index=False)

# Contraste con preguntas.csv
q = pd.read_csv(RAIZ / "evaluacion" / "preguntas.csv")
esperado = pd.concat([q[["id", "respuesta_esperada", "tolerancia"]],
                      q.dropna(subset=["respuesta_esperada_2"]).assign(id=lambda d: d.id + "__2")[
                          ["id", "respuesta_esperada_2", "tolerancia_2"]].set_axis(
                          ["id", "respuesta_esperada", "tolerancia"], axis=1)])
m = res.merge(esperado, on="id", how="left")
m["dentro_tolerancia"] = (m.valor_verificado - m.respuesta_esperada).abs() <= m.tolerancia
print(m[["id", "valor_verificado", "respuesta_esperada", "tolerancia", "dentro_tolerancia", "valor_oficial",
         "coincide"]].to_string(index=False))
assert m.dentro_tolerancia.all(), "Alguna respuesta esperada no coincide con la verificación independiente"
print("\nOK: todas las respuestas esperadas coinciden con la verificación independiente.")
