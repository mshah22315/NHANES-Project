
## Appendix A. Original and derived variable definitions

The following definitions are copied from the current generated variable
dictionary. Eligibility describes the source variable, not an extra exclusion
performed by the cleaning script. See Appendix B for categorical value labels.

| Variable | Original code / derivation | Meaning | Source age eligibility |
| --- | --- | --- | --- |
| participant_id | SEQN | Unique participant identifier | All ages |
| cycle | SDDSRVYR | Readable survey cycle | All ages |
| survey_cycle_code | SDDSRVYR | NHANES data release cycle | All ages |
| age | RIDAGEYR | Age at screening | All ages |
| sex | RIAGENDR | Sex as recorded in NHANES | All ages |
| race_ethnicity | RIDRETH3 | Race and Hispanic origin, including non-Hispanic Asian | All ages |
| country_of_birth | DMDBORN4 | Place of birth category | All ages |
| years_in_us_category | DMDYRSUS | Length of residence in the United States | All ages |
| us_citizenship | DMDCITZN | US citizenship status | All ages |
| education | DMDEDUC2 | Highest completed education level | 20+ years |
| poverty_income_ratio | INDFMPIR | Family income divided by the poverty guideline | All ages |
| interview_weight_2yr | WTINT2YR | Two-year full-sample interview weight | All ages |
| mec_weight_2yr | WTMEC2YR | Two-year full-sample MEC examination weight | All ages |
| survey_psu | SDMVPSU | Masked variance pseudo-primary sampling unit | All ages |
| survey_stratum | SDMVSTRA | Masked variance pseudo-stratum | All ages |
| ever_injected_drugs | DUQ370 | Ever injected a drug not prescribed by a doctor | 18-69 years |
| time_since_injection_value | DUQ400Q | Time since last injection of a non-prescribed drug | 18-69 years |
| time_since_injection_unit | DUQ400U | Unit for time since last injection | 18-69 years |
| lifetime_injection_frequency | DUQ410 | Number of lifetime injections of non-prescribed drugs | 18-69 years |
| peak_injection_frequency | DUQ420 | Injection frequency during the period of most frequent use | 18-69 years |
| hepatitis_b_vaccination | IMQ020 | Self-reported hepatitis B vaccination history | All ages |
| kidney_failure_history | KIQ022 | Ever told by a health professional of weak or failing kidneys | 20+ years |
| dialysis | KIQ025 | Received dialysis in the past 12 months | 20+ years |
| previous_hbv_diagnosis | HEQ010 | Ever told by a doctor or health professional of hepatitis B | 6+ years |
| hepatitis_c_history | HEQ030 | Ever told by a doctor or health professional of hepatitis C | 6+ years |
| health_insurance | HIQ011 | Covered by health insurance or another health care plan | All ages |
| blood_transfusion_history | MCQ092 | Ever received a blood transfusion | 6+ years |
| blood_transfusion_period | MCD093 | Period of the first blood transfusion | 6+ years |
| hbv_core_antibody | LBXHBC | Total hepatitis B core antibody (anti-HBc) result | 6+ years |
| hbv_surface_antigen | LBDHBG | Hepatitis B surface antigen (HBsAg) result | 6+ years |
| hbv_surface_antibody | LBXHBS | Hepatitis B surface antibody (anti-HBs) result | 2+ years |
| mec_weight_4yr | WTMEC2YR / 2 | Four-year MEC examination weight | All ages |
| interview_weight_4yr | WTINT2YR / 2 | Four-year interview weight | All ages |
| hbv_positive | LBDHBG and LBXHBC | Project-defined serologic HBV outcome | 6+ years |

## Appendix B. Complete categorical label mappings

For every variable below, its companion display column is `<variable>_label`.
All ordinary missing values display as `Missing`; a missing target displays as
`Undetermined`. Mappings include valid categories absent from the selected cohort.

| Variable | Code to English label |
| --- | --- |
| survey_cycle_code | 9 = 2015-2016; 10 = 2017-2018 |
| sex | 1 = Male; 2 = Female |
| race_ethnicity | 1 = Mexican American; 2 = Other Hispanic; 3 = Non-Hispanic White; 4 = Non-Hispanic Black; 6 = Non-Hispanic Asian; 7 = Other race, including multiracial |
| country_of_birth | 1 = Born in the 50 US states or Washington, DC; 2 = Born elsewhere; 77 = Refused; 99 = Don't know |
| years_in_us_category | 1 = Less than 1 year; 2 = 1 to less than 5 years; 3 = 5 to less than 10 years; 4 = 10 to less than 15 years; 5 = 15 to less than 20 years; 6 = 20 to less than 30 years; 7 = 30 to less than 40 years; 8 = 40 to less than 50 years; 9 = 50 years or more; 77 = Refused; 99 = Don't know |
| us_citizenship | 1 = US citizen by birth or naturalization; 2 = Not a US citizen; 7 = Refused; 9 = Don't know |
| education | 1 = Less than 9th grade; 2 = 9th-11th grade, including 12th without a diploma; 3 = High school graduate, GED or equivalent; 4 = Some college or associate degree; 5 = College graduate or above; 7 = Refused; 9 = Don't know |
| ever_injected_drugs | 1 = Yes; 2 = No; 7 = Refused; 9 = Don't know |
| time_since_injection_unit | 1 = Days; 2 = Weeks; 3 = Months; 4 = Years; 7 = Refused; 9 = Don't know |
| lifetime_injection_frequency | 1 = Once; 2 = 2-5 times; 3 = 6-19 times; 4 = 20-49 times; 5 = 50-99 times; 6 = 100 times or more; 77 = Refused; 99 = Don't know |
| peak_injection_frequency | 1 = More than once a day; 2 = About once a day; 3 = At least once a week, but not every day; 4 = At least once a month, but not every week; 5 = Less than once a month; 7 = Refused; 9 = Don't know |
| hepatitis_b_vaccination | 1 = At least 3 doses; 2 = Fewer than 3 doses; 3 = No doses; 7 = Refused; 9 = Don't know |
| kidney_failure_history | 1 = Yes; 2 = No; 7 = Refused; 9 = Don't know |
| dialysis | 1 = Yes; 2 = No; 7 = Refused; 9 = Don't know |
| previous_hbv_diagnosis | 1 = Yes; 2 = No; 7 = Refused; 9 = Don't know |
| hepatitis_c_history | 1 = Yes; 2 = No; 7 = Refused; 9 = Don't know |
| health_insurance | 1 = Yes; 2 = No; 7 = Refused; 9 = Don't know |
| blood_transfusion_history | 1 = Yes; 2 = No; 7 = Refused; 9 = Don't know |
| blood_transfusion_period | 1 = Before 1972; 2 = 1972-1991; 3 = 1992 to survey date; 7 = Refused; 9 = Don't know |
| hbv_core_antibody | 1 = Positive; 2 = Negative; 3 = Indeterminate |
| hbv_surface_antigen | 1 = Positive; 2 = Negative; 3 = Indeterminate |
| hbv_surface_antibody | 1 = Positive; 2 = Negative; 3 = Indeterminate |
| hbv_positive | 0 = Negative; 1 = Positive |

`time_since_injection_value_status` has four values: `Reported value`, `Refused`
(raw code 7777), `Don't know` (raw code 9999), and `Missing`. A reported value alone
does not establish that its paired unit is available.


