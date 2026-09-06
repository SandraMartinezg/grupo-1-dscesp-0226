"""
easyMoney - Simulador de campaña de cross-selling (Tarea 4)

Lee las tablas ligeras exportadas por 06_tarea4_impacto_economico.ipynb (data/app/)
y permite a negocio simular una campaña: producto, canal, grupos y corte del modelo.
Toda la lógica de cálculo es la misma del notebook; aquí solo se combina y se muestra.

Ejecutar desde la raíz del repo:  streamlit run app/simulador.py
"""

from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# ── Rutas ────────────────────────────────────────────────────────────────
RUTA_APP = Path(__file__).resolve().parent.parent / "data" / "app"

GRUPOS = [
    "Clientes de nómina", "Particulares con tarjeta", "Particulares básicos",
    "Universitarios recién llegados", "TOP ahorradores", "Nómina y pensiones",
    "Universitarios inactivos", "Sin producto",
]


# ── Datos (se leen una sola vez gracias a la caché) ──────────────────────
@st.cache_data
def cargar(producto):
    val = pd.read_csv(RUTA_APP / f"validacion_grupo_{producto}.csv")
    val["nombre_grupo"] = val["nombre_grupo"].fillna("Sin grupo")
    sc = pd.read_csv(RUTA_APP / f"scoring_grupo_{producto}.csv")
    sc = sc.rename(columns={f"probabilidad_{producto}": "probabilidad"})
    sc["nombre_grupo"] = sc["nombre_grupo"].fillna("Sin grupo")
    margenes = pd.read_csv(RUTA_APP / f"margenes_{producto}.csv")["net_margin"].values
    return val, sc, margenes


# ── Lógica (idéntica al notebook 06) ─────────────────────────────────────
def aplicar_regla(df, nucleo, excluir, top_pct_resto):
    """Núcleo completo + top X% del modelo en el resto de grupos no excluidos."""
    umbral = df["probabilidad"].quantile(1 - top_pct_resto / 100) if top_pct_resto > 0 else np.inf
    en_nucleo = df["nombre_grupo"].isin(nucleo)
    en_resto = ~df["nombre_grupo"].isin(list(nucleo) + list(excluir)) & (df["probabilidad"] >= umbral)
    return df[en_nucleo | en_resto]


def evaluar(val, sc, margen_medio, nucleo, excluir, top_resto, coste_contacto, coste_fijo):
    """Mide la regla en validación y la aplica al scoring. Devuelve el resultado determinista."""
    v = aplicar_regla(val, nucleo, excluir, top_resto)
    s = aplicar_regla(sc, nucleo, excluir, top_resto)
    conv = v["compra_real"].mean() if len(v) else 0.0
    contactos = len(s)
    ventas = contactos * conv
    coste = contactos * coste_contacto + coste_fijo
    return {
        "contactos": contactos, "conversion": conv, "ventas": ventas,
        "ingreso": ventas * margen_medio, "coste": coste, "beneficio": ventas * margen_medio - coste,
        "compras_val": int(v["compra_real"].sum()), "no_compras_val": int(len(v) - v["compra_real"].sum()),
        "seleccion": s,
    }


def monte_carlo(res, margenes, coste_contacto, coste_fijo, n_sim, semilla=42):
    """Beta para la conversión, Binomial para las ventas, márgenes reales muestreados."""
    rng = np.random.default_rng(semilla)
    contactos = res["contactos"]
    coste = contactos * coste_contacto + coste_fijo
    out = np.empty(n_sim)
    for i in range(n_sim):
        conv = rng.beta(res["compras_val"] + 1, res["no_compras_val"] + 1)
        ventas = rng.binomial(contactos, conv)
        out[i] = rng.choice(margenes, size=ventas).sum() - coste
    return out


def eur(x):
    return f"{x:,.0f} €".replace(",", ".")


# ── Interfaz ─────────────────────────────────────────────────────────────
LOGO = Path(__file__).resolve().parent / "assets" / "logo.png"
st.set_page_config(page_title="easyMoney · Simulador de campaña", page_icon=str(LOGO), layout="wide")
c_logo, c_titulo = st.columns([1, 5], vertical_alignment="center")
c_logo.image(str(LOGO), use_container_width=True)
c_titulo.title("Simulador de campaña de cross-selling")
st.caption("Combina el modelo de propensión (Tarea 2) y la segmentación (Tarea 3) para estimar el resultado económico de una campaña.")

DEFECTO = {
    "Clientes de nómina": "Todos", "Particulares con tarjeta": "Todos",
    "Particulares básicos": "Top modelo", "Universitarios recién llegados": "Top modelo",
    "TOP ahorradores": "Top modelo", "Nómina y pensiones": "Top modelo",
    "Universitarios inactivos": "Excluir", "Sin producto": "Excluir",
}
OPCIONES = ["Todos", "Top modelo", "Excluir"]

with st.sidebar:
    st.header("Campaña")
    producto = st.selectbox("Producto", ["pension_plan", "em_acount"])
    coste_contacto = st.select_slider(
        "Canal / coste por contacto (€)", options=[0.1, 0.5, 1, 2, 5, 10, 30, 60], value=0.5,
        help="Push/email ≈ 0,10 · email + gestión ≈ 0,50 · carta ≈ 2 · llamada ≈ 5 · visita ≈ 30",
    )
    coste_fijo = st.number_input("Coste fijo (€)", 0, 100000, 10000, step=1000)

    st.header("Grupos (Tarea 3)")
    st.caption("Para cada grupo: contactar a todos, solo al top del modelo, o excluir.")
    decision = {}
    for g in GRUPOS:
        decision[g] = st.selectbox(g, OPCIONES, index=OPCIONES.index(DEFECTO[g]), key=f"dec_{g}")
    top_resto = st.slider("En los grupos 'Top modelo', contactar al top X %", 0, 50, 20, step=5)

    st.header("Simulación")
    n_sim = st.select_slider("Simulaciones Monte Carlo", options=[1000, 5000, 10000], value=5000)

nucleo = [g for g, d in decision.items() if d == "Todos"]
excluir = [g for g, d in decision.items() if d == "Excluir"]

val, sc, margenes = cargar(producto)
margen_medio = margenes.mean()

res = evaluar(val, sc, margen_medio, nucleo, excluir, top_resto, coste_contacto, coste_fijo)
sim = monte_carlo(res, margenes, coste_contacto, coste_fijo, n_sim)
p5, p50, p95 = np.percentile(sim, [5, 50, 95])

# ── Tarjetas ─────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Clientes contactados", f"{res['contactos']:,}".replace(",", "."),
          f"{res['contactos'] / len(sc) * 100:.0f} % de los elegibles")
c2.metric("Ventas esperadas", f"{res['ventas']:,.0f}".replace(",", "."),
          f"{res['conversion'] * 100:.2f} % de conversión")
c3.metric("Coste de la campaña", eur(res["coste"]))
c4.metric("Beneficio neto", f"{res['beneficio'] / 1e6:.2f} M€",
          f"90 %: {p5 / 1e6:.2f} – {p95 / 1e6:.2f} M€", delta_color="off")

st.markdown(
    f"Una venta de **{producto}** deja de media **{eur(margen_medio)}**. "
    f"Con estos supuestos, cada contacto genera **{eur(res['beneficio'] / max(res['contactos'], 1))}** de beneficio. "
    f"Probabilidad de que la campaña pierda dinero: **{(sim < 0).mean() * 100:.1f} %**."
)

# ── Curva de beneficio según el corte del resto ──────────────────────────
col_a, col_b = st.columns([3, 2])

with col_a:
    st.subheader("¿Dónde parar?")
    cortes = list(range(0, 51, 5))
    curva = pd.DataFrame([
        {"top_resto": c, **{k: v for k, v in evaluar(val, sc, margen_medio, nucleo, excluir, c, coste_contacto, coste_fijo).items() if k != "seleccion"}}
        for c in cortes
    ])
    curva["beneficio_M"] = curva["beneficio"] / 1e6
    base = alt.Chart(curva).encode(
        x=alt.X("contactos:Q", title="Clientes contactados", axis=alt.Axis(format=",.0f")),
        y=alt.Y("beneficio_M:Q", title="Beneficio neto (M€)", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("top_resto:Q", title="Top % del resto"),
                 alt.Tooltip("contactos:Q", title="Contactos", format=",.0f"),
                 alt.Tooltip("ventas:Q", title="Ventas", format=",.0f"),
                 alt.Tooltip("beneficio_M:Q", title="Beneficio (M€)", format=".2f")],
    )
    linea = base.mark_line(color="#9A9A94", point=alt.OverlayMarkDef(color="#9A9A94", size=40))
    actual = alt.Chart(pd.DataFrame({"contactos": [res["contactos"]], "beneficio_M": [res["beneficio"] / 1e6]})).mark_point(
        size=220, filled=True, color="#7CC242").encode(x="contactos:Q", y="beneficio_M:Q")
    st.altair_chart((linea + actual).properties(height=320), use_container_width=True)
    st.caption("Cada punto añade un 5 % más del modelo en los grupos del resto. El punto verde es la configuración actual. Cuando la curva se aplana, cada contacto adicional apenas aporta.")

with col_b:
    st.subheader("A quién contactamos")
    comp = (res["seleccion"]["nombre_grupo"].value_counts().rename("contactos").to_frame())
    conv_grupo = (aplicar_regla(val, nucleo, excluir, top_resto)
                  .groupby("nombre_grupo")["compra_real"].mean() * 100).round(2)
    comp["conversión %"] = conv_grupo.reindex(comp.index).fillna(0)
    comp["ventas esp."] = (comp["contactos"] * comp["conversión %"] / 100).round(0).astype(int)
    st.dataframe(
        comp, use_container_width=True, height=min(40 + 35 * len(comp), 400),
        column_config={
            "contactos": st.column_config.NumberColumn("Contactos", format="%d"),
            "conversión %": st.column_config.NumberColumn("Conversión", format="%.2f %%"),
            "ventas esp.": st.column_config.NumberColumn("Ventas", format="%d"),
        },
    )

# ── Distribución Monte Carlo ─────────────────────────────────────────────
st.subheader("Intervalo de confianza")
hist_df = pd.DataFrame({"beneficio_M": sim / 1e6})
hist = alt.Chart(hist_df).mark_bar(color="#7CC242", opacity=0.75).encode(
    x=alt.X("beneficio_M:Q", bin=alt.Bin(maxbins=60), title="Beneficio neto (M€)"),
    y=alt.Y("count():Q", title="Simulaciones"),
)
lineas = alt.Chart(pd.DataFrame({"x": [p5 / 1e6, p95 / 1e6]})).mark_rule(strokeDash=[4, 4], color="#1F1F1F").encode(x="x:Q")
st.altair_chart((hist + lineas).properties(height=220), use_container_width=True)
st.caption(
    f"{n_sim:,} simulaciones. Escenario conservador (p5) {eur(p5)} · base (p50) {eur(p50)} · optimista (p95) {eur(p95)}. "
    "La conversión se muestrea de una Beta ajustada a la validación de mayo 2019; el margen, de las ventas reales."
)

with st.expander("Supuestos y limitaciones"):
    st.markdown(
        """
- La conversión se mide en el mes de validación (mayo 2019) y se asume igual para la campaña (junio 2019).
- Los resultados son de **un mes**. No se anualizan: las oleadas siguientes rinden menos.
- Son ventas que el modelo **identifica**, no necesariamente atribuibles a la campaña. Para medir incrementalidad hace falta un piloto con grupo de control.
- El coste por contacto y el coste fijo son supuestos de negocio; se pueden cambiar en la barra lateral.
        """
    )