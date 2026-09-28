import numpy as np
import pandas as pd
import polars as pl
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report, roc_auc_score, roc_curve, recall_score, precision_score
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer
import svy

df = pd.read_csv("data/nhanes_2015_2018_clean.csv")

exclude_columns = [
    "participant_id",
    "hbv_positive",
    "hbv_positive_label",
    "hbv_core_antibody",
    "hbv_surface_antigen",
    "hbv_surface_antibody",
    "hbv_core_antibody_label",
    "hbv_surface_antigen_label",
    "hbv_surface_antibody_label",
]

# Convert target and weights to numeric
target = pd.to_numeric(df["hbv_positive"], errors="coerce")
weights = pd.to_numeric(df["mec_weight_4yr"], errors="coerce")

# Remove missing/undetermined outcomes and invalid weights
df = df[df["hbv_positive"].isin([0, 1]) & df["mec_weight_4yr"].notna() & (df["mec_weight_4yr"] > 0)].copy()

# Keep only definitive HBV outcomes and valid MEC weights
valid_rows = (
    target.isin([0, 1])
    & weights.notna()
    & np.isfinite(weights)
    & (weights > 0)
)

# Use the complete eligible sample for survey inference
df_model = df.loc[valid_rows].copy()

# Remove refused/don't know responses for categorical variables
invalid_codes = [7, 9]

for column in [
    "sex",
    "race_ethnicity",
    "education",
    "ever_injected_drugs",
    "health_insurance",
]:
    df_model.loc[df_model[column].isin(invalid_codes), column] = np.nan

# Keep the survey sample complete for every variable used by the GLM.
# This prevents svy margins from converting missing categorical values to 0.
model_columns = [
    "hbv_positive",
    "mec_weight_4yr",
    "survey_stratum",
    "survey_psu",
    "age",
    "sex",
    "race_ethnicity",
    "education",
    "poverty_income_ratio",
    "ever_injected_drugs",
    "health_insurance",
]
df_model = df_model.dropna(subset=model_columns).copy()

# svy expects a Polars DataFrame
survey_data = pl.from_pandas(df_model)

design = svy.Design(
    wgt="mec_weight_4yr",
    stratum="survey_stratum",
    psu="survey_psu",
)

sample = svy.Sample(
    data=survey_data,
    design=design,
)

survey_fit = sample.glm.fit(
    y="hbv_positive",
    x=[
        "age",
        svy.Cat("sex"),
        svy.Cat("race_ethnicity"),
        svy.Cat("education"),
        "poverty_income_ratio",
        svy.Cat("ever_injected_drugs"),
        svy.Cat("health_insurance"),
    ],
    family="binomial",
    drop_nulls=True
)

# Predict the probability of HBV positivity for every participant in the
# complete-case survey sample.
prediction_table = survey_fit.predict(survey_data).to_polars()
predicted_data = survey_data.select(
    ["participant_id", "hbv_positive"]
).with_columns(
    prediction_table["yhat"].alias("predicted_hbv_probability"),
    prediction_table["lci"].alias("probability_lci"),
    prediction_table["uci"].alias("probability_uci"),
)

print("Participant-level predicted probabilities:")
print(predicted_data.head(10))
predicted_data.write_csv("data/hbv_probability_predictions.csv")

# Average marginal effects are changes in predicted probability. Continuous
# variables report the change per unit; categorical variables report the
# probability difference between the displayed levels.
marginal_tables = []
for variable in [
    "age",
    "sex",
    "race_ethnicity",
    "education",
    "poverty_income_ratio",
    "ever_injected_drugs",
    "health_insurance",
]:
    marginal_tables.extend(
        margin.to_polars()
        for margin in survey_fit.margins(variables=[variable])
    )

marginal_effects = pl.concat(marginal_tables, how="diagonal")
print("Average marginal probability changes:")
print(marginal_effects)
marginal_effects.write_csv("data/hbv_probability_marginal_effects.csv")


print(survey_fit)