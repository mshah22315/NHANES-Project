import pandas as pd

years = [2015, 2017]
files = ["DEMO_I", "DEMO_J", "IMQ_I", "IMQ_J", "HEQ_I", "HEQ_J", "MCQ_I", "MCQ_J", "KIQ_I", "KIQ_J", "HEPBD_I", "HEPBD_J", "HEPB_S_I", "HEPB_S_J"]
demo_url = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/DEMO_J.xpt"
for year in years:
    for file in files:
        url = f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{file}.xpt"
        df = pd.read_sas(url, format='xport', encoding='utf-8')
        df.to_csv(f"data/{file}_{year}.csv", index=False)
