import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import requests
import streamlit as st
from typing import Optional
import BMK_UL as bmk_data


def _fallback_normalize_text(value: object) -> str:
    return "" if value is None else str(value).upper().strip()


INSTITUTION_COLORS = getattr(bmk_data, "INSTITUTION_COLORS", {})
STATE_CENTROIDS = getattr(bmk_data, "STATE_CENTROIDS", {})
geocode_campus_points = getattr(bmk_data, "geocode_campus_points")
load_processed_snapshot = getattr(bmk_data, "load_processed_snapshot")
load_campo_amplio_result = getattr(bmk_data, "load_campo_amplio_result")
save_processed_snapshot = getattr(bmk_data, "save_processed_snapshot", lambda raw_df, campus_points_df: None)
standardize_campus_names = getattr(bmk_data, "standardize_campus_names", lambda df: df.copy())
_normalize_text = getattr(bmk_data, "_normalize_text", _fallback_normalize_text)


st.set_page_config(
    page_title="BMK UL",
    layout="wide",
)


LOGO_URL = "https://media.ulibertad.edu.mx/nimda/Umbraco/logo_ul_svg.svg"
MALE_ICON = """
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <circle cx="32" cy="18" r="10" fill="currentColor"/>
  <path d="M20 58V43c0-6.6 5.4-12 12-12s12 5.4 12 12v15h-7V45h-10v13z" fill="currentColor"/>
</svg>
"""
FEMALE_ICON = """
<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <circle cx="32" cy="16" r="10" fill="currentColor"/>
  <path d="M32 28c8.8 0 16 7.2 16 16h-7v14h-6V48h-6v10h-6V44h-7c0-8.8 7.2-16 16-16z" fill="currentColor"/>
</svg>
"""
INSTITUTION_LOGOS = {
    "Tecnológico de Monterrey": "https://www.google.com/s2/favicons?domain=tec.mx&sz=128",
    "Universidad Iberoamericana": "https://www.google.com/s2/favicons?domain=ibero.mx&sz=128",
    "Instituto Tecnológico Autónomo de México": "https://www.google.com/s2/favicons?domain=itam.mx&sz=128",
    "Universidad Anáhuac": "https://www.google.com/s2/favicons?domain=anahuac.mx&sz=128",
    "Universidad Panamericana": "https://www.google.com/s2/favicons?domain=up.edu.mx&sz=128",
    "Universidad de Monterrey": "https://www.google.com/s2/favicons?domain=udem.edu.mx&sz=128",
    "Universidad de las Américas Puebla": "https://www.google.com/s2/favicons?domain=udlap.mx&sz=128",
    "Instituto Tecnológico y de Estudios Superiores de Occidente": "https://www.google.com/s2/favicons?domain=iteso.mx&sz=128",
    "Universidad Tecmilenio": "https://www.google.com/s2/favicons?domain=tecmilenio.mx&sz=128",
    "Universidad del Valle de México": "https://www.google.com/s2/favicons?domain=uvm.mx&sz=128",
    "Universidad La Salle": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Logo_de_la_Universidad_La_Salle_sin_letras.svg/1280px-Logo_de_la_Universidad_La_Salle_sin_letras.svg.png",
    "Universidad Nacional Autónoma de México": "https://www.google.com/s2/favicons?domain=unam.mx&sz=128",
    "Instituto Politécnico Nacional": "https://www.google.com/s2/favicons?domain=ipn.mx&sz=128",
    "Universidad de Guadalajara": "https://www.google.com/s2/favicons?domain=udg.mx&sz=128",
    "Universidad Autónoma de Nuevo León": "https://www.google.com/s2/favicons?domain=uanl.mx&sz=128",
    "Universidad Autónoma del Estado de México": "https://www.google.com/s2/favicons?domain=uaemex.mx&sz=128",
    "Benemérita Universidad Autónoma de Puebla": "https://www.google.com/s2/favicons?domain=buap.mx&sz=128",
    "Universidad Autónoma de Querétaro": "https://www.uaq.mx/favicon.ico",
    "Universidad Autónoma de Baja California": "https://www.uabc.mx/favicon.ico",
    "Universidad Autónoma de Yucatán": "https://www.google.com/s2/favicons?domain=uady.mx&sz=128",
    "Universidad de la Libertad": "https://www.google.com/s2/favicons?domain=ulibertad.edu.mx&sz=128",
}


st.markdown(
    f"""
    <style>
        :root {{
            --ul-black: #0a0a0a;
            --ul-ink: #101828;
            --ul-muted: #475467;
            --ul-subtle: #667085;
            --ul-border: rgba(15, 23, 42, 0.08);
            --ul-surface: rgba(255, 255, 255, 0.88);
            --ul-surface-strong: rgba(255, 255, 255, 0.94);
            --ul-gold: #ffd100;
            --ul-gold-soft: rgba(255, 209, 0, 0.14);
            --ul-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
        }}

        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(255, 209, 0, 0.12), transparent 22%),
                radial-gradient(circle at top right, rgba(194, 214, 255, 0.30), transparent 26%),
                linear-gradient(180deg, #f7f6f2 0%, #f1efe7 100%);
        }}

        .block-container {{
            padding-top: 2.9rem;
        }}

        .ul-header {{
            width: 100%;
            background:
                linear-gradient(135deg, rgba(255,209,0,0.10), transparent 24%),
                linear-gradient(180deg, #050505 0%, #111111 100%);
            min-height: 126px;
            padding: 22px 28px 20px;
            border-radius: 0 0 22px 22px;
            display: flex;
            align-items: center;
            gap: 20px;
            box-sizing: border-box;
            margin-bottom: 28px;
            border-bottom: 2px solid rgba(255, 209, 0, 0.26);
            box-shadow: 0 18px 38px rgba(0, 0, 0, 0.22);
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
            font-size: 2.05rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }}

        .ul-header-text p {{
            margin: 8px 0 0 0;
            font-size: 0.95rem;
            color: #d6d6d6;
            max-width: 920px;
            line-height: 1.35;
        }}

        .brand-rail {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 12px;
        }}

        .brand-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 0.34rem 0.72rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #f8fafc;
            font-size: 0.78rem;
            letter-spacing: 0.02em;
        }}

        .brand-pill.brand-accent {{
            background: rgba(255, 209, 0, 0.16);
            border-color: rgba(255, 209, 0, 0.28);
            color: #fff6c2;
        }}

        .hero-card {{
            background: linear-gradient(180deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.82) 100%);
            border: 1px solid var(--ul-border);
            border-radius: 22px;
            padding: 1.35rem 1.4rem 1.15rem;
            box-shadow: var(--ul-shadow);
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }}

        .hero-card::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, var(--ul-gold) 0%, rgba(255, 209, 0, 0.28) 100%);
        }}

        .hero-card h2 {{
            margin: 0 0 0.4rem 0;
            font-size: 1.8rem;
            color: var(--ul-ink);
            letter-spacing: -0.02em;
        }}

        .hero-card p {{
            margin: 0;
            color: var(--ul-muted);
            max-width: 900px;
        }}

        .stPlotlyChart {{
            background: var(--ul-surface);
            border: 1px solid var(--ul-border);
            border-radius: 22px;
            box-shadow: var(--ul-shadow);
            padding: 0.3rem 0.3rem 0.15rem;
            margin-bottom: 0.85rem;
        }}

        div[data-testid="stVerticalBlock"]:has(.map-zone-marker) .stPlotlyChart {{
            background: transparent;
            border: none;
            border-radius: 0;
            box-shadow: none;
            padding: 0;
            margin-bottom: 0.35rem;
        }}

        .map-zone-marker {{
            display: none;
        }}

        div[data-testid="stMetric"] {{
            background: var(--ul-surface-strong);
            border: 1px solid var(--ul-border);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: 0 14px 30px rgba(15, 23, 42, 0.06);
        }}

        div[data-testid="stMetricLabel"] p {{
            color: var(--ul-subtle);
            font-size: 0.82rem;
            letter-spacing: 0.02em;
        }}

        div[data-testid="stMetricValue"] {{
            color: var(--ul-ink);
        }}

        div[data-testid="stSidebar"] {{
            background:
                radial-gradient(circle at top left, rgba(255, 209, 0, 0.10), transparent 22%),
                linear-gradient(180deg, rgba(255,255,255,0.96) 0%, rgba(248,246,240,0.98) 100%);
            border-right: 1px solid rgba(15, 23, 42, 0.06);
        }}

        div[data-testid="stSidebar"] .stButton button {{
            background: #111111;
            color: #ffffff;
            border: 1px solid rgba(255, 209, 0, 0.28);
            border-radius: 14px;
        }}

        div[data-testid="stSidebar"] .stButton button:hover {{
            border-color: rgba(255, 209, 0, 0.52);
            color: #fff7cc;
        }}

        div[data-testid="stSidebar"] label,
        div[data-testid="stSidebar"] .stMarkdown,
        div[data-testid="stSidebar"] p {{
            color: var(--ul-ink);
        }}

        @media (max-width: 768px) {{
            .ul-header {{
                padding: 16px 18px;
                min-height: 102px;
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
            <h1>Analisis Competitivo y Tendencias del Sector Educativo</h1>
            <p>Estudio integral del ecosistema educativo que permite evaluar posicionamiento, oferta academica y alineacion con las demandas del futuro.</p>
            <div class="brand-rail">
                <span class="brand-pill brand-accent">Universidad de la Libertad</span>
                <span class="brand-pill">Iris Startup Lab</span>
                <span class="brand-pill">Grupo Salinas</span>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
        .institution-card {
            background: #000000;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            box-shadow: 0 18px 36px rgba(15, 23, 42, 0.16);
            height: 176px;
            margin-bottom: 0.9rem;
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }

        .institution-card .inst-type {
            color: #9ca3af;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.25rem;
        }

        .institution-card .inst-name {
            color: #ffffff;
            font-size: 1rem;
            font-weight: 700;
            line-height: 1.2;
            margin-bottom: 0.85rem;
            min-height: 2.45rem;
            padding-right: 2.8rem;
        }

        .institution-card .inst-metric {
            color: #f3f4f6;
            font-size: 0.9rem;
            margin-bottom: 0.2rem;
        }

        .institution-card .inst-metric strong {
            font-size: 1.05rem;
        }

        .institution-card.neon-highlight {
            border-width: 2px;
        }

        .institution-card .inst-logo {
            position: absolute;
            right: 14px;
            bottom: 12px;
            width: 34px;
            height: 34px;
            object-fit: contain;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.96);
            padding: 4px;
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.28);
        }

        .gender-stat-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.85rem;
            margin: 0.4rem 0 1.4rem;
        }

        .left-visual-gap {
            height: 0.85rem;
        }

        .next-step-marker {
            display: none;
        }

        div[data-testid="stVerticalBlock"]:has(.next-step-marker) div[data-testid="stButton"] > button {
            min-height: 74px;
            border-radius: 22px;
            background: linear-gradient(135deg, #111111 0%, #1f1f1f 100%);
            color: #ffffff;
            border: 1px solid rgba(255, 209, 0, 0.36);
            box-shadow: 0 18px 38px rgba(15, 23, 42, 0.14);
            font-size: 1.2rem;
            font-weight: 700;
            letter-spacing: -0.01em;
        }

        div[data-testid="stVerticalBlock"]:has(.next-step-marker) div[data-testid="stButton"] > button:hover {
            border-color: rgba(255, 209, 0, 0.72);
            box-shadow: 0 0 0 1px rgba(255, 209, 0, 0.22), 0 18px 38px rgba(15, 23, 42, 0.18);
            color: #fff7cc;
        }

        .gender-stat-card {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 1rem 0.8rem;
            text-align: center;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
        }

        .gender-stat-icon {
            width: 42px;
            height: 42px;
            margin: 0 auto 0.45rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.45rem;
        }

        .gender-stat-icon svg {
            width: 100%;
            height: 100%;
            display: block;
        }

        .gender-stat-label {
            color: #475467;
            font-size: 0.85rem;
            margin-bottom: 0.25rem;
        }

        .gender-stat-value {
            color: #101828;
            font-size: 1.4rem;
            font-weight: 700;
            line-height: 1.1;
        }

        .gender-stat-pct {
            color: #667085;
            font-size: 0.92rem;
            margin-top: 0.2rem;
        }

        .gender-stat-top-fields {
            margin-top: 0.55rem;
            color: #475467;
            font-size: 0.76rem;
            line-height: 1.35;
        }

        .state-hover-card {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 1rem;
            box-shadow: 0 16px 34px rgba(15, 23, 42, 0.08);
            margin-bottom: 0.9rem;
        }

        .state-hover-card h4 {
            margin: 0 0 0.55rem 0;
            color: #101828;
            font-size: 1.05rem;
        }

        .state-hover-card .state-metric {
            color: #344054;
            font-size: 0.9rem;
            margin-bottom: 0.35rem;
        }

        .state-hover-card .state-metric strong {
            color: #101828;
        }

        .state-list-card {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 1rem;
            box-shadow: 0 16px 34px rgba(15, 23, 42, 0.08);
        }

        .state-list-card h5 {
            margin: 0 0 0.55rem 0;
            color: #101828;
            font-size: 0.95rem;
        }

        .state-list-card ul {
            margin: 0.25rem 0 0.9rem 0;
            padding-left: 1.1rem;
            color: #344054;
        }

        .state-list-card li {
            margin-bottom: 0.22rem;
            line-height: 1.35;
        }

        .benchmark-card {
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(15, 23, 42, 0.08);
            border-radius: 18px;
            padding: 1rem;
            box-shadow: 0 16px 34px rgba(15, 23, 42, 0.08);
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }

        .benchmark-card::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 4px;
            background: linear-gradient(180deg, #ffd100 0%, rgba(255, 209, 0, 0.18) 100%);
        }
    </style>
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
            if snapshot_points_df.empty:
                snapshot_points_df = geocode_campus_points(
                    snapshot_raw_df,
                    force_refresh=False,
                    allow_online=False,
                )
                save_processed_snapshot(snapshot_raw_df, snapshot_points_df)
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

cycle_options = (
    raw_df[["ciclo", "ciclo_inicio"]]
    .drop_duplicates()
    .sort_values("ciclo_inicio")
)
all_cycles = cycle_options["ciclo"].tolist()
default_cycle_range = (all_cycles[0], all_cycles[-1])

age_columns = {
    "TOT_17": "≤17",
    "TOT_18": "18",
    "TOT_19": "19",
    "TOT_20": "20",
    "TOT_21": "21",
    "TOT_22": "22",
    "TOT_23": "23",
    "TOT_24": "24",
    "TOT_25": "25",
    "TOT_26": "26",
    "TOT_27": "27",
    "TOT_28": "28",
    "TOT_29": "29",
    "TOT_30_34": "30-34",
    "TOT_35_39": "35-39",
    "TOT_40": "40+",
}
available_age_filter_options = [
    label for column, label in age_columns.items() if column in raw_df.columns
]

selected_cycle_range = st.select_slider(
    "Rango de ciclos",
    options=all_cycles,
    value=default_cycle_range,
)

institution_options = sorted(raw_df["universidad_objetivo"].dropna().unique().tolist())
institution_default = institution_options

with st.sidebar:
    selected_sexo = st.selectbox(
        "Sexo",
        options=["Todos", "Hombres", "Mujeres"],
        index=0,
    )

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

    with st.expander("Edad", expanded=False):
        selected_edades = st.multiselect(
            "Edad",
            options=available_age_filter_options,
            default=available_age_filter_options,
            label_visibility="collapsed",
        )

selected_institutions = selected_institutions or institution_options
selected_tipos = selected_tipos or tipo_options
selected_campos = selected_campos or campo_options
selected_edades = selected_edades or available_age_filter_options

filtered_raw_df = raw_df.copy()
selected_start_cycle, selected_end_cycle = selected_cycle_range
selected_cycle_values = cycle_options.loc[
    (cycle_options["ciclo_inicio"] >= int(selected_start_cycle.split("-")[0]))
    & (cycle_options["ciclo_inicio"] <= int(selected_end_cycle.split("-")[0])),
    "ciclo",
].tolist()
filtered_raw_df = filtered_raw_df.loc[filtered_raw_df["ciclo"].isin(selected_cycle_values)]
filtered_raw_df = filtered_raw_df.loc[
    filtered_raw_df["universidad_objetivo"].isin(selected_institutions)
]
filtered_raw_df = filtered_raw_df.loc[
    filtered_raw_df["tipo_institucion"].isin(selected_tipos)
]
filtered_raw_df = filtered_raw_df.loc[
    filtered_raw_df["campo_especifico"].isin(selected_campos)
]

if filtered_raw_df.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

selected_age_columns = [
    column
    for column, label in age_columns.items()
    if label in selected_edades and column in filtered_raw_df.columns
]
all_age_columns_selected = set(selected_edades) == set(available_age_filter_options)

if selected_age_columns:
    filtered_raw_df["matricula_edad_filtrada"] = (
        filtered_raw_df[selected_age_columns]
        .fillna(0)
        .sum(axis=1)
    )
else:
    filtered_raw_df["matricula_edad_filtrada"] = filtered_raw_df["matricula_total"]

sexo_col_map = {
    "Todos": "matricula_total",
    "Hombres": "matricula_hombres",
    "Mujeres": "matricula_mujeres",
}
sexo_metric_column = sexo_col_map[selected_sexo]
filtered_raw_df["matricula_sexo_filtrada"] = filtered_raw_df[sexo_metric_column].fillna(0)

age_filter_active = bool(available_age_filter_options) and not all_age_columns_selected
sexo_filter_active = selected_sexo != "Todos"

if age_filter_active:
    filtered_raw_df["matricula_visual"] = filtered_raw_df["matricula_edad_filtrada"]
    selected_metric_label = "Matricula por edad seleccionada"
elif sexo_filter_active:
    filtered_raw_df["matricula_visual"] = filtered_raw_df["matricula_sexo_filtrada"]
    selected_metric_label = f"Matricula de {selected_sexo.lower()}"
else:
    filtered_raw_df["matricula_visual"] = filtered_raw_df["matricula_total"]
    selected_metric_label = "Matricula total"

standardized_raw_df = standardize_campus_names(filtered_raw_df)

filtered_chart_df = (
    filtered_raw_df.groupby(
        ["universidad_objetivo", "ciclo_inicio", "ciclo"],
        as_index=False,
    )["matricula_visual"]
    .sum()
    .sort_values(["ciclo_inicio", "universidad_objetivo"])
)

filtered_campus_points_df = campus_points_df.copy()
if not filtered_campus_points_df.empty:
    if selected_cycle_values and "ciclo" in filtered_campus_points_df.columns:
        filtered_campus_points_df = filtered_campus_points_df.loc[
            filtered_campus_points_df["ciclo"].isin(selected_cycle_values)
        ]
    filtered_campus_points_df = filtered_campus_points_df.loc[
        filtered_campus_points_df["universidad_objetivo"].isin(selected_institutions)
    ]
    if "tipo_institucion" in filtered_campus_points_df.columns:
        filtered_campus_points_df = filtered_campus_points_df.loc[
            filtered_campus_points_df["tipo_institucion"].isin(selected_tipos)
        ]
    if "campo_especifico" in filtered_campus_points_df.columns:
        filtered_campus_points_df = filtered_campus_points_df.loc[
            filtered_campus_points_df["campo_especifico"].isin(selected_campos)
        ]
    filtered_campus_points_df = standardize_campus_names(filtered_campus_points_df)
    filtered_campus_points_df = filtered_campus_points_df.drop_duplicates(
        subset=["universidad_objetivo", "entidad", "campus_normalizado"]
    )

figure = px.line(
    filtered_chart_df,
    x="ciclo",
    y="matricula_visual",
    color="universidad_objetivo",
    markers=True,
    line_group="universidad_objetivo",
    color_discrete_sequence=px.colors.qualitative.Bold,
)
figure.update_layout(
    title=f"{selected_metric_label} por institucion",
    xaxis_title="Ciclo escolar",
    yaxis_title=selected_metric_label,
    legend_title="Institucion",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(255,255,255,0.72)",
    hovermode="x unified",
)
figure.update_traces(line=dict(width=3), marker=dict(size=8))

cycle_total_df = (
    filtered_chart_df.groupby(["ciclo_inicio", "ciclo"], as_index=False)["matricula_visual"]
    .sum()
    .sort_values("ciclo_inicio")
)
total_matriculados_mexico = int(filtered_raw_df["matricula_visual"].sum())
avg_growth_pct = 0.0
age_reference_values = {
    "TOT_17": 17,
    "TOT_18": 18,
    "TOT_19": 19,
    "TOT_20": 20,
    "TOT_21": 21,
    "TOT_22": 22,
    "TOT_23": 23,
    "TOT_24": 24,
    "TOT_25": 25,
    "TOT_26": 26,
    "TOT_27": 27,
    "TOT_28": 28,
    "TOT_29": 29,
    "TOT_30_34": 32,
    "TOT_35_39": 37,
    "TOT_40": 40,
}
if len(cycle_total_df) > 1:
    cycle_total_df["growth_pct"] = cycle_total_df["matricula_visual"].pct_change()
    valid_growth = cycle_total_df["growth_pct"].dropna()
    if not valid_growth.empty:
        avg_growth_pct = float(valid_growth.mean() * 100)

available_age_average_columns = [
    column for column in age_reference_values if column in filtered_raw_df.columns
]
weighted_age_sum = sum(
    float(filtered_raw_df[column].fillna(0).sum()) * age_reference_values[column]
    for column in available_age_average_columns
)
age_population_total = sum(
    float(filtered_raw_df[column].fillna(0).sum())
    for column in available_age_average_columns
)
average_age = (weighted_age_sum / age_population_total) if age_population_total else 0.0

metric_1, metric_2, metric_3 = st.columns(3)
metric_1.metric("Matriculados en Mexico", f"{total_matriculados_mexico:,}")
metric_2.metric("Crecimiento promedio", f"{avg_growth_pct:.1f}%")
metric_3.metric(
    "Edad promedio",
    f"{average_age:.1f} años",
)

st.plotly_chart(figure, use_container_width=True)

if age_filter_active and sexo_filter_active:
    st.caption(
        "Sexo y edad se muestran como filtros independientes en ANUIES. "
        "Cuando ambos estan activos, la vista principal prioriza la seleccion de edad."
    )

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
    share_df = (
        filtered_raw_df.groupby("universidad_objetivo", as_index=False)["matricula_visual"]
        .sum()
        .sort_values("matricula_visual", ascending=False)
    )
    share_fig = px.treemap(
        share_df,
        path=["universidad_objetivo"],
        values="matricula_visual",
        color="universidad_objetivo",
        color_discrete_map=INSTITUTION_COLORS,
    )
    share_fig.update_layout(
        title=f"Share de {selected_metric_label.lower()} por institucion",
        margin=dict(l=18, r=18, t=60, b=18),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    share_fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{percentRoot:.1%}",
        textfont_size=13,
        hovertemplate="%{label}<br>Valor: %{value:,}<br>Share: %{percentRoot:.1%}<extra></extra>",
        marker_line_width=2,
        marker_line_color="rgba(255,255,255,0.65)",
    )
    st.plotly_chart(share_fig, use_container_width=True)
    st.markdown('<div class="left-visual-gap"></div>', unsafe_allow_html=True)

    total_gender = float(gender_df["matricula"].sum())
    women_total = float(gender_summary.get("matricula_mujeres", 0))
    men_total = float(gender_summary.get("matricula_hombres", 0))

    if age_filter_active:
        total_base = float(filtered_raw_df["matricula_total"].fillna(0).sum())
        selected_age_total = float(filtered_raw_df["matricula_edad_filtrada"].fillna(0).sum())
        age_scale_factor = (selected_age_total / total_base) if total_base else 0.0
        women_total *= age_scale_factor
        men_total *= age_scale_factor
    else:
        age_scale_factor = 1.0

    if sexo_filter_active and not age_filter_active:
        if selected_sexo == "Hombres":
            women_total = 0.0
            total_gender = men_total
        elif selected_sexo == "Mujeres":
            men_total = 0.0
            total_gender = women_total

    women_pct = (women_total / total_gender * 100) if total_gender else 0.0
    men_pct = (men_total / total_gender * 100) if total_gender else 0.0

    gender_field_df = (
        filtered_raw_df.groupby("campo_especifico", as_index=False)
        .agg(
            matricula_hombres=("matricula_hombres", "sum"),
            matricula_mujeres=("matricula_mujeres", "sum"),
            matricula_total=("matricula_total", "sum"),
            matricula_edad_filtrada=("matricula_edad_filtrada", "sum"),
        )
    )
    if age_filter_active:
        gender_field_df["age_scale_factor"] = (
            gender_field_df["matricula_edad_filtrada"]
            .div(gender_field_df["matricula_total"].replace(0, pd.NA))
            .fillna(0)
        )
        gender_field_df["matricula_hombres_ajustada"] = (
            gender_field_df["matricula_hombres"] * gender_field_df["age_scale_factor"]
        )
        gender_field_df["matricula_mujeres_ajustada"] = (
            gender_field_df["matricula_mujeres"] * gender_field_df["age_scale_factor"]
        )
    else:
        gender_field_df["matricula_hombres_ajustada"] = gender_field_df["matricula_hombres"]
        gender_field_df["matricula_mujeres_ajustada"] = gender_field_df["matricula_mujeres"]

    men_top_fields = (
        gender_field_df.sort_values("matricula_hombres_ajustada", ascending=False)
    )
    men_top_fields = [
        value
        for value in men_top_fields["campo_especifico"].astype(str).tolist()
        if value and value.lower() != "nan"
    ][:3]

    women_top_fields = (
        gender_field_df.sort_values("matricula_mujeres_ajustada", ascending=False)
    )
    women_top_fields = [
        value
        for value in women_top_fields["campo_especifico"].astype(str).tolist()
        if value and value.lower() != "nan"
    ][:3]

    men_top_fields_html = "<br>".join(men_top_fields) if men_top_fields else "Sin datos suficientes"
    women_top_fields_html = "<br>".join(women_top_fields) if women_top_fields else "Sin datos suficientes"

    st.markdown(
        f"""
        <div class="gender-stat-grid">
            <div class="gender-stat-card">
                <div class="gender-stat-icon" style="color:#3D6D99;">{MALE_ICON}</div>
                <div class="gender-stat-label">Hombres</div>
                <div class="gender-stat-value">{int(men_total):,}</div>
                <div class="gender-stat-pct">{men_pct:.1f}%</div>
                <div class="gender-stat-top-fields">{men_top_fields_html}</div>
            </div>
            <div class="gender-stat-card">
                <div class="gender-stat-icon" style="color:#C95C7B;">{FEMALE_ICON}</div>
                <div class="gender-stat-label">Mujeres</div>
                <div class="gender-stat-value">{int(women_total):,}</div>
                <div class="gender-stat-pct">{women_pct:.1f}%</div>
                <div class="gender-stat-top-fields">{women_top_fields_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if age_filter_active:
        st.caption(
            "Los recuadros de sexo se ajustan proporcionalmente a la seleccion de edad activa."
        )
    st.markdown('<div class="left-visual-gap"></div>', unsafe_allow_html=True)

    age_columns = {
        "TOT_17": "≤17",
        "TOT_18": "18",
        "TOT_19": "19",
        "TOT_20": "20",
        "TOT_21": "21",
        "TOT_22": "22",
        "TOT_23": "23",
        "TOT_24": "24",
        "TOT_25": "25",
        "TOT_26": "26",
        "TOT_27": "27",
        "TOT_28": "28",
        "TOT_29": "29",
        "TOT_30_34": "30-34",
        "TOT_35_39": "35-39",
        "TOT_40": "40+",
    }
    available_age_columns = [
        column
        for column in age_columns
        if column in filtered_raw_df.columns
        and (not age_filter_active or age_columns[column] in selected_edades)
    ]
    if available_age_columns:
        age_df = pd.DataFrame(
            {
                "edad": [age_columns[column] for column in available_age_columns],
                "matricula": [float(filtered_raw_df[column].sum()) for column in available_age_columns],
            }
        )
        age_df = age_df.loc[age_df["matricula"] > 0]
        if not age_df.empty:
            age_pie_fig = px.pie(
                age_df,
                names="edad",
                values="matricula",
                hole=0.22,
                color="edad",
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            age_pie_fig.update_layout(
                title="Distribucion de matricula por edad",
                margin=dict(l=14, r=14, t=56, b=14),
                paper_bgcolor="rgba(0,0,0,0)",
                legend_title="Edad",
            )
            age_pie_fig.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate="%{label}<br>Matricula: %{value:,}<br>Share: %{percent}<extra></extra>",
            )
            st.plotly_chart(age_pie_fig, use_container_width=True)

campus_card_df = (
    standardized_raw_df[["universidad_objetivo", "tipo_institucion", "campus", "campus_normalizado"]]
    .dropna()
    .assign(
        tipo_institucion=lambda df: df["tipo_institucion"].astype(str).str.strip(),
        campus=lambda df: df["campus"].astype(str).str.strip(),
    )
)
campus_card_df = campus_card_df.loc[campus_card_df["campus"] != ""]

institution_summary = (
    filtered_raw_df.groupby("universidad_objetivo", as_index=False)
    .agg(
        matricula_total=("matricula_visual", "sum"),
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
)
institution_summary["card_order"] = institution_summary["universidad_objetivo"].eq(
    "Universidad de la Libertad"
).map({True: 0, False: 1})
institution_summary = institution_summary.sort_values(
    ["card_order", "matricula_total"],
    ascending=[True, False],
).drop(columns="card_order")
top_institutions = set(
    institution_summary.nlargest(5, "matricula_total")["universidad_objetivo"].tolist()
)
top_institutions.add("Universidad de la Libertad")

with gender_and_cards_right:
    st.subheader("Resumen por institucion")
    card_columns = st.columns(3)
    for idx, (_, row) in enumerate(institution_summary.iterrows()):
        column = card_columns[idx % 3]
        with column:
            is_highlighted = row["universidad_objetivo"] in top_institutions
            neon_color = (
                "#FFD100"
                if row["universidad_objetivo"] == "Universidad de la Libertad"
                else INSTITUTION_COLORS.get(row["universidad_objetivo"], "#ffffff")
            )
            extra_class = " neon-highlight" if is_highlighted else ""
            extra_style = (
                f"border-color: {neon_color}; box-shadow: 0 0 10px {neon_color}, 0 0 24px {neon_color};"
                if is_highlighted
                else ""
            )
            logo_url = INSTITUTION_LOGOS.get(row["universidad_objetivo"], "")
            logo_html = (
                f'<img class="inst-logo" src="{logo_url}" alt="{row["universidad_objetivo"]}">'
                if logo_url
                else ""
            )
            st.markdown(
                f"""
                <div class="institution-card{extra_class}" style="{extra_style}">
                    <div class="inst-type">{row["tipo_institucion"]}</div>
                    <div class="inst-name">{row["universidad_objetivo"]}</div>
                    <div class="inst-metric">{selected_metric_label}: <strong>{int(row["matricula_total"]):,}</strong></div>
                    <div class="inst-metric">Campus unicos: <strong>{int(row["campus_count"])}</strong></div>
                    {logo_html}
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


def render_state_hover_panel(state_row: Optional[pd.Series]) -> None:
    if state_row is None:
        st.markdown(
            """
            <div class="state-hover-card">
                <h4>Detalle del estado</h4>
                <div class="state-metric">Resumen del estado destacado con los filtros actuales.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="state-hover-card">
            <h4>{state_row.get("entidad", "")}</h4>
            <div class="state-metric">Campus unicos: <strong>{int(state_row.get("campus_count", 0))}</strong></div>
            <div class="state-metric">Cluster dominante: <strong>{state_row.get("cluster_campo", "Sin cluster")}</strong></div>
            <div class="state-metric">{selected_metric_label}: <strong>{int(state_row.get("cluster_matricula", 0) or 0):,}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if {"entidad", "campus", "universidad_objetivo"}.issubset(filtered_raw_df.columns):
    campus_state_df = (
        standardized_raw_df[["universidad_objetivo", "entidad", "campus", "campus_normalizado"]]
        .dropna()
        .assign(
            entidad=lambda df: df["entidad"].astype(str).str.strip(),
            campus=lambda df: df["campus"].astype(str).str.strip(),
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

    state_cluster_df = (
        filtered_raw_df.groupby(["entidad", "campo_especifico"], as_index=False)["matricula_visual"]
        .sum()
        .sort_values(["entidad", "matricula_visual"], ascending=[True, False])
        .drop_duplicates(subset=["entidad"])
        .rename(columns={"campo_especifico": "cluster_campo", "matricula_visual": "cluster_matricula"})
    )
    state_counts = state_counts.merge(
        state_cluster_df[["entidad", "cluster_campo", "cluster_matricula"]],
        on="entidad",
        how="left",
    )
    state_counts["cluster_campo"] = state_counts["cluster_campo"].fillna("Sin cluster")

    state_institutions_df = (
        filtered_raw_df.groupby(["entidad", "universidad_objetivo"], as_index=False)["matricula_visual"]
        .sum()
        .sort_values(["entidad", "matricula_visual"], ascending=[True, False])
    )
    state_campos_df = (
        filtered_raw_df.groupby(["entidad", "campo_especifico"], as_index=False)["matricula_visual"]
        .sum()
        .sort_values(["entidad", "matricula_visual"], ascending=[True, False])
    )

    centroids_df = pd.DataFrame(
        [
            {"entidad_normalizada": state, "lat": coords["lat"], "lon": coords["lon"]}
            for state, coords in STATE_CENTROIDS.items()
        ]
    )
    state_map_df = state_counts.merge(centroids_df, on="entidad_normalizada", how="left")
    map_plot_col, map_info_col = st.columns([8, 3], vertical_alignment="top")
    default_state_key = (
        state_map_df.sort_values("campus_count", ascending=False).iloc[0]["entidad_normalizada"]
        if not state_map_df.empty
        else None
    )
    selected_state_key = default_state_key
    available_state_keys = state_map_df["entidad_normalizada"].tolist()
    if selected_state_key not in available_state_keys:
        selected_state_key = default_state_key

    with map_info_col:
        if not state_map_df.empty:
            fallback_options = state_map_df.sort_values("entidad")["entidad_normalizada"].tolist()
            selected_state_key = st.selectbox(
                "Estado",
                options=fallback_options,
                index=fallback_options.index(default_state_key) if default_state_key in fallback_options else 0,
                key="selected_state_key",
                format_func=lambda key: state_map_df.loc[
                    state_map_df["entidad_normalizada"] == key, "entidad"
                ].iloc[0],
            )

    selected_state_df = state_map_df.loc[
        state_map_df["entidad_normalizada"] == selected_state_key
    ].copy()
    if not selected_state_df.empty:
        selected_state_df["estado_seleccionado"] = "Seleccionado"

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
            margin=dict(l=52, r=52, t=44, b=44),
            map_style="carto-positron",
            coloraxis_colorbar_title="Campus",
            height=720,
        )
        if not selected_state_df.empty:
            selected_overlay_fig = px.choropleth_map(
                selected_state_df,
                geojson=mexico_geojson,
                locations="entidad_normalizada",
                featureidkey="properties.normalized_name",
                color="estado_seleccionado",
                color_discrete_map={"Seleccionado": "#00E5FF"},
                center=dict(lat=23.5, lon=-102.0),
                zoom=4.2,
                opacity=0.88,
            )
            selected_overlay_fig.update_traces(
                marker_line_width=2.5,
                marker_line_color="#FFFFFF",
                hoverinfo="skip",
            )
            heatmap_fig.add_trace(selected_overlay_fig.data[0])
        with map_plot_col:
            st.markdown('<div class="map-zone-marker"></div>', unsafe_allow_html=True)
            st.plotly_chart(heatmap_fig, use_container_width=True)
            st.caption("Selecciona un estado en el panel derecho para ver su detalle.")
    else:
        bubble_df = filtered_campus_points_df.copy()
        visible_clusters = [
            cluster
            for cluster in state_map_df["cluster_campo"].dropna().astype(str).unique().tolist()
            if cluster
        ]
        cluster_palette = px.colors.qualitative.Bold
        cluster_color_map = {
            cluster: cluster_palette[idx % len(cluster_palette)]
            for idx, cluster in enumerate(sorted(visible_clusters))
        }
        bubble_fig = px.choropleth_map(
            state_map_df,
            geojson=mexico_geojson,
            locations="entidad_normalizada",
            featureidkey="properties.normalized_name",
            color="cluster_campo",
            color_discrete_map=cluster_color_map,
            hover_name="entidad",
            hover_data={
                "campus_count": True,
                "cluster_campo": True,
                "cluster_matricula": ":,.0f",
                "instituciones": True,
                "campus_list": False,
            },
            center={"lat": 23.5, "lon": -102.0},
            zoom=4.2,
            opacity=0.35,
        )
        if not selected_state_df.empty:
            selected_overlay_fig = px.choropleth_map(
                selected_state_df,
                geojson=mexico_geojson,
                locations="entidad_normalizada",
                featureidkey="properties.normalized_name",
                color="estado_seleccionado",
                color_discrete_map={"Seleccionado": "#00E5FF"},
                center={"lat": 23.5, "lon": -102.0},
                zoom=4.2,
                opacity=0.72,
            )
            selected_overlay_fig.update_traces(
                marker_line_width=2.5,
                marker_line_color="#FFFFFF",
                hoverinfo="skip",
            )
            bubble_fig.add_trace(selected_overlay_fig.data[0])
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
        legend_html = "<br>".join(
            [
                "<span style='display:inline-flex;align-items:center;gap:8px;'>"
                f"<span style='width:10px;height:10px;border-radius:50%;display:inline-block;background:{cluster_color_map[cluster]};'></span>"
                f"{cluster}</span>"
                for cluster in sorted(visible_clusters)
            ]
        )
        bubble_fig.add_annotation(
            x=0.01,
            y=0.02,
            xref="paper",
            yref="paper",
            xanchor="left",
            yanchor="bottom",
            align="left",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor="rgba(15,23,42,0.12)",
            borderwidth=1,
            borderpad=8,
            font=dict(size=10, color="#111827"),
            text=legend_html,
        )
        bubble_fig.update_layout(
            margin=dict(l=52, r=52, t=44, b=44),
            map=dict(
                style="carto-positron",
                center=dict(lat=23.5, lon=-102.0),
                zoom=4.2,
            ),
            height=720,
            showlegend=False,
        )
        with map_plot_col:
            st.markdown('<div class="map-zone-marker"></div>', unsafe_allow_html=True)
            st.plotly_chart(bubble_fig, use_container_width=True)
            st.caption("Selecciona un estado en el panel derecho para ver su detalle.")

    with map_info_col:
        selected_state_row = None
        if selected_state_key is not None:
            match_df = state_map_df.loc[state_map_df["entidad_normalizada"] == selected_state_key]
            if not match_df.empty:
                selected_state_row = match_df.iloc[0]
        render_state_hover_panel(selected_state_row)
        if selected_state_row is not None:
            selected_entity = selected_state_row.get("entidad", "")
            top_institutions_state = (
                state_institutions_df.loc[state_institutions_df["entidad"] == selected_entity]
                .head(5)["universidad_objetivo"]
                .tolist()
            )
            top_campos_state = (
                state_campos_df.loc[state_campos_df["entidad"] == selected_entity]
                .head(5)["campo_especifico"]
                .tolist()
            )
            institutions_html = (
                "".join([f"<li>{item}</li>" for item in top_institutions_state])
                if top_institutions_state
                else "<li>Sin datos.</li>"
            )
            campos_html = (
                "".join([f"<li>{item}</li>" for item in top_campos_state])
                if top_campos_state
                else "<li>Sin datos.</li>"
            )
            st.markdown(
                f"""
                <div class="state-list-card">
                    <h5>Instituciones</h5>
                    <ul>{institutions_html}</ul>
                    <h5>Top 5 Campos Especificos</h5>
                    <ul>{campos_html}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
else:
    st.info("El mapa aparecera despues de recargar la base con la nueva columna de entidad.")

top_benchmark_df = (
    filtered_raw_df.groupby("universidad_objetivo", as_index=False)["matricula_visual"]
    .sum()
    .sort_values("matricula_visual", ascending=False)
)

if not top_benchmark_df.empty and "campo_especifico" in filtered_raw_df.columns:
    st.markdown(
        """
        <div class="benchmark-card">
            <h3 style="margin:0;color:#101828;">Instituciones Lideres y Campos Relevantes</h3>
            <p style="margin:0.35rem 0 0 0;color:#475467;">
                Selecciona una institucion visible para ver su huella academica en los campos especificos mas relevantes.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    benchmark_left, benchmark_right = st.columns([3, 7], vertical_alignment="top")
    top_institutions = top_benchmark_df["universidad_objetivo"].tolist()

    with benchmark_left:
        selected_benchmark_institution = st.radio(
            "Instituciones visibles",
            options=top_institutions,
            index=0,
            label_visibility="visible",
        )

    institution_field_df = (
        filtered_raw_df.loc[
            filtered_raw_df["universidad_objetivo"] == selected_benchmark_institution,
            ["campo_especifico", "matricula_visual"],
        ]
        .groupby("campo_especifico", as_index=False)["matricula_visual"]
        .sum()
        .sort_values("matricula_visual", ascending=False)
        .head(8)
    )

    with benchmark_right:
        if not institution_field_df.empty:
            radar_df = institution_field_df.copy()
            radar_df["campo_corto"] = radar_df["campo_especifico"].astype(str)
            theta_values = radar_df["campo_corto"].tolist()
            r_values = radar_df["matricula_visual"].tolist()
            if theta_values and r_values:
                theta_values = theta_values + [theta_values[0]]
                r_values = r_values + [r_values[0]]
            radar_fig = go.Figure()
            radar_fig.add_trace(
                go.Scatterpolar(
                    r=r_values,
                    theta=theta_values,
                    fill="toself",
                    name=selected_benchmark_institution,
                    line=dict(
                        color=INSTITUTION_COLORS.get(selected_benchmark_institution, "#2563EB"),
                        width=3,
                    ),
                    fillcolor=INSTITUTION_COLORS.get(selected_benchmark_institution, "#2563EB"),
                    opacity=0.45,
                )
            )
            radar_fig.update_layout(
                title=f"Top 8 campos especificos de {selected_benchmark_institution}",
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        showticklabels=True,
                        gridcolor="rgba(15,23,42,0.12)",
                    ),
                    angularaxis=dict(
                        gridcolor="rgba(15,23,42,0.08)",
                        direction="clockwise",
                    ),
                    bgcolor="rgba(255,255,255,0.62)",
                ),
                paper_bgcolor="rgba(0,0,0,0)",
                height=520,
                margin=dict(l=36, r=36, t=76, b=36),
                showlegend=False,
            )
            st.plotly_chart(radar_fig, use_container_width=True)
        else:
            st.info("No hay campos especificos suficientes para la institucion seleccionada.")

with st.expander("Ver datos agregados del grafico"):
    summary_df = (
        filtered_raw_df.groupby(
            ["universidad_objetivo", "ciclo_inicio", "ciclo"],
            as_index=False,
        )[["matricula_visual", "egresados_total"]]
        .sum()
        .sort_values(["universidad_objetivo", "ciclo_inicio"])
    )
    summary_df = summary_df.rename(columns={"matricula_visual": selected_metric_label})
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
        )[["matricula_visual", "egresados_total"]]
        .sum()
        .sort_values(["universidad_objetivo", "ciclo_inicio"])
    )
    matricula_wide = (
        total_table.pivot(
            index="universidad_objetivo",
            columns="ciclo",
            values="matricula_visual",
        )
        .fillna(0)
        .reset_index()
    )
    st.dataframe(
        matricula_wide,
        use_container_width=True,
        hide_index=True,
    )

st.markdown('<div class="left-visual-gap"></div>', unsafe_allow_html=True)
st.markdown('<div class="next-step-marker"></div>', unsafe_allow_html=True)
if st.button("¿Qué Sigue?", use_container_width=True, key="next_steps_cta"):
    st.info(
        "Siguiente paso sugerido: profundizar en oferta academica, comparativos por campo especifico "
        "y oportunidades de diferenciacion para Universidad de la Libertad."
    )
