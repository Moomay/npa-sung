from fastapi import FastAPI, File, UploadFile, Body
from pydantic import BaseModel # New import
from typing import Optional
from typing import List
#from starlette.responses import Response
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
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

class Interface(BaseModel):
    interface: str
    ip: str #case DHCP
    subnet: Optional[str] = None
    status: str #up // down
    aclIngress: Optional[int] = None
    aclEgress: Optional[int] = None

class InterfaceList(BaseModel):
    interfaceList: list[Interface]

class ConfigsList(BaseModel):
    configList: list[str]
    description: Optional[str] = None

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
    Route("/interface/{interface:path}", endpoint=get_interface, methods=["GET"]),
]

app = FastAPI(routes=routes)

@app.get("/accesslist")
async def get_accesslist():
    result = requests_info("sh run | i access-list")
    return result

@app.post("/accesslist")
async def post_access(allAcl: AccessList):
    allAcl = allAcl.dict()
    if ("standardAccessList" in allAcl.keys()):
        config_setStd = ["access-list "+str(accl["access_list_number"])+" "+accs["action"]+" "+
        (accs["ip"])+str("" if accs["wildcard"] == None else " "+
        str(accs["wildcard"])) for accl in allAcl["standardAccessList"] for accs in accl["access_control_list"]]
        send_config(config_setStd)
    if ("extendAccessList" in allAcl.keys()):
        config_setExt = ["access-list "+str(accl["access_list_number"])+" "+acce["action"]+" "+
        acce["protocol"]+(" host " if acce["source_wildcard"] == None and acce["source"] != "any" else " ")+
        acce["source"]+("" if acce["source_wildcard"] == None else " "+acce["source_wildcard"])+
        ("" if acce["form_port"] == None else " eq "+acce["form_port"])+
        (" host " if acce["destination_wildcard"] == None and acce["destination"] != "any" else " ")+
        acce["destination"]+("" if acce["destination_wildcard"] == None else " "+acce["destination_wildcard"])+
        ("" if acce["to_port"] == None else " eq "+acce["to_port"]) for accl in allAcl["extendAccessList"] for acce in accl["access_control_list"]]
        send_config_set(config_setExt)
    return config_setStd, config_setExt

@app.post("/accesslist/template")
async def to_template(config: ConfigsList):
    config = config.dict()
    stdAclNumset = []
    extAclNumset = []
    accessls = {'extendAccessList': [],
    'standardAccessList': []
    }
    for line in config["configList"]:
        l = line.split() #l is word seperater in line
        x = dict()       #x is access list
        access_num = int(l[1])
        action = l[2]
        x["action"] = action
        #Check Defind Acl
        if (int(access_num) < 100 and access_num not in stdAclNumset):
            stdAclNumset.append(access_num)
            accessls["standardAccessList"].append({"access_list_number": access_num, "access_control_list": []})
        elif (int(access_num) >= 100 and access_num not in extAclNumset):
            extAclNumset.append(access_num)
            accessls["extendAccessList"].append({"access_list_number": access_num, "access_control_list": []})
        #Check Type Access List
        if (int(access_num) < 100):
        #std
            if (l[3] == "host"):
                ip = l[4]
                x["ip"] = ip
            else:
                ip = l[3]
                x["ip"] = ip
            if (len(l) == 5 and l[3] != "host"):
                wildcard = l[4]
                x["wildcard"] = wildcard
            accessls["standardAccessList"][stdAclNumset.index(access_num)]["access_control_list"].append(x)
        else:
        #extend
            protocol = l[3]
            x["protocol"] = protocol
            if (l[4] == "host"):
            #case host
                sourceIP = l[5]
                x["source"] = sourceIP
                index = 6
            elif (l[4] == "any"):
            #case any
                sourceIP = l[4]
                x["source"] = sourceIP
                index = 5
            else:
            #case wildcard
                sourceIP = l[4]
                x["source"] = sourceIP
                sourceWildcard  = l[5]
                x["source_wildcard"] = sourceWildcard
                index = 6
            if (protocol == "tcp"):
            #case tcp have port
                if (l[index] == "eq"):
                    form_port = l[index+1]
                    x["form_port"] = form_port
                    index += 2
            if (l[index] == "host"):
                destIp = l[index+1]
                x["destination"] = destIp
                index += 2
            elif (l[index] == "any"):
                destIp = l[index]
                x["destination"]= destIp
                index += 1
            else:
                destIp = l[index]
                x["destination"] = destIp
                destWildcard = l[index+1]
                x["destination_wildcard"] = destWildcard
                index += 2
            if (protocol == "tcp" and len(l) > index):
                if (l[index] == "eq"):
                    to_port = l[index+1]
                    x["to_port"] = to_port
            accessls["extendAccessList"][extAclNumset.index(access_num)]["access_control_list"].append(x)
    #delete useless list
    if (len(accessls["extendAccessList"]) == 0):
        accessls.pop("extendAccessList")
    if (len(accessls["standardAccessList"]) == 0):
        accessls.pop("standardAccessList")
    return accessls

@app.post("/interface")
async def set_interface(interfaceList: InterfaceList):
    interfaceList = interfaceList.dict()
    config_set = []
    for interface in interfaceList["interfaceList"]:
        config_set.append("int "+interface["interface"])
        if (interface["subnet"] != None):
            config_set.append("ip add "+interface["ip"]+" "+str(interface["subnet"]))
        else:
            config_set.append("ip add "+interface["ip"])
        if (interface["status"] == "up"):
            config_set.append("no shut")
        else:
            config_set.append("shut")
        if ("aclIngress" in interface.keys()):
            config_set.append("ip access-group "+str(interface["aclIngress"])+" in")
        if ("aclEgress" in interface.keys()):
            config_set.append("ip access-group "+str(interface["aclEgress"])+" out")
    send_config(config_set)
    return config_set
