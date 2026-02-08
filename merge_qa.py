import os
import glob
import pandas as pd



csv_dir = 'result/202601'

df_list = []
for file in glob.glob(f"{csv_dir}/*.csv"):
    df = pd.read_csv(file)
    df.insert(0, 'category', file.split('/')[-1].split('.')[0])
    df_list.append(df)

merged_df = pd.concat(df_list, ignore_index=True)
merged_df.to_csv(f"{csv_dir}/all.csv", index=False)


# Divide the merged file into 4 parts
num_parts = 4
rows_per_part = len(merged_df) // num_parts + 1
for i in range(num_parts):
    part_df = merged_df.iloc[i*rows_per_part : (i+1)*rows_per_part]
    part_df.to_csv(f"{csv_dir}/all_part{i+1}.csv", index=False)