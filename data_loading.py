"""Load the selected public NHANES 2015-2018 variables into one CSV.

Run: python data_loading.py
Requires pandas. Output is relative to this script, not the working directory.
Only column selection, renaming, validated joins, and four-year weights are
performed. Original response codes and missing values are preserved.
See DATA_LOADING.md for the dictionary, eligibility and compatibility decisions.
"""

import argparse
from io import BytesIO
import logging
from pathlib import Path
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pandas as pd


LOGGER = logging.getLogger(__name__)
CYCLES = {"2015-2016": (2015, "I", 9), "2017-2018": (2017, "J", 10)}
BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"
DEFAULT_OUTPUT = Path(__file__).resolve().parent / "data" / "nhanes_2015_2018.csv"

# Explicit allowlist, reviewed against both official codebooks on 2026-09-25.
# NHANES distributes whole XPT files; selection happens immediately after reading.
VARIABLES = {
    "DEMO": {
        "SEQN": "participant_id",
        "SDDSRVYR": "survey_cycle_code",
        "RIDAGEYR": "age",
        "RIAGENDR": "sex",
        "RIDRETH3": "race_ethnicity",
        "DMDBORN4": "country_of_birth",
        "DMDYRSUS": "years_in_us_category",
        "DMDCITZN": "us_citizenship",
        "DMDEDUC2": "education",
        "INDFMPIR": "poverty_income_ratio",
        "WTINT2YR": "interview_weight_2yr",
        "WTMEC2YR": "mec_weight_2yr",
        "SDMVPSU": "survey_psu",
        "SDMVSTRA": "survey_stratum",
    },
    "DUQ": {
        "DUQ370": "ever_injected_drugs",
        "DUQ390": "age_first_injection",
        "DUQ400Q": "time_since_injection_value",
        "DUQ400U": "time_since_injection_unit",
        "DUQ410": "lifetime_injection_frequency",
        "DUQ420": "peak_injection_frequency",
    },
    "IMQ": {"IMQ020": "hepatitis_b_vaccination"},
    "KIQ_U": {"KIQ022": "kidney_failure_history", "KIQ025": "dialysis"},
    "HEQ": {"HEQ030": "hepatitis_c_history"},
    "HIQ": {"HIQ011": "health_insurance"},
    "MCQ": {
        "MCQ092": "blood_transfusion_history",
        "MCD093": "blood_transfusion_period",
    },
    "HEPBD": {"LBXHBC": "hbv_core_antibody", "LBDHBG": "hbv_surface_antigen"},
    "HEPB_S": {"LBXHBS": "hbv_surface_antibody"},
}

# Same name does not guarantee compatibility. Do not infer it from sample ranges.
INCOMPATIBLE = {
    "age_first_injection": (
        "DUQ390 lower age grouping changed: <=6 in 2015-2016 versus <=11 "
        "in 2017-2018. Excluded rather than recoding at the loading stage."
    ),
}
REQUIRED = {
    "participant_id", "survey_cycle_code", "interview_weight_2yr",
    "mec_weight_2yr", "survey_psu", "survey_stratum",
    "hbv_core_antibody", "hbv_surface_antigen", "hbv_surface_antibody",
}


def download_source(year, suffix, source):
    """Download one public XPT in memory; never save intermediate CSV files."""
    url = f"{BASE_URL}/{year}/DataFiles/{source}_{suffix}.xpt"
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "NHANES-Project/1.0"})
            with urlopen(request, timeout=60) as response:
                payload = response.read()
            break
        except (HTTPError, URLError, TimeoutError) as exc:
            if isinstance(exc, HTTPError) and exc.code not in (408, 429, 500, 502, 503, 504):
                raise RuntimeError(f"Download failed: {url}") from exc
            if attempt == 2:
                raise RuntimeError(f"Download failed after 3 attempts: {url}") from exc
            time.sleep(attempt + 1)
    if not payload.startswith(b"HEADER RECORD*******LIBRARY HEADER RECORD!!!!!!!"):
        raise ValueError(f"Expected SAS XPORT data, received another format: {url}")
    try:
        return pd.read_sas(BytesIO(payload), format="xport", encoding="utf-8")
    except (ValueError, OSError) as exc:
        raise ValueError(f"Cannot parse SAS XPORT data: {url}") from exc


def validate_ids(frame, label):
    if "participant_id" not in frame:
        raise ValueError(f"{label}: missing participant_id")
    ids = frame["participant_id"]
    if frame.empty or ids.isna().any() or ids.duplicated().any():
        raise ValueError(f"{label}: empty data, missing IDs or duplicate IDs")
    if not pd.api.types.is_numeric_dtype(ids) or not ((ids > 0) & (ids % 1 == 0)).all():
        raise ValueError(f"{label}: IDs must be positive integers")


def select_variables(raw, source, cycle):
    if not raw.columns.is_unique:
        raise ValueError(f"{cycle}/{source}: duplicate source columns")
    mapping = {"SEQN": "participant_id", **VARIABLES[source]}
    missing = sorted(set(mapping) - set(raw.columns))
    if "SEQN" in missing:
        raise ValueError(f"{cycle}/{source}: missing SEQN")
    if missing:
        LOGGER.warning("%s/%s: selected variables absent: %s", cycle, source, missing)
    present = [name for name in mapping if name in raw.columns]
    selected = raw.loc[:, present].rename(columns=mapping).copy()
    validate_ids(selected, f"{cycle}/{source}")
    selected["participant_id"] = selected["participant_id"].astype("int64")
    return selected


def build_dataset(reader=download_source):
    """Compare renamed schemas, remove incompatible columns, then merge by ID.

    reader(year, suffix, source) is injectable for offline regression tests.
    Any source download failure aborts the run, rather than silently losing it.
    """
    tables = {}
    schemas = {}
    for cycle, (year, suffix, cycle_code) in CYCLES.items():
        tables[cycle] = {}
        seen = set()
        for source in VARIABLES:
            LOGGER.info("Loading %s_%s (%s)", source, suffix, cycle)
            selected = select_variables(reader(year, suffix, source), source, cycle)
            overlap = (set(selected.columns) - {"participant_id"}) & seen
            if overlap:
                raise ValueError(f"Overlapping renamed columns: {sorted(overlap)}")
            seen.update(selected.columns)
            tables[cycle][source] = selected
        schemas[cycle] = seen
        demo = tables[cycle]["DEMO"]
        if "survey_cycle_code" not in demo or not demo["survey_cycle_code"].eq(cycle_code).all():
            raise ValueError(f"{cycle}: unexpected or missing SDDSRVYR")

    common = set.intersection(*schemas.values()) - set(INCOMPATIBLE)
    for name, reason in INCOMPATIBLE.items():
        LOGGER.info("Excluded %s: %s", name, reason)
    for cycle, schema in schemas.items():
        LOGGER.info("%s excluded after comparison: %s", cycle, sorted(schema - common))
    if REQUIRED - common:
        raise ValueError(f"Required columns not shared: {sorted(REQUIRED - common)}")
    ordered = [name for mapping in VARIABLES.values() for name in mapping.values() if name in common]
    if len(ordered) != len(set(ordered)):
        raise ValueError("Rename mapping contains duplicate output names")

    merged_cycles = []
    for cycle, sources in tables.items():
        merged = sources["DEMO"].loc[:, [c for c in sources["DEMO"] if c in common]].copy()
        demo_ids = set(merged["participant_id"])
        for source, frame in sources.items():
            if source == "DEMO":
                continue
            if not set(frame["participant_id"]).issubset(demo_ids):
                raise ValueError(f"{cycle}/{source}: IDs not present in demographics")
            frame = frame.loc[:, [c for c in frame if c in common]]
            merged = merged.merge(frame, on="participant_id", how="left", validate="one_to_one", sort=False)
        if len(merged) != len(demo_ids):
            raise ValueError(f"{cycle}: merge changed demographic row count")
        merged = merged.loc[:, ordered]
        merged.insert(1, "cycle", cycle)
        LOGGER.info("%s: %s participants", cycle, len(merged))
        merged_cycles.append(merged)

    result = pd.concat(merged_cycles, ignore_index=True)
    validate_ids(result, "Combined cycles")
    for kind in ("mec", "interview"):
        weight = result[f"{kind}_weight_2yr"]
        if weight.isna().any() or not weight.ge(0).all() or not weight.lt(float("inf")).all():
            raise ValueError(f"Invalid {kind} survey weights")
        result[f"{kind}_weight_4yr"] = weight / len(CYCLES)
    return result


def save_dataset(frame, output):
    """Replace the final file only after a complete CSV has been written."""
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".tmp", dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
            frame.to_csv(handle, index=False)
        temporary.replace(output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    LOGGER.info("Saved %s rows x %s columns to %s", *frame.shape, output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Final CSV path",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s"
    )

    dataset = build_dataset()

    print("\n" + "=" * 60)
    print("FINAL NHANES 2015-2018 DATASET")
    print("=" * 60)

    print(f"\nDataset shape: {dataset.shape}")
    print(f"Number of participants: {dataset.shape[0]:,}")
    print(f"Number of variables: {dataset.shape[1]}")

    print("\nVariables:")
    for i, column in enumerate(dataset.columns, start=1):
        print(f"{i:02d}. {column}")

    print("\nParticipants by cycle:")
    print(dataset["cycle"].value_counts().sort_index())

    print("\nMissing values:")
    for column in dataset.columns:
        missing = dataset[column].isna().sum()
        pct = missing / len(dataset) * 100
        print(f"{column:35s} {missing:6d} ({pct:6.2f}%)")

    print("=" * 60)

    save_dataset(dataset, args.output)


if __name__ == "__main__":
    main()

