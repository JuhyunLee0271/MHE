import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
import copy, boto3, os
from multiprocessing import Pool

"""
After parsing "pothole_gps.csv" and downloading the file from the s3 bucket, 
and use @manhole_detect to determine whether it is a manhole By Multiprocessing with Pool
"""

# Manhole Detector
class manhole_detect:
    def __init__(self, parent=None):
        self.parent = parent
        
        self.accel = None
        self.magnetic = None

        self.order = None
        self.windowSize = None  # Use to Mag -> Accel fluctuate approximation 
        self.overThresholdAccel = None

        self.local_maxima_idx = None
        self.local_maxima_value = None
        self.local_minima_idx = None
        self.local_minima_value = None

        self.local_maxima_diff = []
        self.local_minima_diff = []
        
        self.lower_threshold = 50
        self.upper_threshold = 1000
        
        self.accel_outlier_threshold = 20000
        self.magn_outlier_threshold = 10000

        self.suspicious_maxima = []
        self.suspicious_minima = []

        self.accel_at_manhole = []
        self.accel_at_manhole_y = []
        
        self.magnetic_at_manhole = []
        self.magnetic_at_manhole_y = []

        self.is_manhole = False

    # Read Accel and Magnetic values from .csv file
    def ReadCSV(self, path):
        data = pd.read_csv(path)
        accel_data = data[['AccelX','AccelY']]
        magnetic_data = data[['MagX','MagY']]
                
        # Cleaning for outliers
        self.accel = (accel_data['AccelX']**2 + accel_data['AccelY']**2)**0.5
        self.accel = pd.Series([v for v in self.accel if 0 < v < self.accel_outlier_threshold])
        
        self.magnetic = ((magnetic_data['MagX']**2 + magnetic_data['MagY']**2)**0.5).to_list()
        self.magnetic = pd.Series([v for v in self.magnetic if 0 < v < self.magn_outlier_threshold])
        
    # Helper Function
    # Calculate the order of "argrelextrema" to find the local maxima and local minima
    def getOrderandWindowSize(self):
        mean_cross = []
        magnetic_mean = np.mean(self.magnetic)

        for i in range(len(self.magnetic)-1):
            if self.magnetic[i] < magnetic_mean < self.magnetic[i+1]:
                mean_cross.append(i)
            elif self.magnetic[i+1] < magnetic_mean < self.magnetic[i]:
                mean_cross.append(i)

        diff = []
        for i in range(len(mean_cross)-1):
            diff.append(mean_cross[i+1] - mean_cross[i])
        
        self.windowSize = 2*int(np.mean(diff))
        self.order = int(np.mean(diff))
    
    # Helper Function
    # Create a clutser of Accel that exceed the threshold.
    # Need to Fix: except clusters that contain points less equal than @number -> Set 20 (pending)
    def clusterAccel(self):
        cluster = []
        temp = []

        for i in range(len(self.overThresholdAccel)):
            if temp:
                centroid = sum(temp) / len(temp)
                if (self.overThresholdAccel[i] - centroid) < self.windowSize:
                    temp.append(self.overThresholdAccel[i])
                else:
                    cluster.append(copy.deepcopy(temp))
                    temp.clear()
                    temp.append(self.overThresholdAccel[i])
            else:
                temp.append(self.overThresholdAccel[i])
            
            if i == len(self.overThresholdAccel) - 1:
                cluster.append(copy.deepcopy(temp))
        
        return cluster

    # Get local maxima(minima) idx, values
    def getLocalMaximaMinima(self):
        self.getOrderandWindowSize()
        
        self.local_maxima_idx = argrelextrema(self.magnetic.values, np.greater_equal, order=self.order)[0]
        self.local_minima_idx = argrelextrema(self.magnetic.values, np.less_equal, order=self.order)[0]
    
        del_max_idx = []
        del_min_idx = []
        
        # Addtional Steps for cleaning noise
        for i in range(len(self.local_maxima_idx)-1):
            if self.local_maxima_idx[i+1] - self.local_maxima_idx[i] < self.order:
                del_max_idx.append(i)
        
        for i in range(len(self.local_minima_idx)-1):
            if self.local_minima_idx[i+1] - self.local_minima_idx[i] < self.order:
                del_min_idx.append(i)
        
        self.local_maxima_idx = np.delete(self.local_maxima_idx, del_max_idx).tolist()
        self.local_maxima_value = [self.magnetic[v] for v in self.local_maxima_idx]

        self.local_minima_idx = np.delete(self.local_minima_idx, del_min_idx).tolist()
        self.local_minima_value = [self.magnetic[v] for v in self.local_minima_idx]
        
        del_max_idx.clear()
        del_min_idx.clear()
            
        # Cleaning outliers
        for i in range(len(self.local_maxima_value)):
            if self.local_maxima_value[i] > self.magn_outlier_threshold:
                del_max_idx.append(i)
        
        self.local_maxima_idx = np.delete(np.array(self.local_maxima_idx), del_max_idx).tolist()
        self.local_maxima_value = np.delete(np.array(self.local_maxima_value), del_max_idx).tolist()

    # Main logic function to detect manhole
    def detectManholeByDiff(self):
        """
        1. In local maxima and local minima, append values exceeding threshold to @suspicious.
        2. Find a cluster of Accel that exceed threshold.
        3. If (cluster's centroid - idx) / self.windowSize < 2, determinde this to be manhole. 
        """
    
        # Diff of Maxima and Minima values 
        for i in range(len(self.local_maxima_value)-1):
            diff_at_i = (self.local_maxima_value[i+1] - self.local_maxima_value[i])
            self.local_maxima_diff.append([self.local_maxima_idx[i], diff_at_i])
        
        for i in range(len(self.local_minima_value)-1):
            diff_at_i = (self.local_minima_value[i+1] - self.local_minima_value[i])*-1
            self.local_minima_diff.append([self.local_minima_idx[i], diff_at_i])
        
        # Threshold
        for idx, diff in self.local_maxima_diff:
            if self.lower_threshold < diff < self.upper_threshold:
                self.suspicious_maxima.append(idx)
            
        for idx, diff in self.local_minima_diff:
            if self.lower_threshold < diff < self.upper_threshold:
                self.suspicious_minima.append(idx)
        
        self.overThresholdAccel = [idx for (idx, acc) in enumerate(self.accel.tolist()) if acc >= 5000]
        clusters = self.clusterAccel()
        if not clusters:
            self.is_manhole = False
            return

        # Magnetic increase -> Accelerator increase: manhole
        for idx in self.suspicious_maxima:
            for c in clusters:
                avg = int(sum(c) / len(c))
                if (abs(avg - idx) / self.windowSize) < 2:
                    self.magnetic_at_manhole.append(idx)
                    if c not in self.accel_at_manhole and len(c) > 20:
                        self.accel_at_manhole.append(c)

        for idx in self.suspicious_minima:
            for c in clusters:
                avg = int(sum(c) / len(c))
                if (abs(avg - idx) / self.windowSize) < 2:
                    self.magnetic_at_manhole.append(idx)
                    if c not in self.accel_at_manhole and len(c) > 20:
                        self.accel_at_manhole.append(c)
        
        if self.magnetic_at_manhole and self.accel_at_manhole:
            self.is_manhole = True

POTHOLE_GPS_PATH = "/home/ubuntu/s3_data/GPS/pothole_gps_new.csv"
POTHOLE_GPS_RESULT_PATH = "/home/ubuntu/s3_data/GPS/pothole_gps_new_result.csv"
BUCKET_BASE_PATH = 'format=data/sensor=sws/hwrev=01/fwrev=01' + '/dt='

bucket_name = 'swmdatabucket'
s3 = boto3.resource('s3')

# Multiprocessing
def multiprocess_work(pothole_gps):
    for idx, row in pothole_gps.iterrows():
        date = row.time.split(' ')[0];  filename = row.time.split(' ')[-1]
        longitude = row.longitude;  latitude = row.latitude;    phLevel = row.severity

        download_path = BUCKET_BASE_PATH + str(date) + '/labeled' + '/Ph' + str(phLevel) + '/' + str(filename) + '.csv'
        target_file_path = os.getcwd() + "/" + filename + ".csv"

        try:
            s3.meta.client.download_file(bucket_name, download_path, target_file_path)
            detector = manhole_detect()            
            detector.ReadCSV(download_path.split('/')[-1])
            detector.getLocalMaximaMinima()
            detector.detectManholeByDiff()
            
            # remove manhole 
            if detector.is_manhole:
                pothole_gps.drop(idx, inplace=True)

            os.remove(target_file_path)
            del detector
            
        except:
            # remove files without csv
            pothole_gps.drop(idx, inplace=True)
            pass

    return pothole_gps

if __name__ == "__main__":
    pothole_gps = pd.read_csv(POTHOLE_GPS_PATH)
    
    # Equally allocating data to 8 processes.
    data_list = [
        pothole_gps.iloc[0:25000],pothole_gps.iloc[25000:50000], pothole_gps.iloc[50000:75000], pothole_gps.iloc[75000:100000:],
        pothole_gps.iloc[100000:125000], pothole_gps.iloc[125000:150000], pothole_gps.iloc[150000:175000], pothole_gps.iloc[175000:]
    ]

    pool = Pool(processes=8)
    # Concatenate each of the eight results.
    result = pd.concat(pool.map(multiprocess_work, data_list))

    # Wait until another process is over.
    pool.close()
    pool.join()
    
    # Cleaning for data (logitude, latitude) = (0.0 0.0)
    for idx, row in result.iterrows():
        if row.latitude == row.longitude == 0.0:
            result.drop(idx, inplace=True)

    # Save Result
    result.to_csv(POTHOLE_GPS_RESULT_PATH, sep=',', index=False)
    