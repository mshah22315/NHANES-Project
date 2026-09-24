import pandas as pd

years = [2015, 2017]
files = ["DEMO_I", "DEMO_J", "IMQ_I", "IMQ_J", "HEQ_I", "HEQ_J", "MCQ_I", "MCQ_J", "KIQ_I", "KIQ_J", "HEPBD_I", "HEPBD_J", "HEPB_S_I", "HEPB_S_J"]

def load_data(years, files):
    for y in years:
        for f in files:
            url = f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{y}/DataFiles/{f}.xpt"
            print(f"Loading {f} from {y}")
            df = pd.read_sas(url, format='xport', encoding='utf-8')
            print(f"Saving {f} from {y} to CSV")
            df.to_csv(f"data/{f}_{y}.csv", index=False)

if __name__ == "__main__":
    load_data(years, files)
