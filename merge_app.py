from fastapi import FastAPI, File, UploadFile, Body, Header
from pydantic import BaseModel
from typing import Optional
from typing import List
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.routing import Route
from netmiko import ConnectHandler
from ntc_templates.parse import parse_output
import json
import base64

class ip_addr(BaseModel):
    loopback_number: int
    ip: str
    netmask: str

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

def get_device_param(ip, Authorization):
    l = base64.b64decode(Authorization.replace("Basic ", ""))
    l = str(l.decode("utf-8"))
    device_ip = ip
    username = l[:l.find(":")]
    password = l[l.find(":")+1:]
    device_params = {'device_type': 'cisco_ios',
                 'ip': device_ip,
                 'username': username,
                  'password': password,
    }
    return device_params

def requests_info(config_command, device_params):
    with ConnectHandler(**device_params) as ssh:
        result = ssh.send_command(config_command)
    return result.split('\n')

def send_config_set(config_set, device_params):
    with ConnectHandler(**device_params) as ssh:
        ssh.send_config_set(config_set)
    return "succeed"

def send_config(config_set, device_params):
    with ConnectHandler(**device_params) as ssh:
        ssh.send_config_set(config_set)

async def get_interface(request):
    interface = request.path_params['interface']
    result = requests_info("sh ip int "+interface.replace("=", ""))
    return PlainTextResponse(str(result))


routes = [
    Route("/interface/{interface:path}", endpoint=get_interface, methods=["GET"]),
]

app = FastAPI(routes=routes)

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
async def get_interfaces(ip: str = Header(None), Authorization: str = Header(None)):
    device_params = get_device_param(ip, Authorization)
    interfaces = []
    info = {}
    response = requests_info('sh ip int b', device_params)
    for i in response[1:]:
        i = i.split()
        print(i)
        info['name'] = i[0]
        info['enabled'] = "up" if i[4] == 'up' else "down"
        info['address'] = {
            "ip": i[1],
            "netmask": netmask(requests_info('sh run int '+i[0], device_params))
        }
        interfaces.append(info)
        info = {}
    return interfaces

#-----------------------------------------------Create Loopback------------------------------------------------

@app.post("/loopback")
async def create_loopback(ip_a:ip_addr, ip: str = Header(None), Authorization: str = Header(None)):
    device_params = get_device_param(ip, Authorization)
    response = send_config(['int lo'+str(ip_a.dict()['loopback_number']), 'ip add '+ip_a.dict()['ip']+' '+ip_a.dict()['netmask']])
    response = requests_info('sh ip int b', device_params)
    return response


#-----------------------------------------------Automate Route OSPF--------------------------------------------
@app.post("/route")
async def route(ip: str = Header(None), Authorization: str = Header(None)):
    device_params = get_device_param(ip, Authorization)
    cmd = ['router ospf 1']  
    result = requests_info('sh ip route', device_params)
    for i in result[result.index('')+3:]:
      if i.split()[0] == 'C':
        cmd.append('network '+str(IPv4Network(i.split()[1]).network_address)+' '+str(IPv4Address(int(IPv4Address(IPv4Network(i.split()[1]).netmask))^(2**32-1)))+' area 0')
    send_config(cmd, device_params)
    return 200

#-----------------------------------------------Get Access list--------------------------------------------

@app.get("/accesslist")
async def get_accesslist(ip: str = Header(None), Authorization: str = Header(None)):
    device_params = get_device_param(ip, Authorization)
    result = requests_info("sh run | i access-list", device_params)
    return result
#-----------------------------------------------Config Access list--------------------------------------------
@app.post("/accesslist")
async def post_access(allAcl: AccessList, ip: str = Header(None), Authorization: str = Header(None)):
    device_params = get_device_param(ip, Authorization)
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
        send_config_set(config_setExt, device_params)
    return config_setStd, config_setExt

@app.post("/accesslist/template")
async def to_template(config: ConfigsList):
    device_params = get_device_param(ip, Authorization)
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
async def set_interface(interfaceList: InterfaceList, ip: str = Header(None), Authorization: str = Header(None)):
    device_params = get_device_param(ip, Authorization)
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
    send_config(config_set, device_params)
    return config_set
