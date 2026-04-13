import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import streamlit as st

from BMK_UL import (
    INSTITUTION_COLORS,
    STATE_CENTROIDS,
    geocode_campus_points,
    load_processed_snapshot,
    load_campo_amplio_result,
    normalize_campus_name,
    save_processed_snapshot,
    _normalize_text,
)


st.set_page_config(
    page_title="BMK UL",
    layout="wide",
)


LOGO_URL = "https://media.ulibertad.edu.mx/nimda/Umbraco/logo_ul_svg.svg"


st.markdown(
    f"""
    <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(194, 214, 255, 0.35), transparent 28%),
                linear-gradient(180deg, #f7f6f2 0%, #f1efe7 100%);
        }}

        .block-container {{
            padding-top: 0;
        }}

        .ul-header {{
            width: 100%;
            background: #000000;
            min-height: 110px;
            padding: 18px 28px;
            border-radius: 0 0 18px 18px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-sizing: border-box;
            margin-bottom: 28px;
        }}

        .ul-header img {{
            height: 56px;
            width: auto;
            display: block;
            flex-shrink: 0;
            filter: brightness(0) invert(1);
        }}

        .ul-header-text {{
            color: #ffffff;
            line-height: 1.1;
        }}

        .ul-header-text h1 {{
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
        }}

        .ul-header-text p {{
            margin: 6px 0 0 0;
            font-size: 0.95rem;
            color: #d6d6d6;
        }}

        .hero-card {{
            background: rgba(255, 255, 255, 0.78);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 22px;
            padding: 1.4rem 1.4rem 1.1rem;
            box-shadow: 0 20px 50px rgba(15, 23, 42, 0.08);
            margin-bottom: 1rem;
        }}

        .hero-card h2 {{
            margin: 0 0 0.4rem 0;
            font-size: 1.8rem;
            color: #101828;
        }}

        .hero-card p {{
            margin: 0;
            color: #475467;
            max-width: 900px;
        }}

        @media (max-width: 768px) {{
            .ul-header {{
                padding: 16px 18px;
                min-height: 90px;
                gap: 14px;
            }}

            .ul-header img {{
                height: 44px;
            }}

            .ul-header-text h1 {{
                font-size: 1.45rem;
            }}
        }}
    </style>

    <div class="ul-header">
        <img src="{LOGO_URL}" alt="Universidad Libertad">
        <div class="ul-header-text">
            <h1>BMK UL</h1>
            <p>Benchmark y analisis de datos</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
        .institution-card {
            background: rgba(255, 255, 255, 0.82);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: 0 14px 32px rgba(15, 23, 42, 0.06);
            min-height: 132px;
        }

        .institution-card .inst-type {
            color: #7a7a7a;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }

        .institution-card .inst-name {
            color: #111827;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 0.8rem;
        }

        .institution-card .inst-metric {
            color: #1f2937;
            font-size: 0.9rem;
            margin-bottom: 0.2rem;
        }

        .institution-card .inst-metric strong {
            font-size: 1.05rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero-card">
        <h2>Evolucion total de la matricula por institucion</h2>
        <p>
            Vista inicial del benchmark historico de ANUIES para universidades objetivo.
            La grafica suma la matricula total de cada institucion por ciclo escolar.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


DATA_SCHEMA_VERSION = "campo_especifico_v2_entidad"
MEXICO_STATES_GEOJSON_URL = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"


@st.cache_data(show_spinner=False)
def load_dashboard_data(force_refresh: bool, schema_version: str) -> dict:
    if not force_refresh:
        snapshot_raw_df, snapshot_points_df = load_processed_snapshot()
        if not snapshot_raw_df.empty:
            summary_df = (
                snapshot_raw_df.groupby(
                    ["universidad_objetivo", "ciclo_inicio", "ciclo"],
                    as_index=False,
                )["matricula_total"]
                .sum()
                .sort_values(["ciclo_inicio", "universidad_objetivo"])
            )
            return {
                "raw_df": snapshot_raw_df.to_dict(orient="records"),
                "chart_df": summary_df.to_dict(orient="records"),
                "campus_points_df": snapshot_points_df.to_dict(orient="records"),
                "matched": sorted(snapshot_raw_df["universidad_objetivo"].dropna().unique().tolist()),
                "missing": [],
                "data_source": "snapshot",
            }

    result = load_campo_amplio_result(use_cache=True, force_refresh=force_refresh)
    campus_points_df = geocode_campus_points(
        result.raw_df,
        force_refresh=force_refresh,
        allow_online=force_refresh,
    )
    save_processed_snapshot(result.raw_df, campus_points_df)
    return {
        "raw_df": result.raw_df.to_dict(orient="records"),
        "chart_df": result.chart_df.to_dict(orient="records"),
        "campus_points_df": campus_points_df.to_dict(orient="records"),
        "matched": result.matched_universities,
        "missing": result.missing_universities,
        "data_source": "anuies",
    }


@st.cache_data(show_spinner=False)
def load_mexico_geojson() -> dict:
    response = requests.get(MEXICO_STATES_GEOJSON_URL, timeout=30)
    response.raise_for_status()
    geojson = response.json()

    for feature in geojson.get("features", []):
        props = feature.setdefault("properties", {})
        raw_name = props.get("name", "")
        normalized_name = _normalize_text(raw_name)
        if normalized_name == "DISTRITO FEDERAL":
            normalized_name = "CIUDAD DE MEXICO"
        props["normalized_name"] = normalized_name

    return geojson

with st.sidebar:
    st.subheader("Controles")
    refresh = st.button("Actualizar desde ANUIES", use_container_width=True)

try:
    payload = load_dashboard_data(
        force_refresh=refresh,
        schema_version=DATA_SCHEMA_VERSION,
    )
    mexico_geojson = load_mexico_geojson()
except Exception as exc:
    st.error(
        "No fue posible cargar ANUIES en este momento. "
        f"Detalle tecnico: {exc}"
    )
    st.stop()


raw_df = pd.DataFrame(payload["raw_df"])
chart_df = pd.DataFrame(payload["chart_df"])
campus_points_df = pd.DataFrame(payload.get("campus_points_df", []))
matched = payload["matched"]
missing = payload["missing"]
data_source = payload.get("data_source", "anuies")

if raw_df.empty or chart_df.empty:
    st.warning("No se encontraron registros para las universidades objetivo.")
    st.stop()

required_chart_columns = {"ciclo", "universidad_objetivo", "matricula_total"}
if not required_chart_columns.issubset(set(chart_df.columns)):
    st.error(
        "La estructura del cache del dashboard no coincide con la version actual. "
        "Haz clic en 'Actualizar desde ANUIES' o reinicia Streamlit."
    )
    st.stop()

institution_options = sorted(raw_df["universidad_objetivo"].dropna().unique().tolist())
institution_default = institution_options

with st.sidebar:
    selected_institutions = st.multiselect(
        "Institucion",
        options=institution_options,
        default=institution_default,
    )

    tipo_options = sorted(
        [
            value
            for value in raw_df["tipo_institucion"].dropna().astype(str).str.strip().unique().tolist()
            if value
        ]
    )
    with st.expander("Tipo de institucion", expanded=False):
        selected_tipos = st.multiselect(
            "Tipo de institucion",
            options=tipo_options,
            default=tipo_options,
            label_visibility="collapsed",
        )

    campo_options = sorted(
        [
            value
            for value in raw_df["campo_especifico"].dropna().astype(str).str.strip().unique().tolist()
            if value
        ]
    )
    with st.expander("Campo especifico", expanded=False):
        selected_campos = st.multiselect(
            "Campo especifico",
            options=campo_options,
            default=campo_options,
            label_visibility="collapsed",
        )

filtered_raw_df = raw_df.copy()
if selected_institutions:
    filtered_raw_df = filtered_raw_df.loc[
        filtered_raw_df["universidad_objetivo"].isin(selected_institutions)
    ]
if selected_tipos:
    filtered_raw_df = filtered_raw_df.loc[
        filtered_raw_df["tipo_institucion"].isin(selected_tipos)
    ]
if selected_campos:
    filtered_raw_df = filtered_raw_df.loc[
        filtered_raw_df["campo_especifico"].isin(selected_campos)
    ]

if filtered_raw_df.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

filtered_chart_df = (
    filtered_raw_df.groupby(
        ["universidad_objetivo", "ciclo_inicio", "ciclo"],
        as_index=False,
    )["matricula_total"]
    .sum()
    .sort_values(["ciclo_inicio", "universidad_objetivo"])
)

filtered_campus_points_df = campus_points_df.copy()
if not filtered_campus_points_df.empty:
    if selected_institutions:
        filtered_campus_points_df = filtered_campus_points_df.loc[
            filtered_campus_points_df["universidad_objetivo"].isin(selected_institutions)
        ]
    if selected_tipos and "tipo_institucion" in filtered_campus_points_df.columns:
        filtered_campus_points_df = filtered_campus_points_df.loc[
            filtered_campus_points_df["tipo_institucion"].isin(selected_tipos)
        ]
    if selected_campos and "campo_especifico" in filtered_campus_points_df.columns:
        filtered_campus_points_df = filtered_campus_points_df.loc[
            filtered_campus_points_df["campo_especifico"].isin(selected_campos)
        ]

figure = px.line(
    filtered_chart_df,
    x="ciclo",
    y="matricula_total",
    color="universidad_objetivo",
    markers=True,
    line_group="universidad_objetivo",
    color_discrete_sequence=px.colors.qualitative.Bold,
)
figure.update_layout(
    title="Matricula total por institucion",
    xaxis_title="Ciclo escolar",
    yaxis_title="Matricula total",
    legend_title="Institucion",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.72)",
    hovermode="x unified",
)
figure.update_traces(line=dict(width=3), marker=dict(size=8))

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Instituciones visibles", filtered_raw_df["universidad_objetivo"].nunique())
metric_2.metric("Instituciones sin match", len(missing))
metric_3.metric(
    "Observaciones totales",
    int(filtered_chart_df["matricula_total"].count()),
)

st.plotly_chart(figure, use_container_width=True)

if data_source == "snapshot":
    st.caption("Fuente actual: snapshot procesado incluido en el proyecto.")
else:
    st.caption("Fuente actual: consulta y procesamiento desde ANUIES.")

if missing:
    st.info("Sin match en ANUIES por ahora: " + ", ".join(missing))

gender_and_cards_left, gender_and_cards_right = st.columns([3, 7], vertical_alignment="top")

gender_summary = filtered_raw_df[["matricula_mujeres", "matricula_hombres"]].sum()
gender_df = pd.DataFrame(
    {
        "grupo": ["Mujeres", "Hombres"],
        "matricula": [
            float(gender_summary.get("matricula_mujeres", 0)),
            float(gender_summary.get("matricula_hombres", 0)),
        ],
    }
)

with gender_and_cards_left:
    pie_fig = px.pie(
        gender_df,
        names="grupo",
        values="matricula",
        color="grupo",
        color_discrete_map={"Mujeres": "#C95C7B", "Hombres": "#3D6D99"},
        hole=0.28,
    )
    pie_fig.update_layout(
        title="Distribucion de matricula por genero",
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title="",
    )
    st.plotly_chart(pie_fig, use_container_width=True)

campus_card_df = (
    filtered_raw_df[["universidad_objetivo", "tipo_institucion", "campus"]]
    .dropna()
    .assign(
        tipo_institucion=lambda df: df["tipo_institucion"].astype(str).str.strip(),
        campus=lambda df: df["campus"].astype(str).str.strip(),
        campus_normalizado=lambda df: df["campus"].map(normalize_campus_name),
    )
)
campus_card_df = campus_card_df.loc[campus_card_df["campus"] != ""]

institution_summary = (
    filtered_raw_df.groupby("universidad_objetivo", as_index=False)
    .agg(
        matricula_total=("matricula_total", "sum"),
        tipo_institucion=("tipo_institucion", lambda values: next((v for v in values if str(v).strip()), "")),
    )
    .merge(
        campus_card_df.groupby("universidad_objetivo", as_index=False).agg(
            campus_count=("campus_normalizado", "nunique")
        ),
        on="universidad_objetivo",
        how="left",
    )
    .fillna({"campus_count": 0})
    .sort_values("matricula_total", ascending=False)
)

with gender_and_cards_right:
    st.subheader("Resumen por institucion")
    card_columns = st.columns(3)
    for idx, (_, row) in enumerate(institution_summary.iterrows()):
        column = card_columns[idx % 3]
        with column:
            st.markdown(
                f"""
                <div class="institution-card">
                    <div class="inst-type">{row["tipo_institucion"]}</div>
                    <div class="inst-name">{row["universidad_objetivo"]}</div>
                    <div class="inst-metric">Matricula total: <strong>{int(row["matricula_total"]):,}</strong></div>
                    <div class="inst-metric">Campus unicos: <strong>{int(row["campus_count"])}</strong></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

map_left, map_right = st.columns([6, 2], vertical_alignment="top")
with map_left:
    st.subheader("Distribucion geografica de campus")
with map_right:
    map_mode = st.segmented_control(
        "Modo de mapa",
        options=["Heatmap por entidad", "Bubble map campus"],
        default="Heatmap por entidad",
        label_visibility="collapsed",
    )

if {"entidad", "campus", "universidad_objetivo"}.issubset(filtered_raw_df.columns):
    campus_state_df = (
        filtered_raw_df[["universidad_objetivo", "entidad", "campus"]]
        .dropna()
        .assign(
            entidad=lambda df: df["entidad"].astype(str).str.strip(),
            campus=lambda df: df["campus"].astype(str).str.strip(),
            campus_normalizado=lambda df: df["campus"].map(normalize_campus_name),
        )
    )
    campus_state_df = campus_state_df.loc[
        (campus_state_df["entidad"] != "") & (campus_state_df["campus"] != "")
    ].drop_duplicates(subset=["universidad_objetivo", "entidad", "campus_normalizado"])

    state_counts = (
        campus_state_df.groupby("entidad", as_index=False)
        .agg(
            campus_count=("campus_normalizado", "nunique"),
            instituciones=("universidad_objetivo", lambda values: ", ".join(sorted(set(values)))),
            campus_list=("campus", lambda values: ", ".join(sorted(set(values))[:12])),
        )
    )
    state_counts["entidad_normalizada"] = state_counts["entidad"].map(_normalize_text).replace(
        {"CIUDAD DE MEXICO": "CIUDAD DE MEXICO"}
    )

    centroids_df = pd.DataFrame(
        [
            {"entidad_normalizada": state, "lat": coords["lat"], "lon": coords["lon"]}
            for state, coords in STATE_CENTROIDS.items()
        ]
    )
    state_map_df = state_counts.merge(centroids_df, on="entidad_normalizada", how="left")

    if map_mode == "Heatmap por entidad":
        heatmap_fig = px.choropleth_map(
            state_map_df,
            geojson=mexico_geojson,
            locations="entidad_normalizada",
            featureidkey="properties.normalized_name",
            color="campus_count",
            color_continuous_scale="YlOrRd",
            hover_name="entidad",
            hover_data={
                "campus_count": True,
                "instituciones": True,
                "campus_list": True,
            },
            center=dict(lat=23.5, lon=-102.0),
            zoom=4.2,
            opacity=0.72,
        )
        heatmap_fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            map_style="carto-positron",
            coloraxis_colorbar_title="Campus",
        )
        st.plotly_chart(heatmap_fig, use_container_width=True)
    else:
        bubble_df = filtered_campus_points_df.copy()
        bubble_fig = px.choropleth_map(
            state_map_df,
            geojson=mexico_geojson,
            locations="entidad_normalizada",
            featureidkey="properties.normalized_name",
            color="campus_count",
            color_continuous_scale="YlOrRd",
            hover_name="entidad",
            hover_data={
                "campus_count": True,
                "instituciones": True,
                "campus_list": False,
            },
            center={"lat": 23.5, "lon": -102.0},
            zoom=4.2,
            opacity=0.35,
        )
        if not bubble_df.empty:
            for institution, institution_df in bubble_df.groupby("universidad_objetivo"):
                bubble_fig.add_trace(
                    go.Scattermap(
                        lat=institution_df["lat"],
                        lon=institution_df["lon"],
                        mode="markers",
                        name=institution,
                        marker=dict(
                            size=10,
                            color=INSTITUTION_COLORS.get(institution, "#2563EB"),
                            opacity=0.9,
                        ),
                        text=institution_df["campus"],
                        customdata=institution_df[["entidad", "institucion", "geocode_source"]],
                        hovertemplate=(
                            "<b>%{text}</b><br>"
                            "Institucion: "
                            + institution
                            + "<br>Entidad: %{customdata[0]}<br>"
                            "Registro ANUIES: %{customdata[1]}<br>"
                            "Fuente coordenada: %{customdata[2]}<extra></extra>"
                        ),
                    )
                )
        bubble_fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            map=dict(
                style="carto-positron",
                center=dict(lat=23.5, lon=-102.0),
                zoom=4.2,
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=0.01,
                xanchor="left",
                x=0.01,
            ),
        )
        st.plotly_chart(bubble_fig, use_container_width=True)
else:
    st.info("El mapa aparecera despues de recargar la base con la nueva columna de entidad.")

with st.expander("Ver datos agregados del grafico"):
    summary_df = (
        filtered_raw_df.groupby(
            ["universidad_objetivo", "ciclo_inicio", "ciclo"],
            as_index=False,
        )[["matricula_total", "egresados_total"]]
        .sum()
        .sort_values(["universidad_objetivo", "ciclo_inicio"])
    )
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Ver tabla total por institucion"):
    total_table = (
        filtered_raw_df.groupby(
            ["universidad_objetivo", "ciclo_inicio", "ciclo"],
            as_index=False,
        )[["matricula_total", "egresados_total"]]
        .sum()
        .sort_values(["universidad_objetivo", "ciclo_inicio"])
    )
    matricula_wide = (
        total_table.pivot(
            index="universidad_objetivo",
            columns="ciclo",
            values="matricula_total",
        )
        .fillna(0)
        .reset_index()
    )
    st.dataframe(
        matricula_wide,
        use_container_width=True,
        hide_index=True,
    )
