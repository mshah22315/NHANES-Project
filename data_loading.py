import pandas as pd

files_2015 = ["DEMO_I", "IMQ_I", "HEQ_I", "MCQ_I", "KIQ_U_I", "HEPBD_I", "HEPB_S_I"]
files_2017 = ["DEMO_J", "IMQ_J", "HEQ_J", "MCQ_J", "KIQ_U_J", "HEPBD_J", "HEPB_S_J"]

def load_data(year, files):
    for f in files:
        url = f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{f}.xpt"
        print(f"Loading {f} from {year}")
        df = pd.read_sas(url, format='xport', encoding='utf-8')
        print(f"Saving {f} from {year} to CSV")
        df.to_csv(f"data/{f}_{year}.csv", index=False)

if __name__ == "__main__":
    load_data(2015, files_2015)
    load_data(2017, files_2017)
