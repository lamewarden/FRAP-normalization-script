#!/usr/bin/python3

import pandas as pd
import os
import numpy as np
from time import sleep
import statistics as st
pd.options.mode.chained_assignment = None  # default='warn'
import math

# Program is written to facilitate repetitive calculations of fluorescence recovery after photobleaching (FRAP).
# For correct work, program requires python 3.6 and above installed.

# Program works with max 3 ROIs at once (besides of background and reference ROIs). Number of samples is unlimited.
# Names of columns with each ROI data are fixed as follows: col_1(or another number), long_1 and lat_1.
# Columns with background, reference and time, should be named by the same model: back_1, ref_1 and time_s_1 respectively.
# Input format should look like follows:

# |time_s_1|back_1|ref_1  |cp_1   |long_1  |lat_1|time_s_2|back_2|
# |0	   |24.332|161.397|398.839|	173.005|NaN	 | 0	  |23.092| etc....

# If less than 3 ROIs per sample needed, user can simply leave column with respective name empty.

# Output for graphic plot undergoes time conversion.
# It's necessary because different samples often has slightly different pace, so mean and SEM cannot be calculated easily.
# Each measurement is assigned to 1 sec interval. If for 1 interval we have more than 1 measurement -
# we calculate mean of those.
# The conversion allows free comparison and averaging of measurements with any pace below or equal 1 s.
# It overall doesn't influence curve's shape, but can slightly affect separate time points(as average is calculated).

# Program gets excel tab as an input, extracts columns of interest, normalizes them,
# normalizes bleached ROIs to non-bleached reference (optional, recommended if undesired bleaching is too strong),
# subtracts background (optional), transforms timescale, calculates mean, standard error of the mean and groups
# output to the new excell tab.
# Created by Kashkan Ivan. 2019.02.12

# Bugfixes and improvements:
# 2019.03.13 - fixed stupid reference to a[-1] - that not gonna work after you have more than 10 samples
# 2019.03.13 fix - fixed breaks, which appeared sometimes in the timed_library and lead to breaks in resulting dataframe
# and output for graphic plot.
# 2019.03.13 fix - empty columns are skipped now. That allows to calculate SEM for each group of values(even if this
# group contains empty samples).
# 2019.04.01 fix - fixed bug when program didn't stop after file name error
# 2019.04.01 Added summary section in output for graph plot
# 2019.06.09 In summary section all mean values are cut at the length of the shortest data seq.
# 2019.06.14 Now program can adjust time with different time pace (in previous versions pace was max 1 sec).


def open_file(path_to_file):
    # opening of excel file
    try:
        dt_frame = pd.read_excel(path_to_file)
        return dt_frame
    except FileNotFoundError:
        print("File does not exist. Restart program with correct input file name please. ")
        sleep(5)
        exit()


def postbleach(raw_dt_frame):
    # Creation of new dataframe without 3 prebleach reference measurements
    return raw_dt_frame[3:]


def pb_time_0(postbleach_df_notime):
    postbleach_df = pd.DataFrame(postbleach_df_notime)
    for i in postbleach_df:
        if i.startswith("time"):
            postbleach_df[i] = postbleach_df[i] - postbleach_df[i][3]# - postbleach_df_notime[a][0]
    return postbleach_df
#we see weird bechavior where both postbleach_df_notime and postbleach_df change after time substraction


def min_calc(postbleach_df):
    # getting array with first afterbleach measurement
    return postbleach_df[:1]

#it's not used in time sacale for sigma, nice
def getting_new_time_scale(raw_dt_frame, pace_value=1):     #we need to ask for pace_value quite early
    # Here we generate list with time maxes-seconds before actual bleaching, to start counting at 0 intencity moment
    new_time_maxes = {f"time_s_{[int(i) for i in a.split('_') if i.isdigit()][0]}": round(max(raw_dt_frame[f"time_s_{[int(i) for i in a.split('_') if i.isdigit()][0]}"]) - int(raw_dt_frame[f"time_s_{[int(i) for i in a.split('_') if i.isdigit()][0]}"][3])) for a in raw_dt_frame}  # fuck.... it's unreadable
    # Let's choose maximum time out of max times:
    time_max = max(new_time_maxes.values())
    graph_timescale = {"time": [g for g in range(0 - pace_value, time_max, pace_value)]} # -1 is defined for 1 prebleached value
    return graph_timescale


def prebleach_mean_calc(raw_dt_frame):
    # Now let's divide original dataframe to prebleach and postbleach peaces
    return np.mean(raw_dt_frame[:3])


def library_creation(postbleach_df):
    # 1. Dict with slots(each of them is dict by themselves) equal to the number of our samples
    # 2. Then to the dict under samples we put each column of the original dataframe, if it's name
    #    ends with the same number as sample
    library = {f"sample{[int(i) for i in a.split('_') if i.isdigit()][0]}": {b: list(postbleach_df[b]) for b in postbleach_df if b.endswith("_"+[i for i in a.split('_') if i.isdigit()][0])} for a in postbleach_df}
    return library


def time_adjustment(library, pace_value=1):
    # creation of list of dataframes from the library
    pandaded_library = dict(library)
    list_of_df = []
    for sample in pandaded_library:
        list_of_df.append(pd.DataFrame(pandaded_library[sample]))
    # here we create universal time scale with pace 1 sec.
    # It's necessary because different samples often has slightly different pace, so mean cannot be calculated easily.
    # For this we assign each measurement to 1 sec interval. If for 1 interval we have more than 1 measurement -
    # we calculate mean of those.
    # Output values are put to the new dataframe.
    # looks like working so far - converter of time. Hooooray!
    list_of_resulting_df = []
    indeks = 0
    for a in list_of_df:
        list_of_resulting_df.append(pd.DataFrame(columns=list(a), index=[0]))
        pace_counter = 0
        for i in range(1, (len(a)-1)):        # it was originally: for i in range(1, (len(a) - 1)):
            try:
                if pace_counter + pace_value > int(a.loc[i + 1, list(a)[0]]) >= pace_counter:
                    continue  # so we ignore first value
                elif pace_counter + pace_value > int(a.loc[i - 1, list(a)[0]]) >= pace_counter:
                    list_of_resulting_df[indeks] = list_of_resulting_df[indeks].append(((a.loc[i] + a.loc[i - 1]) / 2), ignore_index=True)
                    pace_counter += pace_value
                else:  # second value with similar time we summ with previous and pass to new df
                    list_of_resulting_df[indeks] = list_of_resulting_df[indeks].append(a.loc[i])
                    pace_counter += pace_value
                    # those which are not repetitive are sent to new dataframe immediately
            except ValueError:
                pass
        indeks += 1
# Fixing any problems with pandas indices
    for a in list_of_resulting_df:
        z = 0
        for b in a.index.values:
            a.rename(index={b: z}, inplace=True)
            z = z + 1
    return list_of_resulting_df


def library_to_df(timed_library):
    # we created list of dataframes from our library
    pandaded_library = list(timed_library)
    # We join them to one final df
    timed_df = pd.concat([a for a in pandaded_library], ignore_index=False, axis=1)
    timed_df.loc[0] = prebleach_means
    return timed_df


def sigmaplot_normalization(dt_frame):
    try:
        # This part is needed if we want to make fitting of our data in sigmaplot.
        # No time adjustment is needed here.
        # Only normalization to max and min values. normalized value=(current value - min value)/(max value - min value)
        # Here we create dic with means
        mean_maxes = {i:np.mean(dt_frame[i][:3]) for i in dt_frame}
        # Here we create dic with mins
        mins = {i : dt_frame[i][3] for i in dt_frame}
        # Here we put all processed values to the new dic
        results = {}
        for a in dt_frame:
            results[a] = []
            if a.find("cp") >= 0 or a.find("long") >= 0 or a.find("lat") >= 0:
                for b in dt_frame[a]:
                    results[a].append((b-mins[a])/(mean_maxes[a]-mins[a]))
            else:
                for c in dt_frame[a]:
                    results[a].append(c)
        # Here we convert it to the dataframe
        df_results = pd.DataFrame(results)
        df_results = df_results[3:]
        return df_results
    except ZeroDivisionError:
        print("Division by zero is forbidden, check your data.")
    except ValueError:
        print("Non-numeric characters found, check your data.")


def bleaching_normalization(df):
    # Only one question si where to implement it. It looks like it beautifully works with raw dataframe
    # Initial idea is to do both - reference and background as one function, but if we don't want to work with background -
    # make it equal to 0
    # that was easy... too easy
    # Here we create dic with means
    for a in df:
        for b in range(len(df[a])):
            if a.startswith("cp") or a.startswith("long") or a.startswith("lat"):
                df[a].loc[b] = (df[a].loc[b] - df[f"back_{[int(i) for i in a.split('_') if i.isdigit()][0]}"].loc[b])/(df[f"ref_{[int(i) for i in a.split('_') if i.isdigit()][0]}"].loc[b] - df[f"back_{[int(i) for i in a.split('_') if i.isdigit()][0]}"].loc[b])
                normalized_with_ref = pd.DataFrame.copy(df)
    return normalized_with_ref


def graph_normalization(timed_df):
    # Same as sigmaplot normalization but for time adjusted dataframe
    try:
        # Here we put all processed values to the new dic
        results = {}
        for a in timed_df:
            results[a] = []
            if a.find("cp") >= 0 or a.find("long") >= 0 or a.find("lat") >= 0:
                for b in timed_df[a]:
                    results[a].append((b-timed_df[a].loc[1])/(timed_df[a].loc[0]-timed_df[a].loc[1]))
            else:
                for c in timed_df[a]:
                    results[a].append(c)
        # Here we convert it to the dataframe
        df_results = pd.DataFrame(results)
        return df_results.dropna(axis=1, how='all')
    except ZeroDivisionError:
        print("Division by zero is forbidden, check your data.")
    except ValueError:
        print("Non-numeric characters found, check your data.")


def align(datafr):
###cutting our dataframe to the shortest collumn
#here we detect the shortest lenght of our data
    length_of_columns = []
    for a in datafr:
        single_col_length = 0
        for i in datafr[a]:
            if type(i)!= "str":
                if math.isnan(i):
                    single_col_length = single_col_length  + 0
                else:
                    single_col_length = single_col_length  + 1
        if single_col_length !=0:
            length_of_columns.append(single_col_length)
    #here we cut all data to align it with the shortest point
    new_df = datafr.loc[0:(min(length_of_columns)-1)]
    return new_df


def output_for_plot(df_graph_normalized, new_time_scale):
    ### Preparing output for graphical part:
    # By returning time, shuffling data and adding means+SEMs
    # deleting useless time:
    summary_mean_sem = pd.DataFrame(new_time_scale)
    for a in df_graph_normalized:
        if a.startswith("time"):
            del df_graph_normalized[a]
    # aggregating all measurements with alike names to the new dataframes:
    # cp
    cp_counter = 0
    for a in df_graph_normalized:
        if a.startswith("cp"):
            cp_counter +=1
    if cp_counter > 1:
        cp_df = pd.DataFrame(new_time_scale)
        for a in df_graph_normalized:
            if a.startswith("cp"):
                cp_df[a] = df_graph_normalized[a]
        np.mean(cp_df.loc[1][1:])
        cp_df["cp_mean"] = [np.mean(cp_df.loc[a][1:]) for a in range(len(cp_df))]
        cp_df["cp_SEM"] = [st.stdev(cp_df.loc[a][1:-1]) / (len(cp_df.loc[0][1:-1]) ** 0.5) for a in range(len(cp_df))]
        summary_mean_sem["cp_mean"] = cp_df["cp_mean"]
        summary_mean_sem["cp_SEM"] = cp_df["cp_SEM"]
    else:
        cp_df = pd.DataFrame(new_time_scale)

        # long
    long_counter = 0
    for a in df_graph_normalized:
        if a.startswith("long"):
            long_counter +=1
    if long_counter > 1:
        long_df = pd.DataFrame(new_time_scale)
        for a in df_graph_normalized:
            if a.startswith("long"):
                long_df[a]=df_graph_normalized[a]
        long_df["long_mean"] = [np.mean(long_df.loc[a][1:]) for a in range(len(long_df))]
        long_df["long_SEM"] = [st.stdev(long_df.loc[a][1:-1])/(len(long_df.loc[0][1:-1])**0.5) for a in range(len(long_df))]
        summary_mean_sem["long_mean"] = long_df["long_mean"]
        summary_mean_sem["long_SEM"] = long_df["long_SEM"]
    else:
        long_df = pd.DataFrame(new_time_scale)

    # lat
    lat_counter = 0
    for a in df_graph_normalized:
        if a.startswith("lat"):
            lat_counter +=1
    if lat_counter > 1:
        lat_df = pd.DataFrame(new_time_scale)
        for a in df_graph_normalized:
            if a.startswith("lat"):
                lat_df[a]=df_graph_normalized[a]
        lat_df["lat_mean"] = [np.mean(lat_df.loc[a][1:]) for a in range(len(lat_df))]
        lat_df["lat_SEM"] = [st.stdev(lat_df.loc[a][1:-1])/(len(lat_df.loc[0][1:-1])**0.5) for a in range(len(lat_df))]
        summary_mean_sem["lat_mean"] = lat_df["lat_mean"]
        summary_mean_sem["lat_SEM"] = lat_df["lat_SEM"]
    else:
        lat_df = pd.DataFrame(new_time_scale)


    # We align all mean data here:
    summary_mean_sem = pd.DataFrame(align(summary_mean_sem))
    # fusing them togethr:
    # Adding spacer collumn
    summary_mean_sem["Normalized data"] = ""
    summary_spacer = pd.DataFrame()
    summary_spacer["Summary"] = ""

    graphical_output = pd.concat([summary_spacer, summary_mean_sem, cp_df, long_df, lat_df], ignore_index=False, axis=1)
    return graphical_output


def output_for_sigmaplot(normalized_sigmaplot):
    cp_sigmaplot = pd.DataFrame()
    for a in normalized_sigmaplot:
        for b in time_for_sigmaplot:
            if a.startswith("cp") and b.endswith("_"+[i for i in a.split('_') if i.isdigit()][0]):
                cp_sigmaplot[b] = time_for_sigmaplot[b]
                cp_sigmaplot[a] = normalized_sigmaplot[a]

    long_sigmaplot = pd.DataFrame()
    for a in normalized_sigmaplot:
        for b in time_for_sigmaplot:
            if a.startswith("long") and b.endswith("_"+[i for i in a.split('_') if i.isdigit()][0]):
                long_sigmaplot[b] = time_for_sigmaplot[b]
                long_sigmaplot[a] = normalized_sigmaplot[a]

    lat_sigmaplot = pd.DataFrame()
    for a in normalized_sigmaplot:
        for b in time_for_sigmaplot:
            if a.startswith("lat") and b.endswith("_"+[i for i in a.split('_') if i.isdigit()][0]):
                lat_sigmaplot[b] = time_for_sigmaplot[b]
                lat_sigmaplot[a] = normalized_sigmaplot[a]

    sigmaplot_output = pd.concat([cp_sigmaplot, long_sigmaplot, lat_sigmaplot], ignore_index=False, axis=1)
    return sigmaplot_output


def save_as_excel(df_results, final_file_name, home_directory):
    try:
        # Let's save it:
        df_results.to_excel(f'{final_file_name}.xlsx', index=False)
        print(f"File '{final_file_name}.xlsx' is successfully created in \n{home_directory}")
        sleep(1)
    except FileExistsError:
        print("File with such name already exists.")
        sleep(1)
        pass


def timescales_for_sigmaplot(raw_dt_frame):
    time_for_sigmaplot = pd.DataFrame()
    try:
        for a in raw_dt_frame:
            if a.startswith("time"):
                time_for_sigmaplot[a] = [i - raw_dt_frame[a].loc[3] for i in raw_dt_frame[a]]
    except KeyError:
        pass
    return time_for_sigmaplot[3:]


### Primal block


# We ask for adress:
# Let's make work of user easier - presume that folder is always the folder program is actually in:
home_directory = os.getcwd()
file_adress = home_directory + "\\" + input("Put the name of your file here, please:\n")+".xlsx"
# We generate raw_dataframe out of input data
raw_dt_frame = open_file(file_adress)

# More versatile variant than:
# if ref_decision.endswith("es")
# sigmaplot_decision.strip().lower() == "yes"

### Do we want to take our bleaching into account?
ref_decision = input("Do you want to normalize your data to the reference?(useful if unwanted bleaching is strong) (yes/no)\n")
if ref_decision.strip().lower() == "yes":
    back_decision = input("Do you want to do background substraction as well?(yes/no)\n")
    if back_decision.strip().lower() == "no":
        for a in raw_dt_frame:
            if a.startswith("back"):
                raw_dt_frame[a] = 0
        raw_dt_frame = bleaching_normalization(raw_dt_frame)
        print("Your results will be normalized to the reference without background substraction.")
    else:
        raw_dt_frame = bleaching_normalization(raw_dt_frame)
        print("Your results will be normalized to the reference and background will be substracted.")
else:
    print("Your result won't be normalized to the reference. ")
### Preparational block

# Now we should cut out prebleaches and calculate their means
prebleach_means = prebleach_mean_calc(raw_dt_frame)
# cutting maxes out
postbleach_df_notime = postbleach(raw_dt_frame)
#let's nulify time scale for postbleaches(make it start from 0)
postbleach_df = pb_time_0(postbleach_df_notime)
# Save minimal values for normalization
mins = min_calc(postbleach_df)
# For resulting dataframe calculate final time scales(mean and graphical part)
# we ask for a pace
pace_value = int(input("What should be time pace?(number of seconds, 1 is default)\n"))
new_time_scale = getting_new_time_scale(raw_dt_frame, pace_value)
scaffold_time_scale = pd.DataFrame((new_time_scale["time"])[2:], columns=["time"]) #[2:]    #done!


### Block of time normalization

# We prepare library out of this dataframe for further time adjustment
library = library_creation(postbleach_df)
# We do time adjustment (join values which were taken at one sec by calculating it's mean)
timed_library = time_adjustment(library, pace_value)
# Now it would be beautiful to fuse it back as one dataframe
timed_df = library_to_df(timed_library)
#Let's normalize it now:
normalized_df_for_plot = graph_normalization(timed_df)


### Getting output for plot
df_for_plot = output_for_plot(normalized_df_for_plot, new_time_scale)
# A
final_file_name = input("Tab for graphic plot is ready. Give a name to the output file please.\n")
save_as_excel(df_for_plot, final_file_name, home_directory)

### Sigmaplot analysis
sigmaplot_decision = input("Do you want to generate also tab for the further sigmaplot processing? (yes/no)\n")
if sigmaplot_decision.strip().lower() == "yes":
    time_for_sigmaplot = timescales_for_sigmaplot(raw_dt_frame)
    normalized_sigmaplot = sigmaplot_normalization(raw_dt_frame)
    output_sigmaplot = output_for_sigmaplot(normalized_sigmaplot)

    # Saving
    sigmaplot_file_name = input("Tab for sigma plot is ready. Give a name to the output file please.\n")
    save_as_excel(output_sigmaplot, sigmaplot_file_name, home_directory)


###cutting our dataframe to the shortest collumn
