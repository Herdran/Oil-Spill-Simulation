import os
import pandas as pd

raw_data_path = "raw"
processed_data_path = "processed"

# to_replace = "name"
# locations_col_names = ["lat", "lon"]

# locations = {
# "42001":["25.926", "89.662"],
# "42002":["26.055", "93.646"],
# "42003":["25.925", "85.616"],
# "42012":["30.060", "87.548"],
# "42013":["27.173", "82.924"],
# "42019":["27.910", "95.345"],
# "42020":["26.955", "96.687"],
# "42021":["28.311", "83.306"],
# "42035":["29.237", "94.404"],
# "42036":["28.501", "84.508"],
# "42039":["28.787", "86.007"],
# "42040":["29.207", "88.237"],
# "42043":["28.982", "94.899"],
# "42044":["26.191", "97.051"],
# "42045":["26.217", "96.500"],
# "42048":["27.939", "96.843"],
# "42049":["28.351", "96.006"],
# "42050":["28.842", "94.242"],
# "42051":["29.635", "93.642"],
# "42055":["22.140", "94.112"],
# "fgbl1":["28.118", "93.670"],
# }




# # # wanted_cols = [
# # #     "YY", "MM", "DD", "hh", "mm", "WDIR", "WSPD", "name", "DIR01", "SPD01"
# # # ]

def replace_quote(f):
    with open(os.path.join(processed_data_path, f), 'r') as file:
        filedata = file.read()
        filedata = filedata.replace('"', '')
        filedata = filedata.replace('#', '')

    with open(os.path.join(processed_data_path, f), 'w') as file:
        file.write(filedata)
    

# # # paths_with_same_stations = {}    
        
# for f in os.listdir(processed_data_path):
#     df = pd.read_csv(os.path.join(processed_data_path, f))
   
#     # # for all values in SPD1 column multiply it with 0.01
#     # if "SPD01" in df.columns.to_list():
#     #     df["SPD01"] = df["SPD01"].apply(lambda x: x * 0.01)
   
#     # df.to_csv(os.path.join(processed_data_path, f), index=False)
#     # replace_quote(f)        
#     # print(f"Processed {f}")
    
#     # rename columns
#     df.rename(columns={"YY": "year", "MM": "month", "DD": "day", "hh": "hour", "mm": "min", "WDIR": "wind dir", "WSPD": "wind speed", "DIR01": "current dir", "SPD01": "current speed"}, inplace=True)
    
    
#     df.to_csv(os.path.join(processed_data_path, f), index=False)
#     replace_quote(f)        
#     print(f"Processed {f}")




# # #     name = f[:-5]
    
# # #     if name not in paths_with_same_stations:
# # #         paths_with_same_stations[name] = [f]
# # #     else:
# # #         paths_with_same_stations[name].append(f)
    
# #     # df.to_csv(os.path.join(processed_data_path, f), index=False)
# #     # replace_quote(f)        
# #     # print(f"Processed {f}")

# # # for name, paths in paths_with_same_stations.items():
# # #     expected_name = name + ".csv"
# # #     print(f"Processing into {expected_name}")
    
# # #     if len(paths) == 1:
# # #         # just copy the file
# # #         df = pd.read_csv(os.path.join(raw_data_path, paths[0]))
# # #         df.to_csv(os.path.join(processed_data_path, expected_name), index=False)
# # #     else:
# # #         # merge the files
# # #         df = pd.read_csv(os.path.join(raw_data_path, paths[0]))
# # #         for i in range(1, len(paths)):
# # #             df2 = pd.read_csv(os.path.join(raw_data_path, paths[i]))
# # #             df = pd.concat([df, df2])
        
# # #         df.to_csv(os.path.join(processed_data_path, expected_name), index=False)

# # for f in os.listdir(processed_data_path):
# #     name = f[:-4]
# #     print(name)


columns = [
    "lat",
    "lon",
    "year",
    "month",
    "day",
    "hour",
    "min",
    "wind dir",
    "wind speed",
    "current dir",
    "current speed"
]

for f in os.listdir(processed_data_path):
    df = pd.read_csv(os.path.join(processed_data_path, f))
    
    # if any of the columns is not present, then add it with NaN values
    for col in columns:
        if col not in df.columns.to_list():
            df[col] = None
    
    
    df.to_csv(os.path.join(processed_data_path, f), index=False)
    replace_quote(f)        
    print(f"Processed {f}")