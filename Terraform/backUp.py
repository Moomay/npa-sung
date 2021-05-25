from netmiko import ConnectHandler
from botocore.exceptions import NoCredentialsError
import boto3
import time
import json

ACCESS_KEY = 'AKIAQJQIG5XBMEHDLZ4D'
SECRET_KEY = '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'
# device_ip = ['10.0.15.109', '10.0.15.176', '10.0.15.177']
device_ip = {1:'10.0.15.109', 2:'10.0.15.176', 3:'10.0.15.177'}

 #--------------------------------------send config to s3------------------------------------------------------------------
def upload_to_aws(local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True, local_file 
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False

def set_bucket_policy():
    # Create a bucket policy
    bucket_name = 'fileconfig122'
    bucket_policy = {
        'Version': '2008-10-17',
        'Statement': [{
            'Sid': 'AllowPublicRead',
            'Effect': 'Allow',
            'Principal': {
                "AWS": "*"
            },
            'Action': ['s3:GetObject'],
            'Resource': f'arn:aws:s3:::{bucket_name}/*'
        }]
    }

    # Convert the policy from JSON dict to string
    bucket_policy = json.dumps(bucket_policy)

    # Set the new policy
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=SECRET_KEY)
    s3.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy)

def main():
    set_bucket_policy()
    while 1:
        print("start")
        table = {}
        #-----------------get running config from router and call function upload_to_aws() for send config to s3---------------------------------------------------
        for i in device_ip:
            device_params = {'device_type': 'cisco_ios',
                        'ip': device_ip[i],
                        'username': 'admin',
                        'password': 'cisco',
                        }
            with ConnectHandler(**device_params) as ssh:
                result = ssh.send_command('sh run')
                f = open("router"+str(i)+".txt", "w")
                f.write(result)
                f.close()
                print(upload_to_aws("router"+str(i)+".txt", "fileconfig122", "router"+str(i)+".txt"))
            table["router"+str(i)] = "https://fileconfig122.s3.amazonaws.com/router"+str(i)+".txt"

    #-----------------------------------------------send table of router---------------------------------------------
        json_object = json.dumps(table, indent=4)
        with open("table.json", "w") as tb:
            tb.write(json_object)
            tb.close()
        print(upload_to_aws("table.json", "fileconfig122", "table.json"))
        # time.sleep(60)
        break

main()