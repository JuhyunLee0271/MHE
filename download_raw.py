import os,sys, boto3
import pandas as pd
from multiprocessing import Pool

"""
Download "csv" or "avi" files from s3 bucket with "csv_names.txt", "vid_names.txt" result of download_file_list.py
- Usage
    1) Download csv with "csv_names.txt": python download_raw.py csv
    2) Downlaod vid with "vid_names.txt": python download_raw.py vid
    3) You can change @pwd for your PATH you want
"""

pwd = "C:/Users/JuHyun Lee/Desktop/temp"
ACCESS_KEY = ''
SECRET_KEY = ''
s3_client = boto3.client('s3', region_name='ap-northeast-2', aws_access_key_id = ACCESS_KEY, aws_secret_access_key = SECRET_KEY)
data_list = []
option = sys.argv[1]    # csv or vid

def multiprocess_work(data):
    if option == 'csv':
        for d in data:
            # 2022-02-10 ...
            date = d.split('/')[4].split('=')[-1]
            filename = d.split('/')[-1]
            if not os.path.exists(os.path.join(pwd, date)):
                print(F"make directory: {date}")
                os.mkdir(os.path.join(pwd, date))
            try:
                if not os.path.exists(os.path.join(pwd, date, filename)):
                    s3_client.download_file('tmswsdatabucket', d, os.path.join(pwd, date, filename))
            except Exception as e:
                print(e)
                continue

    elif option == 'vid':
        for d in data:
            date = d.split('/')[1].split('=')[-1]
            filename = d.split('/')[-1]
            if not os.path.exists(os.path.join(pwd, date)):
                print(F"make directory: {date}")
                os.mkdir(os.path.join(pwd, date))
            try:
                if not os.path.exists(os.path.join(pwd, date, filename)):
                    s3_client.download_file('tmswsdatabucket', d, os.path.join(pwd, date, filename))
            except Exception as e:
                print(e)
                continue        

if __name__ == "__main__":
    if option == 'csv':
        with open('csv_names.txt', 'r') as f:
            lines = f.readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].strip('\n')
    
    elif option == 'vid':
        with open('vid_names.txt', 'r') as f:
            lines = f.readlines()
        for i in range(len(lines)):
            lines[i] = lines[i].strip('\n')

    data_num = len(lines)
    cpu_num = os.cpu_count()
    data_per_process = data_num // cpu_num

    for i in range(cpu_num):
        data_list.append(lines[i*data_per_process: (i+1)*data_per_process])
    data_list[-1] = lines[(cpu_num-1)*data_per_process:]

    print(F"Downloading...")
    pool = Pool(processes=cpu_num)
    pool.map(multiprocess_work, data_list)
    pool.close()
    pool.join()

