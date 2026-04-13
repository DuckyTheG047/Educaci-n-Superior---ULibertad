from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
import time
import unicodedata

import pandas as pd
import requests


ANUIES_HISTORICO_URL = "https://anuario.anuies.mx/historico.php"
CACHE_DIR = Path(__file__).resolve().parent / "data_cache"
CACHE_DIR.mkdir(exist_ok=True)
CACHE_SCHEMA_VERSION = "v2_entidad"
SNAPSHOT_DIR = Path(__file__).resolve().parent / "data_snapshot"
SNAPSHOT_DIR.mkdir(exist_ok=True)
RAW_SNAPSHOT_FILE = SNAPSHOT_DIR / "raw_dataset.csv.gz"
GEOCODED_SNAPSHOT_FILE = SNAPSHOT_DIR / "campus_points.csv.gz"

CICLO_DESDE = "2020-2021"
CICLO_HASTA = "2024-2025"

TIPOS_INSTITUCION = [
    "PARTICULAR",
    "UNIVERSIDADES PÚBLICAS FEDERALES",
    "UNIVERSIDADES PÚBLICAS ESTATALES",
]

CAMPOS_AMPLIOS = [
    "ADMINISTRACIÓN Y NEGOCIOS",
    "ARTES Y HUMANIDADES",
    "CIENCIAS SOCIALES Y DERECHO",
    "TECNOLOGÍAS DE LA INFORMACIÓN Y LA COMUNICACIÓN",
    "INGENIERÍA, MANUFACTURA Y CONSTRUCCIÓN",
    "CIENCIAS NATURALES, MATEMÁTICAS Y ESTADÍSTICA",
    "CIENCIAS DE LA SALUD",
]

CAMPOS_ESPECIFICOS = [
    "ADMINISTRACIÓN Y GESTIÓN",
    "NEGOCIOS Y CONTABILIDAD",
    "CIENCIAS SOCIALES Y ESTUDIOS DEL COMPORTAMIENTO",
    "DERECHO Y CRIMINOLOGÍA",
    "HUMANIDADES",
    "CIENCIAS DE LA INFORMACIÓN",
    "IMPLEMENTACIÓN DE LAS TECNOLOGÍAS DE LA INFORMACIÓN Y LA COMUNICACIÓN",
    "INNOVACIÓN EN TECNOLOGÍAS DE LA INFORMACIÓN Y LA COMUNICACIÓN",
    "MATEMÁTICAS Y ESTADÍSTICA",
    "INGENIERÍA MECÁNICA, ELÉCTRICA, ELECTRÓNICA, QUÍMICA Y PROFESIONES AFINES",
    "ARQUITECTURA Y CONSTRUCCIÓN",
    "MANUFACTURAS Y PROCESOS",
    "CIENCIAS FÍSICAS, QUÍMICAS Y DE LA TIERRA",
    "CIENCIAS BIOLÓGICAS Y AMBIENTALES",
    "CIENCIAS MÉDICAS",
    "CIENCIAS ODONTOLÓGICAS",
    "ENFERMERÍA",
    "DISCIPLINAS AUXILIARES PARA LA SALUD",
    "TERAPIA, REHABILITACIÓN Y TRATAMIENTOS ALTERNATIVOS",
    "ARTES",
]

CAMPO_ESPECIFICO_TO_AMPLIO = {
    "ADMINISTRACIÓN Y GESTIÓN": "ADMINISTRACIÓN Y NEGOCIOS",
    "NEGOCIOS Y CONTABILIDAD": "ADMINISTRACIÓN Y NEGOCIOS",
    "ARTES": "ARTES Y HUMANIDADES",
    "HUMANIDADES": "ARTES Y HUMANIDADES",
    "CIENCIAS SOCIALES Y ESTUDIOS DEL COMPORTAMIENTO": "CIENCIAS SOCIALES Y DERECHO",
    "DERECHO Y CRIMINOLOGÍA": "CIENCIAS SOCIALES Y DERECHO",
    "CIENCIAS DE LA INFORMACIÓN": "ARTES Y HUMANIDADES",
    "IMPLEMENTACIÓN DE LAS TECNOLOGÍAS DE LA INFORMACIÓN Y LA COMUNICACIÓN": "TECNOLOGÍAS DE LA INFORMACIÓN Y LA COMUNICACIÓN",
    "INNOVACIÓN EN TECNOLOGÍAS DE LA INFORMACIÓN Y LA COMUNICACIÓN": "TECNOLOGÍAS DE LA INFORMACIÓN Y LA COMUNICACIÓN",
    "MATEMÁTICAS Y ESTADÍSTICA": "CIENCIAS NATURALES, MATEMÁTICAS Y ESTADÍSTICA",
    "CIENCIAS FÍSICAS, QUÍMICAS Y DE LA TIERRA": "CIENCIAS NATURALES, MATEMÁTICAS Y ESTADÍSTICA",
    "CIENCIAS BIOLÓGICAS Y AMBIENTALES": "CIENCIAS NATURALES, MATEMÁTICAS Y ESTADÍSTICA",
    "INGENIERÍA MECÁNICA, ELÉCTRICA, ELECTRÓNICA, QUÍMICA Y PROFESIONES AFINES": "INGENIERÍA, MANUFACTURA Y CONSTRUCCIÓN",
    "ARQUITECTURA Y CONSTRUCCIÓN": "INGENIERÍA, MANUFACTURA Y CONSTRUCCIÓN",
    "MANUFACTURAS Y PROCESOS": "INGENIERÍA, MANUFACTURA Y CONSTRUCCIÓN",
    "CIENCIAS MÉDICAS": "CIENCIAS DE LA SALUD",
    "CIENCIAS ODONTOLÓGICAS": "CIENCIAS DE LA SALUD",
    "ENFERMERÍA": "CIENCIAS DE LA SALUD",
    "DISCIPLINAS AUXILIARES PARA LA SALUD": "CIENCIAS DE LA SALUD",
    "TERAPIA, REHABILITACIÓN Y TRATAMIENTOS ALTERNATIVOS": "CIENCIAS DE LA SALUD",
}

UNIVERSIDADES_OBJETIVO = [
    "Tecnológico de Monterrey",
    "Universidad Iberoamericana",
    "Instituto Tecnológico Autónomo de México",
    "Universidad Anáhuac",
    "Universidad Panamericana",
    "Universidad de Monterrey",
    "Universidad de las Américas Puebla",
    "Instituto Tecnológico y de Estudios Superiores de Occidente",
    "Universidad Tecmilenio",
    "Universidad del Valle de México",
    "Universidad La Salle",
    "Universidad Nacional Autónoma de México",
    "Instituto Politécnico Nacional",
    "Universidad de Guadalajara",
    "Universidad Autónoma de Nuevo León",
    "Universidad Autónoma del Estado de México",
    "Benemérita Universidad Autónoma de Puebla",
    "Universidad Autónoma de Querétaro",
    "Universidad Autónoma de Baja California",
    "Universidad Autónoma de Yucatán",
    "Universidad de la Libertad",
]

UNIVERSITY_ALIASES = {
    "Tecnológico de Monterrey": [
        "TECNOLOGICO DE MONTERREY",
        "INSTITUTO TECNOLOGICO Y DE ESTUDIOS SUPERIORES DE MONTERREY",
        "ITESM",
    ],
    "Universidad Iberoamericana": [
        "UNIVERSIDAD IBEROAMERICANA",
        "IBEROAMERICANA",
        "UIA",
    ],
    "Instituto Tecnológico Autónomo de México": [
        "INSTITUTO TECNOLOGICO AUTONOMO DE MEXICO",
        "ITAM",
    ],
    "Universidad Anáhuac": [
        "UNIVERSIDAD ANAHUAC",
        "ANAHUAC",
    ],
    "Universidad Panamericana": [
        "UNIVERSIDAD PANAMERICANA",
        "PANAMERICANA",
    ],
    "Universidad de Monterrey": [
        "UNIVERSIDAD DE MONTERREY",
        "UDEM",
    ],
    "Universidad de las Américas Puebla": [
        "UNIVERSIDAD DE LAS AMERICAS PUEBLA",
        "UDLAP",
    ],
    "Instituto Tecnológico y de Estudios Superiores de Occidente": [
        "INSTITUTO TECNOLOGICO Y DE ESTUDIOS SUPERIORES DE OCCIDENTE",
        "ITESO",
    ],
    "Universidad Tecmilenio": [
        "UNIVERSIDAD TECMILENIO",
        "TECMILENIO",
        "ENSEÑANZA E INVESTIGACIÓN SUPERIOR, A.C.",
    ],
    "Universidad del Valle de México": [
        "UNIVERSIDAD DEL VALLE DE MEXICO",
        "UVM",
    ],
    "Universidad La Salle": [
        "UNIVERSIDAD LA SALLE",
        "LA SALLE",
    ],
    "Universidad Nacional Autónoma de México": [
        "UNIVERSIDAD NACIONAL AUTONOMA DE MEXICO",
        "UNAM",
    ],
    "Instituto Politécnico Nacional": [
        "INSTITUTO POLITECNICO NACIONAL",
        "IPN",
    ],
    "Universidad de Guadalajara": [
        "UNIVERSIDAD DE GUADALAJARA",
        "UDG",
    ],
    "Universidad Autónoma de Nuevo León": [
        "UNIVERSIDAD AUTONOMA DE NUEVO LEON",
        "UANL",
    ],
    "Universidad Autónoma del Estado de México": [
        "UNIVERSIDAD AUTONOMA DEL ESTADO DE MEXICO",
        "UAEMEX",
        "UAEM",
    ],
    "Benemérita Universidad Autónoma de Puebla": [
        "BENEMERITA UNIVERSIDAD AUTONOMA DE PUEBLA",
        "BUAP",
    ],
    "Universidad Autónoma de Querétaro": [
        "UNIVERSIDAD AUTONOMA DE QUERETARO",
        "UAQ",
    ],
    "Universidad Autónoma de Baja California": [
        "UNIVERSIDAD AUTONOMA DE BAJA CALIFORNIA",
        "UABC",
    ],
    "Universidad Autónoma de Yucatán": [
        "UNIVERSIDAD AUTONOMA DE YUCATAN",
        "UADY",
    ],
    "Universidad de la Libertad": [
        "UNIVERSIDAD DE LA LIBERTAD",
        "UNIVERSIDAD LIBERTAD",
        "ULIBERTAD",
    ],
}

@dataclass(frozen=True)
class DatasetResult:
    raw_df: pd.DataFrame
    chart_df: pd.DataFrame
    matched_universities: list[str]
    missing_universities: list[str]


def _normalize_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.upper().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _cache_path(cache_name: str) -> Path:
    return CACHE_DIR / cache_name


UNIVERSITY_PATTERNS = {
    university: "|".join(re.escape(_normalize_text(alias)) for alias in aliases)
    for university, aliases in UNIVERSITY_ALIASES.items()
}


def normalize_campus_name(value: object) -> str:
    text = _normalize_text(value)
    text = text.replace("U.A.N.L.", "UANL")
    text = text.replace("U A N L", "UANL")
    text = text.replace("U.A.N.L", "UANL")
    text = text.replace("UDEM", "UNIVERSIDAD DE MONTERREY")
    text = re.sub(r"[\"'`,.;:()]+", " ", text)
    text = re.sub(r"\s*-\s*", " ", text)
    text = re.sub(r"\s*,\s*", " ", text)
    text = re.sub(r"\bCAMPUS\b", " ", text)
    text = re.sub(r"\bPLANTEL\b", " ", text)
    text = re.sub(r"\bUNIDAD ACADEMICA\b", " ", text)
    text = re.sub(r"\bUNIDAD ACADÉMICA\b", " ", text)
    text = re.sub(r"\bCENTRO DE EXTENSION\b", "CENTRO DE EXTENSION", text)
    text = re.sub(r"\bCENTRO DE EXTENSIÓN\b", "CENTRO DE EXTENSION", text)
    text = re.sub(r"\bDIVISION\b", "DIVISION", text)
    text = re.sub(r"\bDIVISIÓN\b", "DIVISION", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

STATE_CENTROIDS = {
    "AGUASCALIENTES": {"lat": 21.8853, "lon": -102.2916},
    "BAJA CALIFORNIA": {"lat": 30.8406, "lon": -115.2838},
    "BAJA CALIFORNIA SUR": {"lat": 26.0444, "lon": -111.6661},
    "CAMPECHE": {"lat": 19.8301, "lon": -90.5349},
    "COAHUILA": {"lat": 27.0587, "lon": -101.7068},
    "COLIMA": {"lat": 19.1223, "lon": -104.0072},
    "CHIAPAS": {"lat": 16.7569, "lon": -93.1292},
    "CHIHUAHUA": {"lat": 28.6330, "lon": -106.0691},
    "CIUDAD DE MEXICO": {"lat": 19.4326, "lon": -99.1332},
    "DURANGO": {"lat": 24.0277, "lon": -104.6532},
    "GUANAJUATO": {"lat": 21.0190, "lon": -101.2574},
    "GUERRERO": {"lat": 17.4392, "lon": -99.5451},
    "HIDALGO": {"lat": 20.0911, "lon": -98.7624},
    "JALISCO": {"lat": 20.6597, "lon": -103.3496},
    "MEXICO": {"lat": 19.2850, "lon": -99.6557},
    "MICHOACAN": {"lat": 19.5665, "lon": -101.7068},
    "MORELOS": {"lat": 18.6813, "lon": -99.1013},
    "NAYARIT": {"lat": 21.7514, "lon": -104.8455},
    "NUEVO LEON": {"lat": 25.5922, "lon": -99.9962},
    "OAXACA": {"lat": 17.0732, "lon": -96.7266},
    "PUEBLA": {"lat": 19.0414, "lon": -98.2063},
    "QUERETARO": {"lat": 20.5888, "lon": -100.3899},
    "QUINTANA ROO": {"lat": 19.1817, "lon": -88.4791},
    "SAN LUIS POTOSI": {"lat": 22.1565, "lon": -100.9855},
    "SINALOA": {"lat": 24.8091, "lon": -107.3940},
    "SONORA": {"lat": 29.0729, "lon": -110.9559},
    "TABASCO": {"lat": 17.9895, "lon": -92.9475},
    "TAMAULIPAS": {"lat": 23.7369, "lon": -99.1411},
    "TLAXCALA": {"lat": 19.3139, "lon": -98.2404},
    "VERACRUZ": {"lat": 19.1738, "lon": -96.1342},
    "YUCATAN": {"lat": 20.9674, "lon": -89.5926},
    "ZACATECAS": {"lat": 22.7709, "lon": -102.5832},
}

INSTITUTION_COLORS = {
    "Tecnológico de Monterrey": "#00594C",
    "Universidad Iberoamericana": "#A61E22",
    "Instituto Tecnológico Autónomo de México": "#9B1C31",
    "Universidad Anáhuac": "#0057A8",
    "Universidad Panamericana": "#B38B2D",
    "Universidad de Monterrey": "#F58220",
    "Universidad de las Américas Puebla": "#0077C8",
    "Instituto Tecnológico y de Estudios Superiores de Occidente": "#8C1515",
    "Universidad Tecmilenio": "#00A3E0",
    "Universidad del Valle de México": "#B5121B",
    "Universidad La Salle": "#0E4D92",
    "Universidad Nacional Autónoma de México": "#C9A227",
    "Instituto Politécnico Nacional": "#7A1E48",
    "Universidad de Guadalajara": "#CE9B2A",
    "Universidad Autónoma de Nuevo León": "#1E4D8F",
    "Universidad Autónoma del Estado de México": "#2C6E49",
    "Benemérita Universidad Autónoma de Puebla": "#005EB8",
    "Universidad Autónoma de Querétaro": "#004B8D",
    "Universidad Autónoma de Baja California": "#006341",
    "Universidad Autónoma de Yucatán": "#C62828",
    "Universidad de la Libertad": "#111111",
}

GEOCODE_CACHE_FILE = CACHE_DIR / "campus_geocodes_v1.json"


def _load_geocode_cache() -> dict:
    if not GEOCODE_CACHE_FILE.exists():
        return {}
    return json.loads(GEOCODE_CACHE_FILE.read_text(encoding="utf-8"))


def _save_geocode_cache(cache: dict) -> None:
    GEOCODE_CACHE_FILE.write_text(
        json.dumps(cache, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _geocode_query_candidates(campus: str, institucion: str, entidad: str) -> list[str]:
    return [
        f"{campus}, {institucion}, {entidad}, Mexico",
        f"{campus}, {entidad}, Mexico",
        f"{institucion}, {entidad}, Mexico",
    ]


def geocode_campus_points(
    raw_df: pd.DataFrame,
    *,
    force_refresh: bool = False,
    timeout: int = 30,
    allow_online: bool = True,
) -> pd.DataFrame:
    required_columns = {
        "universidad_objetivo",
        "institucion",
        "tipo_institucion",
        "campo_especifico",
        "entidad",
        "campus",
    }
    if not required_columns.issubset(raw_df.columns):
        return pd.DataFrame()

    campus_df = (
        raw_df[list(required_columns)]
        .dropna()
        .assign(
            institucion=lambda df: df["institucion"].astype(str).str.strip(),
            entidad=lambda df: df["entidad"].astype(str).str.strip(),
            campus=lambda df: df["campus"].astype(str).str.strip(),
        )
    )
    campus_df = campus_df.loc[
        (campus_df["institucion"] != "")
        & (campus_df["entidad"] != "")
        & (campus_df["campus"] != "")
    ].copy()
    campus_df["campus_normalizado"] = campus_df["campus"].map(normalize_campus_name)
    campus_df = campus_df.drop_duplicates(
        subset=["universidad_objetivo", "entidad", "campus_normalizado"]
    )

    cache = _load_geocode_cache()
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "BMK-UL/1.0 campus geocoder",
            "Accept": "application/json",
        }
    )

    geocoded_rows: list[dict] = []

    for row in campus_df.to_dict(orient="records"):
        cache_key = f"{row['universidad_objetivo']}|{row['entidad']}|{row['campus_normalizado']}"
        cached = None if force_refresh else cache.get(cache_key)

        if cached is None and allow_online:
            result = None
            for query in _geocode_query_candidates(row["campus"], row["institucion"], row["entidad"]):
                try:
                    response = session.get(
                        "https://nominatim.openstreetmap.org/search",
                        params={
                            "q": query,
                            "format": "jsonv2",
                            "limit": 1,
                            "countrycodes": "mx",
                        },
                        timeout=timeout,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    if payload:
                        item = payload[0]
                        result = {
                            "lat": float(item["lat"]),
                            "lon": float(item["lon"]),
                            "query": query,
                        }
                        break
                except Exception:
                    continue
                finally:
                    time.sleep(1.0)

            if result is not None:
                cache[cache_key] = result
                _save_geocode_cache(cache)
                cached = result

        if cached is None:
            centroid = STATE_CENTROIDS.get(_normalize_text(row["entidad"]))
            if centroid:
                cached = {
                    "lat": centroid["lat"],
                    "lon": centroid["lon"],
                    "query": "state_centroid_fallback",
                }

        if cached is None:
            continue

        geocoded_rows.append(
            {
                **row,
                "lat": cached["lat"],
                "lon": cached["lon"],
                "geocode_source": cached.get("query", ""),
            }
        )

    return pd.DataFrame(geocoded_rows)


def save_processed_snapshot(raw_df: pd.DataFrame, campus_points_df: pd.DataFrame) -> None:
    raw_df.to_csv(RAW_SNAPSHOT_FILE, index=False, compression="gzip")
    campus_points_df.to_csv(GEOCODED_SNAPSHOT_FILE, index=False, compression="gzip")


def load_processed_snapshot() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not RAW_SNAPSHOT_FILE.exists():
        return pd.DataFrame(), pd.DataFrame()

    raw_df = pd.read_csv(RAW_SNAPSHOT_FILE)
    campus_points_df = (
        pd.read_csv(GEOCODED_SNAPSHOT_FILE)
        if GEOCODED_SNAPSHOT_FILE.exists()
        else pd.DataFrame()
    )
    return raw_df, campus_points_df


def _build_base_payload() -> list[tuple[str, str]]:
    payload: list[tuple[str, str]] = [
        ("action", "historico"),
        ("cicloDesde", CICLO_DESDE),
        ("cicloHasta", CICLO_HASTA),
        ("vars[]", "MATRÍCULA"),
        ("vars[]", "EGRESADOS"),
        ("desagSexo", "1"),
        ("desagEdad", "1"),
        ("desagDiscapacidad", "0"),
        ("desagHLI", "0"),
        ("includeEnts", "1"),
        ("entMode", "all"),
        ("includeMuns", "0"),
        ("munMode", "all"),
        ("includeSos", "0"),
        ("includeAnuies", "0"),
        ("includeSub", "1"),
        ("subMode", "select"),
        ("includeInstitucion", "1"),
        ("includeEscuela", "1"),
        ("includeNivel", "0"),
        ("includeModalidad", "0"),
        ("includePrograma", "0"),
        ("includeCampoAmplio", "0"),
        ("includeCampoEspecifico", "1"),
        ("includeCampoDetallado", "0"),
        ("includeCampoUnitario", "0"),
    ]

    for institucion in TIPOS_INSTITUCION:
        payload.append(("subVals[]", institucion))

    return payload


def _build_campo_especifico_payload(campo_especifico: str) -> list[tuple[str, str]]:
    payload = _build_base_payload()
    payload.append(("campoEspecificoVals[]", campo_especifico))
    return payload


def _slugify(value: str) -> str:
    text = _normalize_text(value).lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _request_json(
    session: requests.Session,
    payload: list[tuple[str, str]],
    *,
    timeout: int,
) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
        "Referer": ANUIES_HISTORICO_URL,
    }
    response = session.post(
        ANUIES_HISTORICO_URL,
        data=payload,
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(data.get("error", "ANUIES devolvio una respuesta sin ok=true."))
    return data


def fetch_campo_amplio_dataset(
    *,
    use_cache: bool = True,
    force_refresh: bool = False,
    timeout: int = 90,
) -> pd.DataFrame:
    field_cache_files = {
        campo: _cache_path(f"campo_especifico_{_slugify(campo)}_{CACHE_SCHEMA_VERSION}.json")
        for campo in CAMPOS_ESPECIFICOS
    }

    if use_cache and not force_refresh:
        cached_frames = []
        for campo in CAMPOS_ESPECIFICOS:
            cache_file = field_cache_files[campo]
            if not cache_file.exists():
                continue
            cached_frames.append(_json_to_dataframe(json.loads(cache_file.read_text(encoding="utf-8"))))
        if cached_frames:
            return pd.concat(cached_frames, ignore_index=True)

    session = requests.Session()
    collected_frames: list[pd.DataFrame] = []
    failed_fields: list[str] = []

    for campo in CAMPOS_ESPECIFICOS:
        cache_file = field_cache_files[campo]
        payload = None
        last_error: Exception | None = None

        if use_cache and cache_file.exists() and not force_refresh:
            payload = json.loads(cache_file.read_text(encoding="utf-8"))
        else:
            for attempt in range(3):
                try:
                    payload = _request_json(
                        session,
                        _build_campo_especifico_payload(campo),
                        timeout=timeout,
                    )
                    if use_cache:
                        cache_file.write_text(
                            json.dumps(payload, ensure_ascii=False),
                            encoding="utf-8",
                        )
                    break
                except Exception as exc:
                    last_error = exc
                    if attempt < 2:
                        time.sleep(2 + attempt)

        if payload is None:
            if use_cache and cache_file.exists():
                payload = json.loads(cache_file.read_text(encoding="utf-8"))
            else:
                failed_fields.append(f"{campo}: {last_error}")
                continue

        collected_frames.append(_json_to_dataframe(payload))
        time.sleep(0.7)

    if not collected_frames:
        raise RuntimeError(
            "No fue posible descargar ANUIES por campo especifico. "
            + " | ".join(failed_fields)
        )

    combined = pd.concat(collected_frames, ignore_index=True)
    combined = combined.drop_duplicates().reset_index(drop=True)

    return combined


def _json_to_dataframe(payload: dict) -> pd.DataFrame:
    rows = payload.get("rows", [])
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).copy()

    rename_map = {
        "ENTIDAD": "entidad",
        "CLASIFICACION": "tipo_institucion",
        "NOMBRE_INSTITUCION": "institucion",
        "NOMBRE_DE_ESCUELA_CAMPUS_FACULTAD": "campus",
        "CAMPO_ESPECIFICO": "campo_especifico",
        "CICLO": "ciclo",
        "M_M": "matricula_mujeres",
        "M_H": "matricula_hombres",
        "MAT_TOTAL": "matricula_total",
        "E_M": "egresados_mujeres",
        "E_H": "egresados_hombres",
        "E": "egresados_total",
    }
    df = df.rename(columns=rename_map)

    numeric_columns = [
        "matricula_mujeres",
        "matricula_hombres",
        "matricula_total",
        "egresados_mujeres",
        "egresados_hombres",
        "egresados_total",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    text_columns = [
        "entidad",
        "tipo_institucion",
        "institucion",
        "campus",
        "campo_especifico",
        "ciclo",
    ]
    for column in text_columns:
        if column in df.columns:
            df[column] = df[column].fillna("").astype(str).str.strip()

    if "ciclo" in df.columns:
        df["ciclo_inicio"] = pd.to_numeric(df["ciclo"].str.split("-").str[0], errors="coerce")

    if "campo_especifico" in df.columns:
        df["campo_especifico_normalizado"] = df["campo_especifico"].map(_normalize_text)
    else:
        df["campo_especifico_normalizado"] = ""

    if "institucion" in df.columns:
        df["institucion_normalizada"] = df["institucion"].map(_normalize_text)
    else:
        df["institucion_normalizada"] = ""

    return df


def filter_target_universities(df: pd.DataFrame) -> DatasetResult:
    if df.empty:
        return DatasetResult(
            raw_df=df.copy(),
            chart_df=df.copy(),
            matched_universities=[],
            missing_universities=UNIVERSIDADES_OBJETIVO.copy(),
        )

    matched_frames: list[pd.DataFrame] = []
    matched_universities: list[str] = []
    missing_universities: list[str] = []

    for university in UNIVERSIDADES_OBJETIVO:
        pattern = UNIVERSITY_PATTERNS.get(university, re.escape(_normalize_text(university)))
        mask = df["institucion_normalizada"].str.contains(pattern, regex=True, na=False)
        university_df = df.loc[mask].copy()

        if university_df.empty:
            missing_universities.append(university)
            continue

        university_df["universidad_objetivo"] = university
        matched_universities.append(university)
        matched_frames.append(university_df)

    if not matched_frames:
        return DatasetResult(
            raw_df=df.iloc[0:0].copy(),
            chart_df=df.iloc[0:0].copy(),
            matched_universities=[],
            missing_universities=missing_universities,
        )

    filtered_df = pd.concat(matched_frames, ignore_index=True)

    chart_df = (
        filtered_df.groupby(
            [
                "ciclo_inicio",
                "ciclo",
                "universidad_objetivo",
            ],
            as_index=False,
        )["matricula_total"]
        .sum()
        .sort_values(["ciclo_inicio", "universidad_objetivo"])
    )

    return DatasetResult(
        raw_df=filtered_df,
        chart_df=chart_df,
        matched_universities=matched_universities,
        missing_universities=missing_universities,
    )


def load_campo_amplio_result(
    *,
    use_cache: bool = True,
    force_refresh: bool = False,
) -> DatasetResult:
    df = fetch_campo_amplio_dataset(use_cache=use_cache, force_refresh=force_refresh)
    return filter_target_universities(df)
