"""

Run after data_loading.py: python data_cleaning.py
Requires pandas. Paths default to the data directory beside this script.
Raw input columns, response codes, missing values and survey weights are retained.
Official codebooks: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/
See DATA_CLEANING.md for interpretation and scope.
"""

import argparse
import json
import math
from pathlib import Path
import tempfile

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
YES_NO = {1: "Yes", 2: "No", 7: "Refused", 9: "Don't know"}
LAB_RESULT = {1: "Positive", 2: "Negative", 3: "Indeterminate"}
VALUE_LABELS = {
    "survey_cycle_code": {9: "2015-2016", 10: "2017-2018"},
    "sex": {1: "Male", 2: "Female"},
    "race_ethnicity": {
        1: "Mexican American", 2: "Other Hispanic", 3: "Non-Hispanic White",
        4: "Non-Hispanic Black", 6: "Non-Hispanic Asian",
        7: "Other race, including multiracial",
    },
    "country_of_birth": {
        1: "Born in the 50 US states or Washington, DC",
        2: "Born elsewhere", 77: "Refused", 99: "Don't know",
    },
    "years_in_us_category": {
        1: "Less than 1 year", 2: "1 to less than 5 years",
        3: "5 to less than 10 years", 4: "10 to less than 15 years",
        5: "15 to less than 20 years", 6: "20 to less than 30 years",
        7: "30 to less than 40 years", 8: "40 to less than 50 years",
        9: "50 years or more", 77: "Refused", 99: "Don't know",
    },
    "us_citizenship": {
        1: "US citizen by birth or naturalization", 2: "Not a US citizen",
        7: "Refused", 9: "Don't know",
    },
    "education": {
        1: "Less than 9th grade", 2: "9th-11th grade, including 12th without a diploma",
        3: "High school graduate, GED or equivalent",
        4: "Some college or associate degree", 5: "College graduate or above",
        7: "Refused", 9: "Don't know",
    },
    "ever_injected_drugs": YES_NO,
    "time_since_injection_unit": {
        1: "Days", 2: "Weeks", 3: "Months", 4: "Years",
        7: "Refused", 9: "Don't know",
    },
    "lifetime_injection_frequency": {
        1: "Once", 2: "2-5 times", 3: "6-19 times", 4: "20-49 times",
        5: "50-99 times", 6: "100 times or more", 77: "Refused", 99: "Don't know",
    },
    "peak_injection_frequency": {
        1: "More than once a day", 2: "About once a day",
        3: "At least once a week, but not every day",
        4: "At least once a month, but not every week",
        5: "Less than once a month", 7: "Refused", 9: "Don't know",
    },
    "hepatitis_b_vaccination": {
        1: "At least 3 doses", 2: "Fewer than 3 doses", 3: "No doses",
        7: "Refused", 9: "Don't know",
    },
    "kidney_failure_history": YES_NO,
    "dialysis": YES_NO,
    "previous_hbv_diagnosis": YES_NO,
    "hepatitis_c_history": YES_NO,
    "health_insurance": YES_NO,
    "blood_transfusion_history": YES_NO,
    "blood_transfusion_period": {
        1: "Before 1972", 2: "1972-1991", 3: "1992 to survey date",
        7: "Refused", 9: "Don't know",
    },
    "hbv_core_antibody": LAB_RESULT,
    "hbv_surface_antigen": LAB_RESULT,
    "hbv_surface_antibody": LAB_RESULT,
    "hbv_positive": {0: "Negative", 1: "Positive"},
}


def variable(source, code, description, role, age="All ages", notes="", unit="Code"):
    """Describe a variable independently of its observed sample values."""
    return {
        "source": source, "original_variable": code, "description": description,
        "role": role, "eligible_age": age, "unit": unit, "notes": notes,
    }


VARIABLE_METADATA = {
    "participant_id": variable("DEMO", "SEQN", "Unique participant identifier", "identifier", unit="Identifier"),
    "survey_cycle_code": variable("DEMO", "SDDSRVYR", "NHANES data release cycle", "survey metadata"),
    "age": variable("DEMO", "RIDAGEYR", "Age at screening", "candidate feature", notes="80 represents age 80 or older.", unit="Years"),
    "sex": variable("DEMO", "RIAGENDR", "Sex as recorded in NHANES", "candidate feature"),
    "race_ethnicity": variable("DEMO", "RIDRETH3", "Race and Hispanic origin, including non-Hispanic Asian", "candidate feature"),
    "country_of_birth": variable("DEMO", "DMDBORN4", "Place of birth category", "candidate feature", notes="Born elsewhere includes locations outside the 50 states and Washington, DC."),
    "years_in_us_category": variable("DEMO", "DMDYRSUS", "Length of residence in the United States", "candidate feature", notes="Asked of people born outside the 50 US states and Washington, DC. Codes 7 and 9 are valid duration categories."),
    "us_citizenship": variable("DEMO", "DMDCITZN", "US citizenship status", "candidate feature"),
    "education": variable("DEMO", "DMDEDUC2", "Highest completed education level", "candidate feature", "20+ years"),
    "poverty_income_ratio": variable("DEMO", "INDFMPIR", "Family income divided by the poverty guideline", "candidate feature", notes="5 represents a ratio of 5 or greater.", unit="Ratio"),
    "interview_weight_2yr": variable("DEMO", "WTINT2YR", "Two-year full-sample interview weight", "survey weight", unit="Survey weight"),
    "mec_weight_2yr": variable("DEMO", "WTMEC2YR", "Two-year full-sample MEC examination weight", "survey weight", notes="Zero denotes not MEC examined.", unit="Survey weight"),
    "survey_psu": variable("DEMO", "SDMVPSU", "Masked variance pseudo-primary sampling unit", "survey design", notes="Use together with survey_stratum for variance estimation.", unit="Design identifier"),
    "survey_stratum": variable("DEMO", "SDMVSTRA", "Masked variance pseudo-stratum", "survey design", unit="Design identifier"),
    "ever_injected_drugs": variable("DUQ", "DUQ370", "Ever injected a drug not prescribed by a doctor", "candidate feature", "18-69 years"),
    "time_since_injection_value": variable("DUQ", "DUQ400Q", "Time since last injection of a non-prescribed drug", "candidate feature", "18-69 years", "Conditional question for injection history. Read with time_since_injection_unit. 7777 means Refused; 9999 means Don't know.", "Reported number in the paired unit"),
    "time_since_injection_unit": variable("DUQ", "DUQ400U", "Unit for time since last injection", "candidate feature", "18-69 years", "Conditional question; interpret together with time_since_injection_value."),
    "lifetime_injection_frequency": variable("DUQ", "DUQ410", "Number of lifetime injections of non-prescribed drugs", "candidate feature", "18-69 years", "Conditional on injection history."),
    "peak_injection_frequency": variable("DUQ", "DUQ420", "Injection frequency during the period of most frequent use", "candidate feature", "18-69 years", "Conditional on injection history and questionnaire skips, including a single lifetime injection."),
    "hepatitis_b_vaccination": variable("IMQ", "IMQ020", "Self-reported hepatitis B vaccination history", "cohort criterion", notes="This project keeps codes 3 and 9 only. Labels describe the survey response, not verified immunization records."),
    "kidney_failure_history": variable("KIQ_U", "KIQ022", "Ever told by a health professional of weak or failing kidneys", "candidate feature", "20+ years", "Excludes kidney stones, bladder infections and incontinence."),
    "dialysis": variable("KIQ_U", "KIQ025", "Received dialysis in the past 12 months", "candidate feature", "20+ years", "Asked after a Yes to kidney_failure_history. A missing value is not recoded to No."),
    "previous_hbv_diagnosis": variable("HEQ", "HEQ010", "Ever told by a doctor or health professional of hepatitis B", "cohort criterion", "6+ years", "Self-reported diagnosis history. The loader excludes Yes; Refused and Don't know are retained."),
    "hepatitis_c_history": variable("HEQ", "HEQ030", "Ever told by a doctor or health professional of hepatitis C", "candidate feature", "6+ years"),
    "health_insurance": variable("HIQ", "HIQ011", "Covered by health insurance or another health care plan", "candidate feature"),
    "blood_transfusion_history": variable("MCQ", "MCQ092", "Ever received a blood transfusion", "candidate feature", "6+ years"),
    "blood_transfusion_period": variable("MCQ", "MCD093", "Period of the first blood transfusion", "candidate feature", "6+ years", "Asked after a Yes to blood_transfusion_history. The last category ends at the survey date."),
    "hbv_core_antibody": variable("HEPBD", "LBXHBC", "Total hepatitis B core antibody (anti-HBc) result", "outcome component", "6+ years", "Laboratory result; do not use as a pre-test screening feature."),
    "hbv_surface_antigen": variable("HEPBD", "LBDHBG", "Hepatitis B surface antigen (HBsAg) result", "outcome component", "6+ years", "Laboratory result; do not use as a pre-test screening feature."),
    "hbv_surface_antibody": variable("HEPB_S", "LBXHBS", "Hepatitis B surface antibody (anti-HBs) result", "laboratory descriptor", "2+ years", "Not used to derive the project target; not a pre-test screening feature."),
    "cycle": variable("Derived", "SDDSRVYR", "Readable survey cycle", "survey metadata", unit="2015-2016 or 2017-2018"),
    "mec_weight_4yr": variable("Derived", "WTMEC2YR / 2", "Four-year MEC examination weight", "survey weight", notes="Constructed by the loader from two complete two-year cycles; retained unchanged.", unit="Survey weight"),
    "interview_weight_4yr": variable("Derived", "WTINT2YR / 2", "Four-year interview weight", "survey weight", notes="Constructed by the loader; retained unchanged.", unit="Survey weight"),
    "hbv_positive": variable("Derived", "LBDHBG and LBXHBC", "Project-defined serologic HBV outcome", "target", "6+ years", "1: HBsAg=1 and anti-HBc=1. 0: HBsAg=2 and anti-HBc in {1,2}. Otherwise missing (Undetermined). Not a follow-up-confirmed chronic HBV diagnosis."),
}


def label_values(values, mapping, missing_label="Missing"):
    """Reject undocumented nonmissing codes instead of silently hiding them."""
    invalid = values.notna() & ~values.isin(mapping)
    if invalid.any():
        raise ValueError(f"{values.name}: undocumented codes {values[invalid].unique().tolist()}")
    return values.map(mapping).astype("string").fillna(missing_label)


def clean_data(frame):
    """Return a copy with English labels and the agreed nullable integer target.

    Every original column is preserved. Missing labels describe absence only;
    they do not assert a reason such as a skip, nonresponse or age ineligibility.
    No rows are filtered and no weights are recomputed.
    """
    required = set(VARIABLE_METADATA) - {"hbv_positive"}
    missing = required - set(frame.columns)
    unexpected = set(frame.columns) - set(VARIABLE_METADATA)
    if missing or unexpected or not frame.columns.is_unique:
        raise ValueError(f"Input schema mismatch. Missing: {sorted(missing)}; unexpected: {sorted(unexpected)}")
    if frame.empty or frame["participant_id"].isna().any() or frame["participant_id"].duplicated().any():
        raise ValueError("Input must contain nonmissing, unique participant IDs and at least one row.")
    result = frame.copy()
    for name, mapping in VALUE_LABELS.items():
        if name != "hbv_positive":
            result[f"{name}_label"] = label_values(result[name], mapping)
    expected_cycle = result["survey_cycle_code"].map(VALUE_LABELS["survey_cycle_code"])
    if expected_cycle.isna().any() or not result["cycle"].eq(expected_cycle).fillna(False).all():
        raise ValueError("cycle and survey_cycle_code must identify the same supported cycle.")

    surface = result["hbv_surface_antigen"]
    core = result["hbv_core_antibody"]
    target = pd.Series(pd.NA, index=result.index, dtype="Int64", name="hbv_positive")
    target.loc[surface.eq(1) & core.eq(1)] = 1
    target.loc[surface.eq(2) & core.isin([1, 2])] = 0
    if "hbv_positive" in frame:
        label_values(frame["hbv_positive"], VALUE_LABELS["hbv_positive"], "Undetermined")
        if not frame["hbv_positive"].astype("Int64").equals(target):
            raise ValueError("Existing hbv_positive disagrees with the project definition.")
    result["hbv_positive"] = target
    result["hbv_positive_label"] = label_values(target, VALUE_LABELS["hbv_positive"], "Undetermined")

    duration = result["time_since_injection_value"]
    if not pd.api.types.is_numeric_dtype(duration):
        raise ValueError("time_since_injection_value must be numeric.")
    observed = duration.notna() & ~duration.isin([7777, 9999])
    if ((duration[observed] < 0) | ~duration[observed].map(math.isfinite)).any():
        raise ValueError("Reported injection duration must be finite and nonnegative.")
    status = pd.Series("Reported value", index=result.index, dtype="string")
    status.loc[duration.isna()] = "Missing"
    status.loc[duration.eq(7777)] = "Refused"
    status.loc[duration.eq(9999)] = "Don't know"
    result["time_since_injection_value_status"] = status
    return result


def build_dictionary(columns):
    """Create one documented entry per output column, including added labels."""
    dictionary = {}
    for name, metadata in VARIABLE_METADATA.items():
        entry = dict(metadata)
        source = entry["source"]
        entry["codebook_urls"] = [] if source == "Derived" else [
            f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{source}_{suffix}.htm"
            for year, suffix in [(2015, "I"), (2017, "J")]
        ]
        if name in VALUE_LABELS:
            entry["value_labels"] = VALUE_LABELS[name]
            entry["label_column"] = f"{name}_label"
        if name == "time_since_injection_value":
            entry["special_codes"] = {7777: "Refused", 9999: "Don't know"}
        entry["missing_label"] = "Undetermined" if name == "hbv_positive" else "Missing"
        dictionary[name] = entry
    for name in VALUE_LABELS:
        dictionary[f"{name}_label"] = {
            "description": f"English value label for {name}", "role": "display label",
            "derived_from": name, "missing_label": dictionary[name]["missing_label"],
            "notes": "Display companion; the original numeric variable is retained.",
        }
    dictionary["time_since_injection_value_status"] = {
        "description": "Response status for the numeric injection duration",
        "role": "response status", "derived_from": "time_since_injection_value",
        "values": ["Reported value", "Refused", "Don't know", "Missing"],
        "notes": "Reported value does not establish that the paired unit is available.",
    }
    if set(dictionary) != set(columns):
        raise ValueError("Output dictionary does not cover exactly the output columns.")
    return {name: dictionary[name] for name in columns}


def atomic_write(path, writer):
    """Replace an output only after its temporary file has been written."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".tmp", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        writer(temporary)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=BASE_DIR / "data" / "nhanes_2015_2018.csv")
    parser.add_argument("--output", type=Path, default=BASE_DIR / "data" / "nhanes_2015_2018_clean.csv")
    parser.add_argument("--dictionary", type=Path, default=BASE_DIR / "data" / "variable_dictionary.json")
    args = parser.parse_args()
    paths = [path.resolve() for path in (args.input, args.output, args.dictionary)]
    if len(set(paths)) != 3:
        parser.error("Input, output and dictionary paths must be different.")
    original = pd.read_csv(args.input)
    cleaned = clean_data(original)
    dictionary = build_dictionary(cleaned.columns)
    atomic_write(args.output, lambda path: cleaned.to_csv(path, index=False))
    atomic_write(args.dictionary, lambda path: path.write_text(
        json.dumps(dictionary, ensure_ascii=True, indent=2) + "\n", encoding="utf-8"))
    print(f"Rows retained: {len(cleaned):,} / {len(original):,}")
    print(f"Columns: {len(original.columns)} input; {len(cleaned.columns)} output")
    print(cleaned["hbv_positive_label"].value_counts(dropna=False).to_string())
    print(f"Labeled data: {args.output}")
    print(f"Variable dictionary: {args.dictionary}")


if __name__ == "__main__":
    main()
