import boto3, sys
import pandas as pd

"""
Download "csv" or "avi" filenames list from s3 bucket 
- Usage
    1) Download csv filename list: python download_file_list.py csv -> csv.names.txt
    2) Download vid filename list: python download_file_list.py vid -> vid.names.txt
    3) You can change @sensor_list_1(2) and @date_list_1(2) to receive data on the sensor and date you want

"""
ACCESS_KEY = ''
SECRET_KEY = ''
bucket_name = ''
download_list = []

sensor_list_1 = ['s1','s2','s3','s4']
sensor_list_2 = ['s8','s12','s15','s16']

date_list_1 = [
                '2021-09-06','2021-09-07','2021-09-08','2021-09-09','2021-09-10',
                '2021-10-06','2021-10-07','2021-10-08','2021-10-09','2021-10-10',
                '2021-11-06','2021-11-07','2021-11-08','2021-11-09','2021-11-10',
                '2021-12-06','2021-12-07','2021-12-08','2021-12-09','2021-12-10',
                '2022-01-06','2022-01-07','2022-01-08','2022-01-09','2022-01-10',
                '2022-02-06','2022-02-07','2022-02-08','2022-02-09','2022-02-10',
                ]
date_list_2 = [
                '2021-08-01','2021-08-02','2021-08-03','2021-08-04','2021-08-05',
                '2021-09-01','2021-09-02','2021-09-03','2021-09-04','2021-09-05',
                '2021-10-01','2021-10-02','2021-10-03','2021-10-04','2021-10-05',
                '2021-11-01','2021-11-02','2021-11-03','2021-11-04','2021-11-05',
                '2021-12-01','2021-12-02','2021-12-03','2021-12-04','2021-12-05',
                '2022-01-01','2022-01-02','2022-01-03','2022-01-04','2022-01-05',
                '2022-02-01','2022-02-02','2022-02-03','2022-02-04','2022-02-05'
                ]

if __name__ == "__main__":
    option = sys.argv[1]    # csv or vid
    
    s3_client = boto3.client('s3', region_name='ap-northeast-2', aws_access_key_id = ACCESS_KEY, aws_secret_access_key = SECRET_KEY)
    files = s3_client.list_objects_v2(Bucket='tmswsdatabucket')['Contents']
    paginator = s3_client.get_paginator('list_objects')
    page_iterator = paginator.paginate(Bucket=bucket_name)

    # For csv
    if option == 'csv':
        for page in page_iterator:
            try:
                for object in page['Contents']:
                    key = object['Key']

                    format_, sensor, hwrev, fwrev, dt, name = key.split('/')
                    if hwrev == 'hwrev=02' and fwrev == 'fwrev=02':
                        if dt.split('=')[-1] in date_list_1:
                            if name.split('_')[1] in sensor_list_1:
                                download_list.append(key)
                        if dt.split('=')[-1] in date_list_2:
                            if name.split('_')[1] in sensor_list_2:
                                download_list.append(key)
            except Exception as e:
                pass
        
        result = pd.Series(download_list)
        result.to_csv('csv_names.txt', index=False, header=None)

    # For video
    elif option == 'vid':
        for page in page_iterator:
            try:
                for object in page['Contents']:
                    key = object['Key']

                    format_, dt, name = key.split('/')
                    if format_ == 'format=data':
                        continue
                    elif format_ == 'format=video':
                        if dt.split('=')[-1] in date_list_1:
                            if name.split('_')[1].split('.')[0] in sensor_list_1 and name.endswith('avi'):
                                download_list.append(key)
                        if dt.split('=')[-1] in date_list_2:
                            if name.split('_')[1].split('.')[0] in sensor_list_2 and name.endswith('avi'):
                                download_list.append(key)
    
            except Exception as e:
                pass
        
        result = pd.Series(download_list)
        result.to_csv('vid_names.txt', index=False, header=None)
