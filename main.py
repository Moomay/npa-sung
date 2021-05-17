from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel # New import
from typing import List
from starlette.responses import Response
from netmiko import ConnectHandler
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

# New
book_db = [
    {
        "title":"The C Programming",
        "price": 720
    },
    {
        "title":"Learn Python the Hard Way",
        "price": 870
    },
    {
        "title":"JavaScript: The Definitive Guide",
        "price": 1369
    },
    {
        "title":"Python for Data Analysis",
        "price": 1394
    },
    {
        "title":"Clean Code",
        "price": 1500
    },
]


def requests_info(config_command):
    with ConnectHandler(**device_params) as ssh:
        result = ssh.send_command(config_command)
    return result.split('\n')

def send_config(config_set):
    with ConnectHandler(**device_params) as ssh:
        ssh.send_config_set(config_set)
        result = ssh.send_command('sh ip int b')
    return result.split('\n')

@app.get("/")
async def root():
    return {"message": "Rest API"}

@app.get("/book/")
async def get_books():
    return book_db

@app.get("/intrfaces/")
async def get_interfaces():
    response = requests_info('sh ip int b')
    return response

@app.get("/intrface/{int_id}")
async def get_interfaces(int_id: int):
    interfaces = []
    info = {}
    netmask = requests_info('sh run int gi'+str(int_id))
    netmask = netmask[5].split()[3] if len(netmask[5].split()) == 4 else ""  #Get subnet mask
    int_info = requests_info('sh ip int b')
    #---------------ต้องแก้ให้รับได้หลาย interface Gig, Se, Lo ตอนนี้ได้แค่ Gig
    for i in enumerate(int_info):
        if 'GigabitEthernet'+str(int_id) in i[1]:
            txt = i[1].split()
            info['name'] = txt[0]
            info['enabled'] = txt[4]
            info['address'] = [
                {'ip': txt[1],
                  'netmask': netmask}
            ]
            print(info)
            return info


@app.post("/loopback/{lo_num}/{addr}")
async def create_loopback(lo_num: int, addr: str):
    response = send_config(['int lo'+str(lo_num), 'ip add '+addr])
    return response

# @app.get("/book/{book_id}")
# async def get_books(book_id: int):
#     return book_db[book_id-1]


# ...

# # Model
# class Book(BaseModel):
#     title: str
#     price: float

# ...

# #create new book
# @app.post("/book")
# async def create_book(book: Book):
#     book_db.append(book.dict())
#     return book_db[-1]

# @app.post("/img")
# async def up_img_book(file: UploadFile = File(...)):
#     size = await file.read()
#     return { "File Name": file.filename, "size": len(size)}

# @app.post("/multi-img")
# async def up_multi_file(files: List[UploadFile] = File(...)):
#     file = [
#         {
#             "File Name":file.filename, 
#             "Size":len(await file.read())
#         } for file in files]
#     return  file

# @app.put("/book/{book_id}")
# async def edit_book(book_id: int, book: Book):
#     result = book.dict()
#     book_db[book_id-1].update(result)
#     return result

# @app.delete("/book/{book_id}")
# async def delete_book(book_id: int):
#     book = book_db.pop(book_id-1)
#     return book