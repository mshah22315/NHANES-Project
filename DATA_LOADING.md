# NHANES 2015–2018 Data Loading

## Overview

This project uses two pre-pandemic Continuous NHANES cycles:

- 2015–2016
- 2017–2018

Only variables selected in advance based on the project objective are loaded. The pipeline does not retain all variables contained in the original NHANES files.

The loading pipeline:

1. Downloads the selected public NHANES XPT files for both cycles.
2. Extracts only the variables included in the project allowlist.
3. Renames NHANES variable codes to human-readable names.
4. Compares the renamed schemas between the two cycles.
5. Excludes variables that are unavailable or incompatible across cycles.
6. Merges all selected data sources within each cycle using the participant identifier (`SEQN`).
7. Combines the 2015–2016 and 2017–2018 cycles vertically.
8. Constructs four-year survey weights from the original two-year weights.
9. Saves one final dataset:
   `data/nhanes_2015_2018.csv`

Original NHANES response codes and missing values are preserved during this loading stage. Imputation, recoding, feature engineering, train/test splitting, and model preprocessing are performed later.

---

# Variables Included in the Final Dataset

## 1. Identifiers and Cycle Information

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Demographics | `SEQN` | `participant_id` | Unique NHANES participant identifier used to merge data sources. |
| Derived | — | `cycle` | Human-readable NHANES cycle: `2015-2016` or `2017-2018`. |
| Demographics | `SDDSRVYR` | `survey_cycle_code` | Original NHANES survey cycle code. |

---

## 2. Demographics

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Demographics | `RIDAGEYR` | `age` | Participant age in years at screening. |
| Demographics | `RIAGENDR` | `sex` | Participant sex recorded by NHANES. |
| Demographics | `RIDRETH3` | `race_ethnicity` | NHANES race and Hispanic-origin category. |
| Demographics | `DMDBORN4` | `country_of_birth` | Indicates whether the participant was born in the United States or elsewhere. |
| Demographics | `DMDYRSUS` | `years_in_us_category` | Categorized length of time living in the United States for eligible foreign-born participants. |
| Demographics | `DMDCITZN` | `us_citizenship` | U.S. citizenship status. |
| Demographics | `DMDEDUC2` | `education` | Highest education level among eligible adult participants. |
| Demographics | `INDFMPIR` | `poverty_income_ratio` | Ratio of family income to the federal poverty threshold. |

---

## 3. NHANES Survey Design and Two-Year Weights

These variables are retained for survey-weighted descriptive statistics and population-level inference. They are not ordinary model predictors.

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Demographics | `WTINT2YR` | `interview_weight_2yr` | NHANES two-year interview sample weight. |
| Demographics | `WTMEC2YR` | `mec_weight_2yr` | NHANES two-year Mobile Examination Center (MEC) sample weight. |
| Demographics | `SDMVPSU` | `survey_psu` | Masked variance pseudo-primary sampling unit used for complex survey analysis. |
| Demographics | `SDMVSTRA` | `survey_stratum` | Masked variance pseudo-stratum used for complex survey analysis. |

---

## 4. Drug Use

Only injection-drug-use variables considered potentially relevant to HBV exposure were selected.

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Drug Use | `DUQ370` | `ever_injected_drugs` | Whether the participant has ever used a needle to inject a drug not prescribed by a doctor. |
| Drug Use | `DUQ400Q` | `time_since_injection_value` | Numeric value describing how long it has been since the participant last injected drugs. |
| Drug Use | `DUQ400U` | `time_since_injection_unit` | Time unit associated with `time_since_injection_value`. |
| Drug Use | `DUQ410` | `lifetime_injection_frequency` | Reported lifetime frequency of injection drug use. |
| Drug Use | `DUQ420` | `peak_injection_frequency` | Frequency of injection drug use during the participant's period of greatest use. |

### Excluded variable

`DUQ390` (`age_first_injection`) was initially considered but excluded during cycle harmonization because its lower-age grouping differs between the two cycles:

- 2015–2016: lower category includes age ≤ 6
- 2017–2018: lower category includes age ≤ 11

The variable was therefore excluded rather than automatically recoded.

---

## 5. Hepatitis B Vaccination

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Immunization | `IMQ020` | `hepatitis_b_vaccination` | Self-reported Hepatitis B vaccination status. |

---

## 6. Kidney Conditions

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Kidney Conditions | `KIQ022` | `kidney_failure_history` | Whether the participant was ever told that they had weak or failing kidneys. |
| Kidney Conditions | `KIQ025` | `dialysis` | Whether the participant received dialysis during the specified NHANES reference period. |

Some missing values in `dialysis` are structural because the question is only asked after specific preceding questionnaire responses.

---

## 7. Other Hepatitis History

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Hepatitis Questionnaire | `HEQ030` | `hepatitis_c_history` | Whether the participant was ever told by a health professional that they had Hepatitis C. |

Variables directly asking whether the participant had previously been diagnosed with Hepatitis B were not selected as predictors because they could introduce target leakage.

---

## 8. Healthcare Access

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Health Insurance | `HIQ011` | `health_insurance` | Whether the participant is covered by health insurance or another healthcare plan. |

---

## 9. Blood Transfusion History

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Medical Conditions | `MCQ092` | `blood_transfusion_history` | Whether the participant has ever received a blood transfusion. |
| Medical Conditions | `MCD093` | `blood_transfusion_period` | Historical period in which the participant first received a blood transfusion. |

`blood_transfusion_period` is only applicable to participants reporting a previous blood transfusion, so its high missingness is largely structural.

---

## 10. Hepatitis B Laboratory Variables

These laboratory variables are retained to characterize HBV serologic status and to support later construction of the prediction target. They should not automatically be used as predictor variables.

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Hepatitis B Laboratory | `LBXHBC` | `hbv_core_antibody` | Hepatitis B core antibody (anti-HBc), indicating previous or current natural HBV infection. |
| Hepatitis B Laboratory | `LBDHBG` | `hbv_surface_antigen` | Hepatitis B surface antigen (HBsAg), indicating current HBV infection when positive. |
| Hepatitis B Surface Antibody | `LBXHBS` | `hbv_surface_antibody` | Hepatitis B surface antibody (anti-HBs), indicating immunity due to vaccination or previous infection depending on the overall serologic pattern. |

These variables will be reviewed during the target-definition stage before modeling.

---

## 11. Derived Four-Year Survey Weights

Because two complete two-year NHANES cycles are combined, four-year weights are created by dividing each two-year weight by the number of cycles combined:

`four_year_weight = two_year_weight / 2`

| Source | Original Variable | Renamed Variable | Description |
|---|---|---|---|
| Derived from `WTMEC2YR` | — | `mec_weight_4yr` | Four-year MEC survey weight for analyses combining the two NHANES cycles. |
| Derived from `WTINT2YR` | — | `interview_weight_4yr` | Four-year interview survey weight for analyses combining the two NHANES cycles. |

Survey weights are analysis variables and should not be treated as ordinary predictive features.

---

# Final Dataset Summary

The final loading pipeline produces:

| Item | Result |
|---|---:|
| 2015–2016 participants | 9,971 |
| 2017–2018 participants | 9,254 |
| Total participants | **19,225** |
| Total columns | **32** |
| Final dataset shape | **(19,225, 32)** |

The 32 columns include:

- participant and cycle identifiers;
- demographic variables;
- candidate HBV risk predictors;
- survey design variables and sample weights;
- HBV laboratory variables;
- derived four-year survey weights.

Therefore, the 32 columns should not be interpreted as 32 independent predictive features.

---