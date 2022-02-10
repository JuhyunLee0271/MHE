import pandas as pd
import os, boto3, sys
from datetime import datetime
from multiprocessing import Pool

"""
Download Pothole Video from s3 bucket on a given date using "pothole_gps_clustered.csv"
- Parse the pothole data of a specific date by reading "pothole_gps_clustered.csv" 
- Date is passed as a parameter when executing the program (default = today)
- Download the same video as the filename from the s3 bucket with multiprocessing
- Can change the number of cores by changing @process_num
- Usage 
        1) "python pothole-vid-download-multi.py"
        2) "python pothole-vid-download-multi.py 2022-02-08"

"""
BUCKET_BASE_PATH = 'format=video/sensor=sws/dt='
bucket_name = 'swmdatabucket'
s3 = boto3.resource('s3')
working_directory = os.getcwd()

def multiprocess_work(data):
    for idx, row in data.iterrows():
        date = row.time.split(' ')[0];  filename = row.time.split(' ')[-1]
        longitude = row.longitude;  latitude = row.latitude;    phLevel = row.severity

        download_path = BUCKET_BASE_PATH + str(date) + '/labeled' + '/Ph' + str(phLevel) + '/' + str(filename) + '.mp4'
        target_file_path= working_directory + "/" + date + "/" + filename + ".mp4"
        
        if not os.path.exists(os.path.join(working_directory, date)):
            os.mkdir(os.path.join(working_directory, date))
        
        if not os.path.exists(target_file_path):
            try:
                s3.meta.client.download_file(bucket_name, download_path, target_file_path)
            except Exception as e:
                print(F"Exception: {e}")
                pass
            
if __name__ == "__main__":
    target = datetime.now().strftime("%Y-%m-%d") if len(sys.argv) == 1 else sys.argv[1]
    
    data = pd.read_csv(working_directory + "/pothole_gps_clustered.csv")
    for idx, row in data.iterrows():
        date = row.time.split(' ')[0];  filename = row.time.split(' ')[-1]
        if date != target:
            data.drop(idx, inplace=True)

    data_num = len(data)
    process_num = 4
    
    data_per_process = data_num // process_num
    data_list = []
    
    for i in range(process_num):
        data_list.append(data.iloc[i*data_per_process: (i+1)*data_per_process])
    data_list[-1] = data.iloc[(process_num-1)*data_per_process:]

    print(F"Download Pothole Video ({target})")
    pool = Pool(processes=process_num)
    pool.map(multiprocess_work, data_list)
    pool.close()
    pool.join()
    