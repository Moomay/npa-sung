from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel # New import
from typing import Optional
#from typing import List
#from starlette.responses import Response
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from netmiko import ConnectHandler
from urllib.parse import unquote
import json


def requests_info(config_command):
    with ConnectHandler(**device_params) as ssh:
        result = ssh.send_command(config_command)
    return result.split('\n')

def send_config(config_set):
    with ConnectHandler(**device_params) as ssh:
        ssh.send_config_set(config_set)
        result = ssh.send_command('sh ip int b')
    return result.split('\n')

async def get_interface(request):
    interface = request.path_params['interface']
    result = requests_info("sh ip int "+interface.replace("=", ""))
    return PlainTextResponse(str(result))

device_ip = '10.0.15.42'
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




@app.get("/test")
async def test():
    return {"Hello": "World"}

