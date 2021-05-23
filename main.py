from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel # New import
from typing import List
from starlette.responses import Response
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
from ipaddress import *
import json

app = FastAPI()

device_ip = '10.0.15.109'
username = 'admin'
password = 'cisco'
device_params = {'device_type': 'cisco_ios',
                 'ip': device_ip,
                 'username': username,
                  'password': password,
                }



def requests_info(config_command):
    with ConnectHandler(**device_params) as ssh:
        result = ssh.send_command(config_command)
    return result.split('\n')

def send_config(config_set):
    with ConnectHandler(**device_params) as ssh:
        ssh.send_config_set(config_set)
    #     result = ssh.send_command(res)
    # return result.split('\n')
    
#----------------------------------------------Find netmask--------------------------------------------------------------
def netmask(data): 
    for i in data:
        if i.find("no ip") != -1:
            return "unassigned"
        elif i.find("255") != -1:
            return i.split()[3]

@app.get("/")
async def root():
    return {"message": "Rest API"}

#-----------------------------------------------Show Interfaces-------------------------------------------------
@app.get("/intrfaces/")
async def get_interfaces():
    interfaces = []
    info = {}
    response = requests_info('sh ip int b')
    for i in response[1:]:
        i = i.split()
        print(i)
        info['name'] = i[0]
        info['enabled'] = "up" if i[4] == 'up' else "down"
        info['address'] = {
            "ip": i[1],
            "netmask": netmask(requests_info('sh run int '+i[0]))
        }
        interfaces.append(info)
        info = {}
    return interfaces

#-----------------------------------------------Create Loopback------------------------------------------------
@app.post("/loopback/{loopback_no}/{addr}")
async def create_loopback(loopback_no: int, addr: str):
    response = send_config(['int lo'+str(loopback_no), 'ip add '+addr])
    return response


#-----------------------------------------------Automate Route OSPF--------------------------------------------
@app.post("/route")
async def route():
    cmd = ['router ospf 1']  
    result = requests_info('sh ip route')
    for i in result[result.index('')+3:]:
      if i.split()[0] == 'C':
        cmd.append('network '+str(IPv4Network(i.split()[1]).network_address)+' '+str(IPv4Address(int(IPv4Address(IPv4Network(i.split()[1]).netmask))^(2**32-1)))+' area 0')
    send_config(cmd)
    return 200


