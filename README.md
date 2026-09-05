# Caso easyMoney — TFM Data Science & AI

Trabajo Final de Máster · Nuclio Digital School · Sandra Martínez

Proyecto de analítica y machine learning sobre los datos de easyMoney, una fintech ficticia que quiere pasar de una estrategia de captación a una de **cross-selling** sobre su base de clientes. El trabajo se desarrolla en el rol de Data Scientist ("Bob") y responde a cuatro encargos encadenados de la dirección.

## Las cuatro tareas

| Tarea | Pregunta de negocio | Enfoque | Estado |
|---|---|---|---|
| **1. Dashboard** | ¿Qué hemos vendido, a quién y dónde está el margen? | Limpieza y unión de las 5 tablas en Python; dashboard de 5 páginas en Power BI | Cerrada |
| **2. Propensión** | ¿A qué clientes ofrecer cada producto? | Random Forest sobre panel cliente-mes con features lag-1; scoring para `pension_plan` y `em_acount` | Cerrada |
| **3. Segmentación** | ¿Quiénes son nuestros clientes? | Regla de negocio + K-Means (k=7) → 8 grupos con nombre y oportunidad comercial | Cerrada |
| **4. Impacto económico** | ¿Cuánto podemos ganar con la campaña? | Cruce de segmentación y propensión para estimar ventas y margen por grupo | Pendiente |

Resultados clave hasta ahora:

- `pension_plan` genera el 79 % del margen con solo el 8 % de las ventas.
- Contactando al 5 % de clientes con mayor propensión, la conversión se multiplica por **7,7** en `pension_plan` y por **10,2** en `em_acount` frente a contactar al azar.
- Los 442.995 clientes de la base actual se agrupan en 8 perfiles; tres de ellos (7 % de la base) concentran la mayor parte del margen, y prácticamente todos los planes de pensiones están en un único grupo.

## Estructura del repositorio

```
grupo-1-dscesp-0226/
├── data/
│   ├── raw/            CSVs originales + diccionario de variables (no versionados)
│   └── processed/      Archivos generados por los notebooks (no versionados)
├── notebooks/
│   ├── 01_tarea1_limpieza.ipynb
│   ├── 02_tarea2_preprocessing_propension.ipynb
│   ├── 03_tarea2_modelling_pension_plan.ipynb
│   ├── 04_tarea2_modelling_em_acount.ipynb
│   ├── 05_tarea3_segmentacion.ipynb
│   └── obsoletos/      Versiones de prueba (no versionadas)
├── powerbi/
│   └── easymoney_dashboard.pbix
├── docs/
│   ├── Enunciado_TFM.pdf
│   └── Tarea2_Justificacion_Propension.docx
├── README.md
└── .gitignore
```

## Datos

Los datos no se incluyen en el repositorio por tamaño. Para reproducir el proyecto, coloca en `data/raw/` los cinco CSVs originales y el diccionario:

- `sales.csv`
- `customer_sociodemographics.csv`
- `customer_commercial_activity.csv`
- `customer_products.csv`
- `product_description.csv`
- `diccionario_tablas.xlsx`

Los notebooks escriben sus salidas en `data/processed/`:

| Archivo | Generado por | Usado por |
|---|---|---|
| `df_powerbi.csv` | 01 | Power BI |
| `df_panel_propension.parquet` | 02 | 03, 04 |
| `scoring_pension_plan.csv` | 03 | Tarea 4 |
| `scoring_em_acount.csv` | 04 | Tarea 4 |
| `clientes_grupos.csv` | 05 | Tarea 4 |

## Cómo ejecutar

Python 3.9 con `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `seaborn` y `pyarrow`.

Los notebooks están numerados en el orden de ejecución. El 01 y el 05 son independientes entre sí; el 03 y el 04 necesitan el parquet que genera el 02. Todas las rutas son relativas a la carpeta `notebooks/`, así que hay que abrirlos desde ahí (o desde la raíz del repo en VS Code).

El dashboard de Power BI lee `data/processed/df_powerbi.csv`; al abrirlo por primera vez en otro equipo hay que actualizar la ruta del origen de datos.

## Nota sobre nombres de variables

`em_acount` (sin la segunda "c") es la grafía oficial del diccionario de variables y se mantiene así en todo el proyecto.
