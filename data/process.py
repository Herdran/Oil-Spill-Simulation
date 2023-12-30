import os
import pandas as pd
import shutil as sh

raw_data_path = "raw"
processed_data_path = "processed"


locations = {
    "42001":["25.926", "-89.662"],
    "42002":["26.055", "-93.646"],
    "42003":["25.925", "-85.616"],
    "42012":["30.060", "-87.548"],
    "42013":["27.173", "-82.924"],
    "42019":["27.910", "-95.345"],
    "42020":["26.955", "-96.687"],
    "42021":["28.311", "-83.306"],
    "42035":["29.237", "-94.404"],
    "42036":["28.501", "-84.508"],
    "42039":["28.787", "-86.007"],
    "42040":["29.207", "-88.237"],
    "42043":["28.982", "-94.899"],
    "42044":["26.191", "-97.051"],
    "42045":["26.217", "-96.500"],
    "42048":["27.939", "-96.843"],
    "42049":["28.351", "-96.006"],
    "42050":["28.842", "-94.242"],
    "42051":["29.635", "-93.642"],
    "42055":["22.140", "-94.112"],
    "fgbl1":["28.118", "-93.670"]
}

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
    "current speed",
    "temp"
]


wanted_cols = [
    "#YY", "MM", "DD", "hh", "mm", "WDIR", "WSPD", "DIR01", "SPD01", "WTMP"
]

keys_cols = [
    "#YY", "MM", "DD", "hh", "mm", "lat", "lon"
]


columns_map = {
    "#YY": "year", "MM": "month", "DD": "day", "hh": "hour", "mm": "min", 
    "WDIR": "wind dir", "WSPD": "wind speed", "DIR01": "current dir", "SPD01": 
    "current speed", "WTMP": "temp"
}

def trim_initial_filename(f):
    return f[:-8]

def get_station_name(f):
    return f[:-5]

def into_csv(name):
    return name + ".csv" 

def clean_dir(path):
    print(f"START: Cleaning directory '{path}' ...")
    removed = 0
    for f in os.listdir(path):
        os.remove(os.path.join(path, f))
        removed += 1
    print(f"DONE:  Removed {removed} files")
    

def copy_into_processed_with_new_filename():
    print("START: Copying files into processed folder...")
    for f in os.listdir(raw_data_path):
        sh.copy(os.path.join(raw_data_path, f), os.path.join(processed_data_path, into_csv(trim_initial_filename(f))))
        print(f"\rcopied {f}", end=" ")
    print(f"\rDONE:  copied {len(os.listdir(processed_data_path))} files")
        
        
def get_columns(f):
    df = pd.read_csv(os.path.join(processed_data_path, f), nrows=1)
    return df.columns.to_list()    

def remove_not_wanted_columns():
    print("START: removing not wanted columns...")
    for f in os.listdir(processed_data_path):
        print(f"\r Processing {f}", end=" ")
        columns = set(get_columns(f))
        wanted = list(set(wanted_cols).intersection(columns))
        df = pd.read_csv(os.path.join(processed_data_path, f), usecols=wanted, skiprows=[1])
        df.to_csv(os.path.join(processed_data_path, f), index=False)
    print("\rDONE:  removed not wanted columns")
    
def remove_not_wanted_values():
    print("START: removing not wanted values...")
    for f in os.listdir(processed_data_path):
        print(f"\r Processing {f}", end=" ")
        df = pd.read_csv(os.path.join(processed_data_path, f))
    
        DIR_MIN = 0
        DIR_MAX = 360
        dir_cols = [col for col in df.columns.to_list() if "DIR" in col]
        for col in dir_cols:
           df[col].mask((df[col] <= DIR_MIN) | (df[col] >= DIR_MAX), inplace=True, )
        
        speed_cols = [col for col in df.columns.to_list() if "SPD" in col]
        max_speed_value = 200
        for col in speed_cols:
            df[col].mask(df[col] > max_speed_value, inplace=True)
            
        temp_cols = [col for col in df.columns.to_list() if "TMP" in col]
        max_temp_value = 50
        for col in temp_cols:
            df[col].mask(df[col] > max_temp_value, inplace=True)
        
    
        df.to_csv(os.path.join(processed_data_path, f), index=False)
    print("\rDONE:  removed not wanted values")    
    
def scale_values():
    problematic_col = "SPD01"
    cm_to_m = 0.01
    
    print("START: scaling values...")
    for f in os.listdir(processed_data_path):
        print(f"\r Processing {f}", end=" ")
        df = pd.read_csv(os.path.join(processed_data_path, f))
        if problematic_col in df.columns.to_list():
            df[problematic_col] = df[problematic_col].apply(lambda x: x * cm_to_m)
        df.to_csv(os.path.join(processed_data_path, f), index=False)
        
    print("\rDONE:  scaled values")

def add_lat_lon():
    print("START: adding lat lon...")
    for f in os.listdir(processed_data_path):
        print(f"\r Processing {f}", end=" ")
        name = f[:-5]
        df = pd.read_csv(os.path.join(processed_data_path, f))
        df["lat"] = locations[name][0]
        df["lon"] = locations[name][1]
        df.to_csv(os.path.join(processed_data_path, f), index=False)
        
    print("\rDONE:  added lat lon")

def join_files():
    print("START: joining files...")
    for f in os.listdir(processed_data_path):
        print(f"\r Processing {f}", end=" ")
        name = get_station_name(f)
        csv_name = into_csv(name)
        if(os.path.exists(os.path.join(processed_data_path, csv_name))):
            df_1 = pd.read_csv(os.path.join(processed_data_path, f))
            df_2 = pd.read_csv(os.path.join(processed_data_path, csv_name))
            result = pd.merge(df_1, df_2, how="outer")
            result.to_csv(os.path.join(processed_data_path, csv_name), index=False)
            os.remove(os.path.join(processed_data_path, f))
        else:
            os.rename(os.path.join(processed_data_path, f), os.path.join(processed_data_path, csv_name))        
    print("\rDONE:  joined files")

def remove_multiple_spaces():
    print("START: removing multiple spaces...")
    for f in os.listdir(processed_data_path):
        full_path = os.path.join(processed_data_path, f)
        
        print(f"\r Processing {f}", end=" ")
        file = open(full_path, "rt")
        file_out = open("temp.txt", "wt")

        for line in file:
            file_out.write(','.join(line.split()))
            file_out.write("\n")
            
        file.close()
        file_out.close()
        
        os.remove(full_path)
        os.rename("temp.txt", full_path)
            
    print("\rDONE:  removed multiple spaces")

def rename_columns():
    print("START: renaming columns...")
    for f in os.listdir(processed_data_path):
        print(f"\r Processing {f}", end=" ")
        df = pd.read_csv(os.path.join(processed_data_path, f))
        df.rename(columns=columns_map, inplace=True)
        df.to_csv(os.path.join(processed_data_path, f), index=False)
    print("\rDONE:  renamed columns")

def add_missing_columns():
    print("START: adding missing columns...")
    for f in os.listdir(processed_data_path):
        print(f"\r Processing {f}", end=" ")
        df = pd.read_csv(os.path.join(processed_data_path, f))
        for col in columns:
            if col not in df.columns.to_list():
                df[col] = None
        df.to_csv(os.path.join(processed_data_path, f), index=False)
    print("\rDONE:  added missing columns")

if __name__ == "__main__":
    clean_dir(processed_data_path)
    copy_into_processed_with_new_filename()
    remove_multiple_spaces()
    remove_not_wanted_columns()
    remove_not_wanted_values()
    scale_values()
    add_lat_lon()
    join_files()
    rename_columns()
    add_missing_columns()