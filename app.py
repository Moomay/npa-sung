from fastapi import FastAPI, File, UploadFile, Body
from pydantic import BaseModel # New import
from typing import Optional
#from typing import List
#from starlette.responses import Response
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from netmiko import ConnectHandler
from urllib.parse import unquote
import json

class StandardAccessControl(BaseModel):
    action: str #permit deny
    ip: str
    description: Optional[str] = None
    wildcard : Optional[str] = None

class ExtendAccessControl(BaseModel):
    action: str
    description: Optional[str] = None
    protocol: str
    source: str #case any case host
    source_wildcard: Optional[str] = None
    form_port: Optional[str] = None
    destination: str #case any case host
    destination_wildcard: Optional[str] = None
    to_port: Optional[str] = None

class StandardAccessList(BaseModel):
    access_list_number: int #1-99
    description: Optional[str] = None
    access_control_list: list[StandardAccessControl]

class ExtendAccessList(BaseModel):
    access_list_number: int #100-199
    description: Optional[str] = None
    access_control_list: list[ExtendAccessControl]

class AccessList(BaseModel):
    standardAccessList: Optional[list[StandardAccessList]] = None
    extendAccessList: Optional[list[ExtendAccessList]] = None

def requests_info(config_command):
    with ConnectHandler(**device_params) as ssh:
        result = ssh.send_command(config_command)
    return result.split('\n')

def send_config_set(config_set):
    with ConnectHandler(**device_params) as ssh:
        ssh.send_config_set(config_set)
    return "succeed"
def send_config(config_set):
    with ConnectHandler(**device_params) as ssh:
        ssh.send_config_set(config_set)
        result = ssh.send_command('sh ip int b')
    return result.split('\n')

async def get_interface(request):
    interface = request.path_params['interface']
    result = requests_info("sh ip int "+interface.replace("=", ""))
    return PlainTextResponse(str(result))

device_ip = '10.0.15.43'
username = 'admin'
password = 'cisco'
device_params = {'device_type': 'cisco_ios',
                 'ip': device_ip,
                 'username': username,
                  'password': password,
                }
routes = [
    Route("/interface/{interface:path}", endpoint=get_interface),
]

app = FastAPI(routes=routes)

@app.get("/accesslist")
async def get_accesslist():
    result = requests_info("sh run | i access")
    return result

@app.post("/accesslist")
async def post_access(testAcl: AccessList):
    accesslist = []
    return testAcl
