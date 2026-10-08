# easyMoney · Simulador de campaña (Tarea 4)

App de Streamlit que combina el modelo de propensión (Tarea 2) y la segmentación (Tarea 3) para que negocio pueda simular una campaña de cross-selling y ver al momento su resultado económico, con intervalo de confianza.

## Ejecutar

Desde la raíz del repositorio, con Python 3.9:

```bash
pip install -r app/requirements.txt
streamlit run app/simulador.py
```

## Qué se puede decidir (barra lateral)

- **Producto:** `pension_plan` o `em_acount`.
- **Canal / coste por contacto:** de 0,10 € (push o email) a 60 €, más un coste fijo de campaña.
- **Qué hacer con cada grupo de la Tarea 3:** contactar a *todos*, solo al *top del modelo* o *excluir*. La propuesta inicial sale de la conversión real de cada grupo en validación, con la misma regla que el notebook 04: *todos* si convierte al menos el doble de la media (con un mínimo de 30 compras), *excluir* si convierte menos de la mitad y *top del modelo* en el resto.
- **Corte del modelo:** en los grupos de *top del modelo*, qué porcentaje de clientes con mejor nota se contacta (por defecto, el 20 %).
- **Número de simulaciones** Monte Carlo.

Con los valores por defecto, la app reproduce la campaña recomendada en el notebook 04.

## Qué muestra

- **Tarjetas:** clientes contactados, ventas esperadas y conversión, coste de la campaña y beneficio neto con su intervalo del 90 %.
- **¿Dónde parar?:** beneficio según cuántos clientes del resto se añaden (del 0 % al 50 % del modelo, de 5 en 5). El punto verde es la configuración actual.
- **A quién contactamos:** contactos, conversión y ventas esperadas por grupo.
- **Intervalo de confianza:** distribución del beneficio en las simulaciones, con los escenarios conservador (p5), base (p50) y optimista (p95).
- **Supuestos y limitaciones**, en un bloque desplegable.

## Cómo calcula

La lógica es la misma que la del notebook 04:

1. La regla de selección se **mide** en validación (probabilidad con datos hasta abril, grupo de abril y compra real de mayo 2019) para obtener la conversión.
2. La misma regla se **aplica** al scoring (clientes de junio con su grupo de mayo) para saber a cuántos se contacta.
3. Beneficio = contactos × conversión × margen medio − coste.
4. **Monte Carlo:** en cada simulación, la conversión se muestrea de una Beta ajustada a las compras de validación, las ventas de una Binomial y el margen de las ventas reales del producto. Semilla fija para que sea reproducible.

Los nombres de los grupos no están escritos en el código: se leen de los datos.

## Datos que necesita

Los CSV de `data/app/`, que genera la última sección de `notebooks/04_tarea4_impacto_economico.ipynb`:

| Archivo | Contenido |
|---|---|
| `validacion_grupo_{producto}.csv` | Probabilidad, compra real de mayo y grupo de abril de cada cliente |
| `scoring_grupo_{producto}.csv` | Probabilidad para junio y grupo de mayo de cada cliente elegible |
| `margenes_{producto}.csv` | Margen real de cada venta del producto |

Si se reentrena algún modelo o la segmentación, basta con volver a ejecutar el notebook 04; el código de la app no cambia.

## Limitaciones

- La conversión se mide en un solo mes (mayo 2019) y se asume igual para la campaña.
- Los resultados son de un mes y no se anualizan.
- Son ventas que el modelo identifica, no necesariamente atribuibles a la campaña: para medir el efecto real hace falta un piloto con grupo de control.
- Los costes son supuestos de negocio, por eso se pueden cambiar en la barra lateral.
