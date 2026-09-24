import pandas as pd

def merge_data(year, files):
    merged_df = pd.read_csv(f"data/{year}/{files[0]}.csv")
    for i in range(1, len(files)):
        f = files[i]
        print(f"Merging {f} from {year}")
        df = pd.read_csv(f"data/{year}/{f}.csv")
        merged_df = merged_df.merge(df, on='SEQN', how='left')
    print(f"Saving merged data for {year} to CSV")
    merged_df.to_csv(f"data/{year}/merged_data.csv", index=False)

if __name__ == "__main__":
    files_2015 = ["DEMO_I", "IMQ_I", "DUQ_I", "HEQ_I", "HIQ_I", "MCQ_I", "KIQ_U_I", "HEPBD_I", "HEPB_S_I"]
    files_2017 = ["DEMO_J", "IMQ_J", "DUQ_J", "HEQ_J", "HIQ_J", "MCQ_J", "KIQ_U_J", "HEPBD_J", "HEPB_S_J"]
    
    merge_data(2015, files_2015)
    merge_data(2017, files_2017)