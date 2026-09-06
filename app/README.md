# easyMoney · Simulador de campaña (Tarea 4)

App Streamlit que combina el modelo de propensión (Tarea 2) y la segmentación (Tarea 3) para simular una campaña de cross-selling y estimar su resultado económico con intervalo de confianza.

## Ejecutar

Desde la raíz del repositorio, con el entorno `python3.9` activo:

```bash
pip install -r app/requirements.txt
streamlit run app/simulador.py
```

## Qué necesita

Los CSV de `data/app/`, generados por `notebooks/06_tarea4_impacto_economico.ipynb` (última celda): validación y scoring con grupo, márgenes reales por producto, curvas de conversión y tabla de estrategias. Si se reentrena algún modelo, basta con volver a ejecutar el notebook 06; el código de la app no cambia.

El tema visual está en `.streamlit/config.toml` (raíz del repo). El logo, en `app/assets/logo.png`.

---

# simulador.py explicado bloque a bloque

Cómo funciona Streamlit: el script se ejecuta de arriba abajo cada vez que el usuario toca un control. No hay eventos ni callbacks: se escribe el cálculo una vez, en orden, y Streamlit lo repite con los nuevos valores. Los controles (`st.slider`, `st.selectbox`...) pintan un widget y devuelven el valor elegido a una variable, como `input()` pero visual.

## 1. Imports y rutas

```python
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

RUTA_APP = Path(__file__).resolve().parent.parent / "data" / "app"
```

`RUTA_APP` es la carpeta de los CSV exportados por el notebook 06, calculada desde la posición del fichero: `__file__` es `app/simulador.py`, su `parent` es `app/`, y el `parent` de ese es la raíz del repo. Así funciona desde cualquier sitio.

```python
GRUPOS = ["Clientes de nómina", "Particulares con tarjeta", "Particulares básicos",
          "Universitarios recién llegados", "TOP ahorradores", "Nómina y pensiones",
          "Universitarios inactivos", "Sin producto"]
```

Los 8 nombres de la Tarea 3, para rellenar los desplegables.

## 2. Carga de datos

```python
@st.cache_data
def cargar(producto):
    val = pd.read_csv(RUTA_APP / f"validacion_grupo_{producto}.csv")
    val["nombre_grupo"] = val["nombre_grupo"].fillna("Sin grupo")
    sc = pd.read_csv(RUTA_APP / f"scoring_grupo_{producto}.csv")
    sc = sc.rename(columns={f"probabilidad_{producto}": "probabilidad"})
    sc["nombre_grupo"] = sc["nombre_grupo"].fillna("Sin grupo")
    margenes = pd.read_csv(RUTA_APP / f"margenes_{producto}.csv")["net_margin"].values
    return val, sc, margenes
```

Lee tres ficheros del producto elegido:

- `val`: validación de mayo con el grupo de **abril**. Sirve para **medir** la conversión (predicción y compra real lado a lado).
- `sc`: scoring de junio con el grupo de **mayo**. Es la lista real de clientes a contactar.
- `margenes`: los márgenes reales de cada venta del producto (19.369 para pension_plan), para muestrear en la Monte Carlo.

Limpiezas: los clientes sin grupo pasan a "Sin grupo" para que no den error al filtrar; la columna de probabilidad del scoring, que se llama distinto en cada fichero, se renombra a `probabilidad` para que el resto del código sea el mismo para ambos productos.

`@st.cache_data`: Streamlit reejecuta todo con cada clic; sin caché leería 422.000 filas cada vez. Con el decorador lee una vez por valor de `producto` y reutiliza.

## 3. Lógica (las funciones del notebook 06)

```python
def aplicar_regla(df, nucleo, excluir, top_pct_resto):
    umbral = df["probabilidad"].quantile(1 - top_pct_resto / 100) if top_pct_resto > 0 else np.inf
    en_nucleo = df["nombre_grupo"].isin(nucleo)
    en_resto = ~df["nombre_grupo"].isin(list(nucleo) + list(excluir)) & (df["probabilidad"] >= umbral)
    return df[en_nucleo | en_resto]
```

La regla de la estrategia D. Devuelve las filas que cumplen: estar en un grupo núcleo, **o** estar en un grupo que no es ni núcleo ni excluido y tener probabilidad por encima del umbral del top X%. Si X es 0, el umbral es infinito y solo entra el núcleo.

```python
def evaluar(val, sc, margen_medio, nucleo, excluir, top_resto, coste_contacto, coste_fijo):
    v = aplicar_regla(val, nucleo, excluir, top_resto)   # medir en validación
    s = aplicar_regla(sc, nucleo, excluir, top_resto)    # aplicar en scoring
    conv = v["compra_real"].mean() if len(v) else 0.0
    contactos = len(s)
    ventas = contactos * conv
    coste = contactos * coste_contacto + coste_fijo
    return {"contactos": contactos, "conversion": conv, "ventas": ventas,
            "ingreso": ventas * margen_medio, "coste": coste,
            "beneficio": ventas * margen_medio - coste,
            "compras_val": int(v["compra_real"].sum()),
            "no_compras_val": int(len(v) - v["compra_real"].sum()),
            "seleccion": s}
```

La fórmula completa en una función. La regla se **mide** en validación (de ahí la conversión) y se **aplica** en el scoring (de ahí los contactos). Devuelve un diccionario con todo, incluidos `compras_val` y `no_compras_val` (los dos parámetros de la Beta) y `seleccion` (los clientes elegidos, para la tabla por grupo).

```python
def monte_carlo(res, margenes, coste_contacto, coste_fijo, n_sim, semilla=42):
    rng = np.random.default_rng(semilla)
    contactos = res["contactos"]
    coste = contactos * coste_contacto + coste_fijo
    out = np.empty(n_sim)
    for i in range(n_sim):
        conv = rng.beta(res["compras_val"] + 1, res["no_compras_val"] + 1)
        ventas = rng.binomial(contactos, conv)
        out[i] = rng.choice(margenes, size=ventas).sum() - coste
    return out
```

Copia de la celda del notebook. En cada tirada: una conversión de la Beta (centrada en lo medido, anchura según cuántos datos había), un número de ventas de la Binomial, y un ingreso sumando márgenes reales al azar. Devuelve el array de beneficios simulados. La semilla fija hace el resultado reproducible.

```python
def eur(x):
    return f"{x:,.0f} €".replace(",", ".")
```

Formatea números como "14.261.769 €".

## 4. Barra lateral (controles)

```python
st.set_page_config(page_title="easyMoney · Simulador de campaña", layout="wide")
st.title("Simulador de campaña de cross-selling")
st.caption("...")

with st.sidebar:
    producto = st.selectbox("Producto", ["pension_plan", "em_acount"])
    coste_contacto = st.select_slider("Coste por contacto (€)", options=[0.1, 0.5, 1, 2, 5, 10, 30, 60], value=0.5)
    coste_fijo = st.number_input("Coste fijo de la campaña (€)", 0, 100000, 10000, step=1000)
    nucleo = st.multiselect("Grupos núcleo (se contacta a todos)", GRUPOS, default=[...])
    excluir = st.multiselect("Grupos excluidos", [g for g in GRUPOS if g not in nucleo], default=[...])
    top_resto = st.slider("Del resto de grupos, contactar al top X % del modelo", 0, 100, 20, step=5)
    n_sim = st.select_slider("Simulaciones Monte Carlo", options=[1000, 5000, 10000], value=5000)
```

`set_page_config` pone el título de la pestaña y el modo ancho. Todo lo que va dentro de `with st.sidebar:` se pinta a la izquierda. Cada control devuelve el valor elegido:

- `selectbox`: desplegable (producto).
- `select_slider`: slider con valores fijos (los costes de la tabla de sensibilidad).
- `number_input`: cajita numérica (coste fijo).
- `multiselect`: elegir varios (grupos núcleo y excluidos). En "excluidos" solo se ofrecen los que no están en el núcleo.
- `slider`: rango (top X% del resto).

Los valores por defecto reproducen la estrategia D recomendada.

## 5. Cálculo y tarjetas

```python
val, sc, margenes = cargar(producto)
margen_medio = margenes.mean()
res = evaluar(val, sc, margen_medio, nucleo, excluir, top_resto, coste_contacto, coste_fijo)
sim = monte_carlo(res, margenes, coste_contacto, coste_fijo, n_sim)
p5, p50, p95 = np.percentile(sim, [5, 50, 95])
```

Con los valores de la barra lateral: cargar datos, evaluar la regla, simular. `p5`, `p50`, `p95` son los escenarios conservador, base y optimista.

```python
c1, c2, c3, c4 = st.columns(4)
c1.metric("Clientes contactados", ..., "X % de los elegibles")
c2.metric("Ventas esperadas", ..., "X % de conversión")
c3.metric("Coste de la campaña", eur(res["coste"]))
c4.metric("Beneficio neto", eur(res["beneficio"]), f"90 %: {eur(p5)} – {eur(p95)}", delta_color="off")
```

Cuatro columnas, una tarjeta en cada una. El tercer argumento de `metric` es el texto pequeño de debajo. `delta_color="off"` evita que el intervalo salga en verde o rojo como si fuera una subida o bajada.

```python
st.markdown(f"Una venta de **{producto}** deja de media **{eur(margen_medio)}**. "
            f"Cada contacto genera **{eur(res['beneficio'] / max(res['contactos'], 1))}**. "
            f"Probabilidad de pérdida: **{(sim < 0).mean() * 100:.1f} %**.")
```

Frase resumen. `(sim < 0).mean()` es la fracción de simulaciones con beneficio negativo.

## 6. Curva "¿Dónde parar?" y tabla por grupo

```python
col_a, col_b = st.columns([3, 2])

with col_a:
    cortes = list(range(0, 101, 5))
    curva = [evaluar(val, sc, margen_medio, nucleo, excluir, c, coste_contacto, coste_fijo) for c in cortes]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot([r["contactos"] for r in curva], [r["beneficio"] / 1e6 for r in curva], marker="o", color="grey")
    ax.scatter(res["contactos"], res["beneficio"] / 1e6, s=140, color="tab:green", zorder=5, label="Configuración actual")
    ...
    st.pyplot(fig)
```

Dos columnas de ancho 3 y 2. En la izquierda, se llama a `evaluar` 21 veces (top del resto = 0, 5, 10... 100) y se dibuja contactos frente a beneficio: es la tabla de la estrategia híbrida del notebook, en gráfico. El punto verde es la configuración actual. `st.pyplot(fig)` pinta una figura de matplotlib en la página.

```python
with col_b:
    comp = res["seleccion"]["nombre_grupo"].value_counts().rename("contactos").to_frame()
    conv_grupo = (aplicar_regla(val, nucleo, excluir, top_resto)
                  .groupby("nombre_grupo")["compra_real"].mean() * 100).round(2)
    comp["conversión %"] = conv_grupo.reindex(comp.index).fillna(0)
    comp["ventas esp."] = (comp["contactos"] * comp["conversión %"] / 100).round(0).astype(int)
    st.dataframe(comp, use_container_width=True)
```

En la derecha, la tabla de a quién contactamos: contactos por grupo (contados en la selección del scoring), conversión por grupo (medida en la selección de la validación) y ventas esperadas. `st.dataframe` pinta un DataFrame como tabla interactiva.

## 7. Histograma Monte Carlo y supuestos

```python
fig2, ax2 = plt.subplots(figsize=(10, 3))
ax2.hist(sim / 1e6, bins=60, color="tab:green", alpha=0.7)
for x in (p5, p95):
    ax2.axvline(x / 1e6, ls="--", color="black", lw=0.8)
st.pyplot(fig2)
st.caption(f"{n_sim:,} simulaciones. Conservador {eur(p5)} · base {eur(p50)} · optimista {eur(p95)}. ...")
```

Histograma de los beneficios simulados con dos líneas en los percentiles 5 y 95: el intervalo del 90%.

```python
with st.expander("Supuestos y limitaciones"):
    st.markdown("""...""")
```

Un bloque plegable con los avisos: un mes, ventas identificadas y no atribuibles, conversión de junio = conversión de mayo, costes como supuestos.

## Qué decir en la defensa si preguntan por la app

- **Qué es**: un producto de datos. El análisis vive en el notebook; la app lo convierte en algo que negocio puede usar sin un data scientist al lado.
- **Qué calcula**: exactamente lo mismo que el notebook 06 (mismas funciones). Los valores por defecto reproducen la recomendación: 80.282 contactos, 14,3 M€, intervalo 13,6–15,0.
- **Por qué mide en validación y aplica en scoring**: la validación (mayo) tiene compra real y sirve para medir; el scoring (junio) es la lista de la campaña. Mezclarlos sería usar el futuro para medir.
- **Qué aporta frente a unas slides**: Carol puede hacerse preguntas que no le hemos respondido ("¿y si excluyo a los universitarios?", "¿y por teléfono?") y ver el efecto en segundos, con intervalo de confianza.
- **Limitaciones**: hereda las del análisis (un mes, incrementalidad no medida). La app las muestra en el bloque de supuestos.