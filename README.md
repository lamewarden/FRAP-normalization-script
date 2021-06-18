# FRAP-normalization-script
Short description.


Program is written to facilitate repetitive calculations of fluorescence recovery after photobleaching (FRAP).
For correct work, program requires python 3.6 and above - https://www.python.org/downloads/. 

Program works with max 3 ROIs at once (plus  one background and  one reference ROIs). Number of samples is unlimited.
Names of columns with each ROI data are fixed as follows: col_1(or another number), long_1 and lat_1. 
Columns with background, reference and time, should be named by the same model: back_1, ref_1 and time_s_1 respectively.
Input format should look like following exaple:

|time_s_1|back_1|ref_1  |cp_1   |long_1  |lat_1|time_s_2|back_2|
|0	   |24.332|161.397|398.839|	173.005|NaN	 | 0	  |23.092| etc....

If less than 3 ROIs per sample needed, user can simply leave column with respective name empty.


Output for graphic plot undergoes time conversion. 
It's necessary because different samples often has slightly different pace, so mean and SEM cannot be calculated easily.
Each measurement is assigned to 1 sec interval. If for 1 interval we have more than 1 measurement -
we calculate mean of those. 
The conversion allows free comparison and averaging of measurements with any pace below or equal 1 s.
It overall doesn't influence curve's shape, but can slightly affect separate time points(as average is calculated).
If you don't want to make any time conversion - use tab for sigmaplot as result.


Program gets excel tab as an input, extracts columns of interest, normalizes them,
normalizes bleached ROIs to non-bleached reference (optional, recommended if undesired bleaching is too strong),
subtracts background (optional), transforms timescale, calculates mean, standard error of the mean and groups
output to the new excell tab.
Created by Kashkan Ivan. 2019.02.12
