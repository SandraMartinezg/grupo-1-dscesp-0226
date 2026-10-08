# Caso easyMoney — TFM Data Science & AI

Trabajo Fin de Máster · Nuclio Digital School · Grupo 1

easyMoney es una fintech ficticia que quiere dejar de centrarse en captar clientes nuevos y empezar a vender más a los que ya tiene (**cross-selling**). Con 17 meses de datos de clientes y ventas (enero 2018 – mayo 2019), el proyecto responde a cuatro encargos encadenados de la dirección: qué ha pasado, a quién ofrecer cada producto, quiénes son nuestros clientes y cuánto podemos ganar con una campaña.

## Las cuatro tareas

| Tarea | Pregunta de negocio | Enfoque | Notebook |
|---|---|---|---|
| **1. Dashboard** | ¿Qué hemos vendido, a quién y dónde está el margen? | Limpieza y unión de las 5 tablas en Python; cuadro de mando en Power BI (ventas y clientes) | `00_powerbi_limpieza` |
| **2. Propensión** | ¿A qué clientes ofrecer cada producto? | Panel cliente-mes con variables del mes anterior; comparación de 4 modelos (regresión logística, árbol de decisión, Random Forest y Gradient Boosting) para `pension_plan` y `em_acount`; scoring para junio 2019 | `02_tarea2_propension` |
| **3. Segmentación** | ¿Quiénes son nuestros clientes? | Clientes sin producto aparte + K-Means (k=7) sobre el resto → 8 grupos con nombre y perfil comercial | `03_tarea3_segmentacion` |
| **4. Impacto económico** | ¿A cuántos contactar y cuánto podemos ganar? | Cruce de propensión y segmentación; conversión medida con compras reales; simulación Monte Carlo del beneficio; simulador interactivo en Streamlit | `04_tarea4_impacto_economico` + `app/` |

## Resultados clave

- **El dinero está en los planes de pensiones:** son el 8 % de las ventas pero generan el 79 % del margen. Cada plan deja de media unos 6.000 €; la cuenta easyMoney, unos 70 €.
- **El modelo de propensión encuentra a los compradores:** en el 5 % de clientes con mayor probabilidad, la conversión real de mayo 2019 es 13 veces la media en `pension_plan` y 10 veces en `em_acount`.
- **La segmentación dice dónde parar:** quien tiene la nómina domiciliada compra planes de pensiones unas 20 veces más que la media; tres grupos (74 % de la base) casi no compran.
- **Campaña propuesta para `pension_plan`:** contactar a todos los clientes de los grupos con nómina o tarjeta y, del resto de grupos con potencial, solo al 20 % con mejor nota del modelo. Son unos **62.200 clientes**, con una conversión del **3,7 %** frente al 0,66 % al azar y unas **2.300 ventas**: el 93 % de las ventas que conseguiría el modelo solo, con la mitad de contactos.
- **Beneficio estimado:** unos 13,7 M€ en un mes (entre 13,0 y 14,4 M€ con un 90 % de probabilidad), con supuestos de coste por contacto. Se recomienda validarlo con una prueba de un mes con grupo de control.

## Pipeline

```
                    ┌─► 00_powerbi_limpieza ──► df_powerbi.csv ──► Power BI (Tarea 1)
                    │
CSV en bruto ───────┤                        ┌─► 02_tarea2_propension ────┐
(data/raw)          │                        │                            │
                    └─► 01_base_comun ───────┼─► 03_tarea3_segmentacion ──┼─► 04_tarea4_impacto_economico ──► data/app ──► app/simulador.py
                                             │                            │
                                             └─────── (ventas limpias) ───┘
```

Toda la limpieza e imputación de la parte de modelado se hace **una sola vez** en `01_base_comun`. Cada tarea construye después sus propias variables a partir de esa base común. El dashboard de Power BI tiene su propia rama de limpieza (`00`), independiente del resto.

| Archivo | Generado por | Usado por |
|---|---|---|
| `data/processed/df_powerbi.csv` | 00 | Power BI |
| `data/processed/df_panel_limpio.parquet` | 01 | 02, 03 |
| `data/processed/df_sales_limpio.parquet` | 01 | 04 |
| `data/processed/scoring_{producto}.csv` | 02 | 04 |
| `data/processed/validacion_{producto}.csv` | 02 | 04 |
| `data/processed/comparacion_modelos_{producto}.csv`, `lift_{producto}.csv` | 02 | Consulta |
| `data/processed/clientes_grupos_abril.csv` | 03 | 04 (medir conversión de mayo) |
| `data/processed/clientes_grupos.csv` | 03 | 04 (lista de la campaña de junio) |
| `data/app/*.csv` | 04 | `app/simulador.py` |

`{producto}` es `pension_plan` o `em_acount`.

## Estructura del repositorio

```
grupo-1-dscesp-0226/
├── app/
│   ├── simulador.py        Simulador de campaña (Streamlit)
│   ├── requirements.txt
│   ├── README.md
│   └── assets/logo.png
├── data/
│   ├── raw/                CSV originales + diccionario de variables (no incluidos)
│   ├── processed/          Salidas de los notebooks (se regeneran al ejecutarlos)
│   └── app/                Datos ligeros que lee el simulador (incluidos)
├── docs/
│   └── Enunciado_TFM.pdf
├── notebooks/
│   ├── 00_powerbi_limpieza.ipynb
│   ├── 01_base_comun.ipynb
│   ├── 02_tarea2_propension.ipynb
│   ├── 03_tarea3_segmentacion.ipynb
│   └── 04_tarea4_impacto_economico.ipynb
├── powerbi/
│   └── Dashboard_EasyMoney.pbix
├── Presentación/
│   └── easyMoney — Propuesta de campaña.pptx
└── README.md
```

## Datos

Los CSV originales no se incluyen por tamaño (unos 950 MB). Para reproducir el proyecto, coloca en `data/raw/`:

- `sales.csv`
- `customer_sociodemographics.csv`
- `customer_commercial_activity.csv`
- `customer_products.csv`
- `product_description.csv`
- `diccionario_tablas.xlsx`

Los datos de `data/app/` sí se incluyen, para que el simulador funcione sin ejecutar antes los notebooks.

## Cómo reproducirlo

**Entorno.** Python 3.9 con `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn` y `pyarrow`.

**Notebooks.** Ejecutar en orden: `01` → `02` → `03` → `04`. El `02` y el `03` solo dependen del `01` y pueden ejecutarse en cualquier orden entre ellos; el `04` necesita los dos. El `00` es independiente y solo hace falta para el dashboard. Las rutas son relativas a la carpeta `notebooks/`, así que hay que abrirlos desde ahí.

**Power BI.** `powerbi/Dashboard_EasyMoney.pbix` lee `data/processed/df_powerbi.csv` (separador `;`, decimal `,`). Al abrirlo en otro equipo hay que actualizar la ruta del origen de datos.

**Simulador.** Desde la raíz del repositorio:

```bash
pip install -r app/requirements.txt
streamlit run app/simulador.py
```

Más detalle en [`app/README.md`](app/README.md).

## Nota sobre nombres de variables

`em_acount` (sin la segunda "c") es la grafía oficial del diccionario de variables y se mantiene así en todo el proyecto.
