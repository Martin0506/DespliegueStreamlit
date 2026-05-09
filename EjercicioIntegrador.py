import streamlit as st
import pandas as pd
import plotly.express as px
import altair as alt
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

# ------------------------------------------------------------
# Configuración de la página
# ------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Financiero Corporativo",
    layout="wide"
)

st.title("Dashboard financiero corporativo")
st.write(
    "Aplicación de inteligencia de negocios para analizar la rentabilidad operativa "
    "y neta de las unidades de negocio de un grupo financiero. "
    "**Pregunta orientadora:** ¿Qué unidades de negocio presentan mayor rentabilidad operativa "
    "y cómo evoluciona su desempeño a lo largo del tiempo?"
)

# ------------------------------------------------------------
# Carga y transformación de datos
# ------------------------------------------------------------
@st.cache_data
def cargar_datos(archivo):
    df = pd.read_csv(archivo)
    df["periodo"] = pd.to_datetime(df["periodo"])
    df["utilidad_bruta"] = df["ingresos"] - df["costos"]
    df["utilidad_operativa"] = df["utilidad_bruta"] - df["gastos_operativos"]
    df["utilidad_neta"] = df["utilidad_operativa"] - df["gastos_financieros"] - df["impuestos"]
    df["margen_bruto"] = df["utilidad_bruta"] / df["ingresos"]
    df["margen_operativo"] = df["utilidad_operativa"] / df["ingresos"]
    df["margen_neto"] = df["utilidad_neta"] / df["ingresos"]
    df["mes"] = df["periodo"].dt.to_period("M").astype(str)
    return df

archivo = st.file_uploader("Cargar archivo CSV", type=["csv"])

if archivo is not None:
    datos = cargar_datos(archivo)
    st.success("Archivo cargado correctamente.")
else:
    datos = cargar_datos("finanzas_corporativas.csv")
    st.info("Usando datos de ejemplo: finanzas_corporativas.csv")

# Validación de columnas requeridas
columnas_requeridas = [
    "periodo", "unidad_negocio", "region",
    "ingresos", "costos", "gastos_operativos", "gastos_financieros", "impuestos"
]
faltantes = [col for col in columnas_requeridas if col not in datos.columns]

if faltantes:
    st.error(f"Faltan columnas requeridas: {faltantes}")
    st.stop()

# ------------------------------------------------------------
# Filtros en barra lateral
# ------------------------------------------------------------
st.sidebar.header("Filtros")

unidades = ["Todas"] + sorted(datos["unidad_negocio"].unique())
regiones = ["Todas"] + sorted(datos["region"].unique())

unidad = st.sidebar.selectbox("Unidad de negocio", unidades)
region = st.sidebar.selectbox("Región", regiones)

meses_disponibles = sorted(datos["mes"].unique())
mes_inicio = st.sidebar.selectbox("Periodo inicial", meses_disponibles, index=0)
mes_fin = st.sidebar.selectbox("Periodo final", meses_disponibles, index=len(meses_disponibles) - 1)

# ------------------------------------------------------------
# Aplicar filtros
# ------------------------------------------------------------
datos_filtrados = datos.copy()

if unidad != "Todas":
    datos_filtrados = datos_filtrados[datos_filtrados["unidad_negocio"] == unidad]

if region != "Todas":
    datos_filtrados = datos_filtrados[datos_filtrados["region"] == region]

datos_filtrados = datos_filtrados[
    (datos_filtrados["mes"] >= mes_inicio) &
    (datos_filtrados["mes"] <= mes_fin)
]

if datos_filtrados.empty:
    st.warning("No hay datos para los filtros seleccionados.")
    st.stop()

# ------------------------------------------------------------
# Cálculo de indicadores agregados
# ------------------------------------------------------------
ingresos_total = datos_filtrados["ingresos"].sum()
utilidad_bruta_total = datos_filtrados["utilidad_bruta"].sum()
utilidad_op_total = datos_filtrados["utilidad_operativa"].sum()
utilidad_neta_total = datos_filtrados["utilidad_neta"].sum()
margen_op = utilidad_op_total / ingresos_total if ingresos_total > 0 else 0
margen_neto = utilidad_neta_total / ingresos_total if ingresos_total > 0 else 0

# ------------------------------------------------------------
# Indicadores principales
# ------------------------------------------------------------
st.subheader("Indicadores del periodo seleccionado")

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Ingresos totales", f"$ {ingresos_total / 1e9:.2f} B")
with col2:
    st.metric("Utilidad bruta", f"$ {utilidad_bruta_total / 1e9:.2f} B")
with col3:
    st.metric("Utilidad operativa", f"$ {utilidad_op_total / 1e9:.2f} B")
with col4:
    st.metric("Utilidad neta", f"$ {utilidad_neta_total / 1e9:.2f} B")
with col5:
    st.metric("Margen operativo", f"{margen_op:.2%}")
with col6:
    st.metric("Margen neto", f"{margen_neto:.2%}")

# ------------------------------------------------------------
# Pestañas de análisis
# ------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["Evolución", "Rentabilidad", "Estructura de costos", "Datos"])

# ---- TAB 1: Evolución temporal ----
with tab1:
    st.subheader("Evolución mensual de ingresos y utilidad operativa")

    eje_color = "unidad_negocio" if unidad == "Todas" else "region"

    evolucion = (
        datos_filtrados
        .groupby(["mes", eje_color], as_index=False)[["ingresos", "utilidad_operativa", "utilidad_neta"]]
        .sum()
    )

    fig_ing = px.line(
        evolucion,
        x="mes", y="ingresos", color=eje_color,
        markers=True,
        title="Evolución mensual de ingresos",
        labels={"mes": "Periodo", "ingresos": "Ingresos ($)", eje_color: eje_color.replace("_", " ").title()}
    )
    st.plotly_chart(fig_ing, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        fig_op = px.line(
            evolucion,
            x="mes", y="utilidad_operativa", color=eje_color,
            markers=True,
            title="Utilidad operativa mensual",
            labels={"mes": "Periodo", "utilidad_operativa": "Utilidad operativa ($)"}
        )
        st.plotly_chart(fig_op, use_container_width=True)

    with col_b:
        fig_neta = px.line(
            evolucion,
            x="mes", y="utilidad_neta", color=eje_color,
            markers=True,
            title="Utilidad neta mensual",
            labels={"mes": "Periodo", "utilidad_neta": "Utilidad neta ($)"}
        )
        st.plotly_chart(fig_neta, use_container_width=True)

    st.markdown(
        "**Lectura analítica:** La tendencia creciente de ingresos no siempre se traduce en "
        "mejoras proporcionales de utilidad. Una brecha creciente entre ingresos y utilidad "
        "operativa señala incremento en gastos operativos que debe gestionarse. Las unidades "
        "con margen estable o en expansión son las más sólidas para sostener el crecimiento."
    )

# ---- TAB 2: Rentabilidad por unidad ----
with tab2:
    st.subheader("Comparación de rentabilidad por unidad de negocio")

    rentabilidad = (
        datos_filtrados
        .groupby("unidad_negocio", as_index=False)
        .agg(
            ingresos=("ingresos", "sum"),
            utilidad_operativa=("utilidad_operativa", "sum"),
            utilidad_neta=("utilidad_neta", "sum"),
        )
    )
    rentabilidad["margen_operativo"] = rentabilidad["utilidad_operativa"] / rentabilidad["ingresos"]
    rentabilidad["margen_neto"] = rentabilidad["utilidad_neta"] / rentabilidad["ingresos"]
    rentabilidad["margen_op_pct"] = rentabilidad["margen_operativo"] * 100
    rentabilidad["margen_neto_pct"] = rentabilidad["margen_neto"] * 100

    col_c, col_d = st.columns(2)

    with col_c:
        grafico_margen_op = (
            alt.Chart(rentabilidad)
            .mark_bar()
            .encode(
                x=alt.X("margen_op_pct:Q", title="Margen operativo (%)"),
                y=alt.Y("unidad_negocio:N", sort="-x", title="Unidad de negocio"),
                color=alt.Color("unidad_negocio:N", legend=None),
                tooltip=[
                    alt.Tooltip("unidad_negocio:N", title="Unidad"),
                    alt.Tooltip("margen_op_pct:Q", title="Margen operativo (%)", format=".2f")
                ]
            )
            .properties(title="Margen operativo por unidad de negocio")
        )
        st.altair_chart(grafico_margen_op, use_container_width=True)

    with col_d:
        grafico_margen_neto = (
            alt.Chart(rentabilidad)
            .mark_bar()
            .encode(
                x=alt.X("margen_neto_pct:Q", title="Margen neto (%)"),
                y=alt.Y("unidad_negocio:N", sort="-x", title="Unidad de negocio"),
                color=alt.Color("unidad_negocio:N", legend=None),
                tooltip=[
                    alt.Tooltip("unidad_negocio:N", title="Unidad"),
                    alt.Tooltip("margen_neto_pct:Q", title="Margen neto (%)", format=".2f")
                ]
            )
            .properties(title="Margen neto por unidad de negocio")
        )
        st.altair_chart(grafico_margen_neto, use_container_width=True)

    st.subheader("Comparación de ingresos vs utilidad operativa por unidad")

    fig_scatter = px.scatter(
        rentabilidad,
        x="ingresos", y="utilidad_operativa",
        size="utilidad_neta", color="unidad_negocio",
        text="unidad_negocio",
        title="Ingresos vs Utilidad operativa (tamaño = Utilidad neta)",
        labels={
            "ingresos": "Ingresos ($)",
            "utilidad_operativa": "Utilidad operativa ($)",
            "unidad_negocio": "Unidad"
        }
    )
    fig_scatter.update_traces(textposition="top center")
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown(
        "**Lectura analítica:** Las unidades con mayor margen operativo son las más eficientes "
        "en transformar ingresos en rentabilidad antes de gastos financieros e impuestos. "
        "La diferencia entre margen operativo y margen neto revela el peso de la deuda y "
        "la carga tributaria. Unidades con alto margen operativo pero bajo margen neto pueden "
        "tener una estructura financiera que merece revisión estratégica."
    )

# ---- TAB 3: Estructura de costos ----
with tab3:
    st.subheader("Estructura de costos y gastos por unidad de negocio")

    estructura = (
        datos_filtrados
        .groupby("unidad_negocio", as_index=False)
        .agg(
            costos=("costos", "sum"),
            gastos_operativos=("gastos_operativos", "sum"),
            gastos_financieros=("gastos_financieros", "sum"),
            impuestos=("impuestos", "sum"),
            ingresos=("ingresos", "sum")
        )
    )

    # Gráfico apilado con Matplotlib
    fig_est, ax = plt.subplots(figsize=(10, 5))
    unidades_nombres = estructura["unidad_negocio"].tolist()
    x = range(len(unidades_nombres))
    width = 0.5

    b1 = ax.bar(x, estructura["costos"] / 1e9, width, label="Costos", color="#4C72B0")
    b2 = ax.bar(x, estructura["gastos_operativos"] / 1e9, width,
                bottom=estructura["costos"] / 1e9, label="Gastos operativos", color="#DD8452")
    b3 = ax.bar(x, estructura["gastos_financieros"] / 1e9, width,
                bottom=(estructura["costos"] + estructura["gastos_operativos"]) / 1e9,
                label="Gastos financieros", color="#55A868")
    b4 = ax.bar(x, estructura["impuestos"] / 1e9, width,
                bottom=(estructura["costos"] + estructura["gastos_operativos"] + estructura["gastos_financieros"]) / 1e9,
                label="Impuestos", color="#C44E52")

    ax.plot(x, estructura["ingresos"] / 1e9, "D--k", label="Ingresos", zorder=5)

    ax.set_xticks(list(x))
    ax.set_xticklabels(unidades_nombres, rotation=15, ha="right")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda val, _: f"$ {val:.1f} B"))
    ax.set_title("Estructura de costos y gastos vs ingresos por unidad (en miles de millones)")
    ax.set_ylabel("Monto (miles de millones $)")
    ax.legend(loc="upper left")
    plt.tight_layout()
    st.pyplot(fig_est)

    st.subheader("Participación porcentual de cada componente sobre los ingresos")

    estructura_pct = estructura.copy()
    for col in ["costos", "gastos_operativos", "gastos_financieros", "impuestos"]:
        estructura_pct[col] = estructura_pct[col] / estructura_pct["ingresos"] * 100

    estructura_long = estructura_pct[["unidad_negocio", "costos", "gastos_operativos", "gastos_financieros", "impuestos"]].melt(
        id_vars="unidad_negocio", var_name="componente", value_name="porcentaje"
    )
    etiquetas = {
        "costos": "Costos",
        "gastos_operativos": "Gastos operativos",
        "gastos_financieros": "Gastos financieros",
        "impuestos": "Impuestos"
    }
    estructura_long["componente"] = estructura_long["componente"].map(etiquetas)

    grafico_pct = (
        alt.Chart(estructura_long)
        .mark_bar()
        .encode(
            x=alt.X("unidad_negocio:N", title="Unidad de negocio"),
            y=alt.Y("porcentaje:Q", title="% sobre ingresos", stack="zero"),
            color=alt.Color("componente:N", title="Componente"),
            tooltip=[
                alt.Tooltip("unidad_negocio:N", title="Unidad"),
                alt.Tooltip("componente:N", title="Componente"),
                alt.Tooltip("porcentaje:Q", title="% sobre ingresos", format=".1f")
            ]
        )
        .properties(title="Participación de cada componente sobre los ingresos (%)")
    )
    st.altair_chart(grafico_pct, use_container_width=True)

    st.markdown(
        "**Lectura analítica:** La estructura de costos revela la eficiencia operativa de cada unidad. "
        "Una participación elevada de costos directos puede indicar baja productividad o presión "
        "en márgenes brutos. Los gastos financieros como proporción de ingresos señalan el nivel "
        "de apalancamiento: valores altos pueden comprometer la sostenibilidad si los ingresos caen. "
        "Las unidades con mejor estructura son aquellas donde la suma de todos los componentes "
        "deja mayor espacio para la utilidad neta."
    )

# ---- TAB 4: Datos ----
with tab4:
    st.subheader("Datos filtrados")
    st.dataframe(
        datos_filtrados[[
            "mes", "unidad_negocio", "region", "ingresos", "costos",
            "gastos_operativos", "gastos_financieros", "impuestos",
            "utilidad_bruta", "utilidad_operativa", "utilidad_neta",
            "margen_operativo", "margen_neto"
        ]].rename(columns={
            "mes": "Periodo",
            "unidad_negocio": "Unidad de negocio",
            "region": "Región",
            "ingresos": "Ingresos ($)",
            "costos": "Costos ($)",
            "gastos_operativos": "Gastos operativos ($)",
            "gastos_financieros": "Gastos financieros ($)",
            "impuestos": "Impuestos ($)",
            "utilidad_bruta": "Utilidad bruta ($)",
            "utilidad_operativa": "Utilidad operativa ($)",
            "utilidad_neta": "Utilidad neta ($)",
            "margen_operativo": "Margen operativo",
            "margen_neto": "Margen neto"
        }),
        use_container_width=True
    )
