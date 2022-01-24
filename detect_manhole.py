import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
import copy

"""
manhole_detect: Class to detect a "manhole"
    - get 'AccelX', 'AccelY', 'MagX', 'MagY' in rawdata(@data)
      - Magnetic values are normalized through MinMax scaling (@scaler)
    - When passing through the "manhole", the Acceleration value tends to rise after the magnetic value rises.
      1. Find an index that fluctuate exceed a specific threshold(@lower_threshold, @upper_threshold) after obtaining a local maxima and a local minima from the Magnitude of magnetic Data 
        - To find a local maxima and a local minima, use scipy.signal.argrelextrema
      2. Create a cluster(@clusters) of Accelerations that exceed a specific threshold
        - @clusterAccel 
      3. IF @windowSize and index found in 1 (@suspicious_maxima, @suspicious_minima) is within the range of the Acceleration cluster, it is judged as a "manhole" by satisfying the tendency.
"""
class manhole_detect:

    def __init__(self, parent=None):
        self.parent = parent
        
        self.accel = None
        self.scaled_magnetic = None

        self.order = None
        self.windowSize = None  # Use to Mag -> Accel fluctuate approximation 
        self.overThresholdAccel = None

        self.local_maxima_idx = None
        self.local_maxima_value = None
        self.local_minima_idx = None
        self.local_minima_value = None

        self.local_maxima_gradient = []
        self.local_minima_gradient = []

        self.upper_threshold = 6.0 * pow(10,-4)
        self.lower_threshold = 6.0 * pow(10,-5)

        self.suspicious_maxima = []
        self.suspicious_minima = []

        self.accel_at_manhole = []
        self.magnetic_at_manhole = []
        self.accel_at_manhole_y = []
        self.magnetic_at_manhole_y = []

        self.is_manhole = False

    # Read Accel and Magnetic values from .csv file
    def ReadCSV(self, path):
        data = pd.read_csv(path)
        accel_data = data[['AccelX','AccelY']]
        magnetic_data = data[['MagX','MagY']]
        
        # Min-Max Scaling for Magnetic data 
        scaler = MinMaxScaler()
        scaled_magnetic_data = pd.DataFrame(scaler.fit_transform(magnetic_data), columns=['MagX','MagY'])
        self.accel = (accel_data['AccelX']**2 + accel_data['AccelY']**2)**0.5
        self.scaled_magnetic = (scaled_magnetic_data['MagX']**2 + scaled_magnetic_data['MagY']**2)**0.5
        

    # Helper Function
    # Calculate the order of "argrelextrema" to find the local maxima and local minima
    def getOrderandWindowSize(self):
        mean_cross = []
        magnetic_mean = np.mean(self.scaled_magnetic)

        for i in range(len(self.scaled_magnetic)-1):
            if self.scaled_magnetic[i] < magnetic_mean < self.scaled_magnetic[i+1]:
                mean_cross.append(i)
            elif self.scaled_magnetic[i+1] < magnetic_mean < self.scaled_magnetic[i]:
                mean_cross.append(i)

        diff = []
        for i in range(len(mean_cross)-1):
            diff.append(mean_cross[i+1] - mean_cross[i])
        
        self.windowSize = 2*int(np.mean(diff))
        self.order = int(np.mean(diff)//2)
    
    # Helper Function
    # Create a clutser of Accel that exceed the threshold.
    # Need to Fix: except clusters that contain points less equal than @number
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
        
        self.local_maxima_idx = argrelextrema(self.scaled_magnetic.values, np.greater_equal, order=self.order)[0]
        self.local_minima_idx = argrelextrema(self.scaled_magnetic.values, np.less_equal, order=self.order)[0]
        
        del_max_idx = []
        del_min_idx = []
        
        # Addtional Steps for cleaning noise
        for i in range(len(self.local_maxima_idx)-1):
            if self.local_maxima_idx[i+1] - self.local_maxima_idx[i] < self.order:
                del_max_idx.append(i)
        
        for i in range(len(self.local_minima_idx)-1):
            if self.local_minima_idx[i+1] - self.local_minima_idx[i] < self.order:
                del_min_idx.append(i)
        
        self.local_maxima_idx = np.delete(self.local_maxima_idx, del_max_idx)
        self.local_maxima_value = [self.scaled_magnetic[v] for v in self.local_maxima_idx]

        self.local_minima_idx = np.delete(self.local_minima_idx, del_min_idx)
        self.local_minima_value = [self.scaled_magnetic[v] for v in self.local_minima_idx]

    # plot Accel and Magnetic or local maxima(minima)
    def plotAccelandMagnetic(self):
        fix, axes = plt.subplots(2, 1, figsize=(20,12))
        
        axes[0].set_title("Accel")
        axes[0].plot(self.accel, color='blue')

        for i in range(len(self.accel_at_manhole)):
            axes[0].scatter(self.accel_at_manhole[i], self.accel_at_manhole_y[i], color='red')
    
        axes[1].set_title("Magnetic")
        axes[1].plot(self.scaled_magnetic, label='Magnetic')

        axes[1].plot(self.local_maxima_idx, self.local_maxima_value, color='red')
        axes[1].plot(self.local_minima_idx, self.local_minima_value, color='red')        

        plt.show()

    # Main logic function to detect manhole
    def detectManholeByGradient(self):

        """
        1. In local maxima and local minima, append values exceeding threshold to @suspicious.
        2. Find a cluster of Accel that exceed threshold.
        3. If (cluster's centroid - idx) / self.windowSize < 2, determinde this to be manhole. 
        """

        # Gradients of Maxima and Minima values 
        for i in range(len(self.local_maxima_value)-1):
            gradient_at_i = (self.local_maxima_value[i+1] - self.local_maxima_value[i]) / (self.local_maxima_idx[i+1] - self.local_maxima_idx[i])       
            self.local_maxima_gradient.append([self.local_maxima_idx[i], gradient_at_i])
        
        for i in range(len(self.local_minima_value)-1):
            gradient_at_i = (self.local_minima_value[i+1] - self.local_minima_value[i]) / (self.local_minima_idx[i+1] - self.local_minima_idx[i]) * -1
            self.local_minima_gradient.append([self.local_minima_idx[i], gradient_at_i])
        
        # Threshold
        for idx, gradient in self.local_maxima_gradient:
            if self.lower_threshold < gradient < self.upper_threshold:
                self.suspicious_maxima.append(idx)
            
        for idx, gradient in self.local_minima_gradient:
            if self.lower_threshold < gradient < self.upper_threshold:
                self.suspicious_minima.append(idx)
        
        self.overThresholdAccel = [idx for (idx, acc) in enumerate(self.accel.tolist()) if acc >= 5000]
        clusters = self.clusterAccel()
        
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

        # Used to plotting
        temp = []
        for c in self.accel_at_manhole:
            for i in range(len(c)):
                temp.append(self.accel[c[i]])
            self.accel_at_manhole_y.append(copy.deepcopy(temp))
            temp.clear()

if __name__ == "__main__":
    c = manhole_detect()
    c.ReadCSV("YOUR/PATH/OF/CSV")
    c.getLocalMaximaMinima()
    c.detectManholeByGradient()
    c.plotAccelandMagnetic()