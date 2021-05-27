from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import requests




app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def get_index():
    url = "https://fileconfig122.s3.amazonaws.com/router1.txt"
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    response1 = response.text.replace("!","!<br>")

    url = "https://fileconfig122.s3.amazonaws.com/router2.txt"
    payload={}
    headers = {}
    response2 = requests.request("GET", url, headers=headers, data=payload)
    response2 = response2.text.replace("!","!<br>")

    url = "https://fileconfig122.s3.amazonaws.com/router3.txt"
    payload={}
    headers = {}
    response3 = requests.request("GET", url, headers=headers, data=payload)
    response3 = response3.text.replace("!","!<br>")
    t = """<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/css/bootstrap.min.css" rel="stylesheet"
        integrity="sha384-+0n0xVW2eSR5OomGNYDnhzAbDsOXxcvSN1TPprVMTNDbiYZCxYbOOl7+AMvyTG2x" crossorigin="anonymous">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.1/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-gtEjrD/SeCtmISkJkNUaaKMoLD0//ElJ19smozuHV6z3Iehds+3Ulb9Bn9Plx0x4"
        crossorigin="anonymous"></script>
    <title>Config</title>
    <style>
        div.ex3 {
            height: 250pt;
            width: 80%;
            overflow-y: auto;
            background-color: black;

        }

        .col {
            padding: 10px;
        }
        .card-body{
            color:white;
            padding: 0px;
        }
        .topcard{
            width: 100%;
            height: 10%;
            background-color: rgb(151, 151, 151);
            display: flex;
            align-items: baseline;
            
        }
        .textzone{
            padding: 10px;
        }
        .curred{
            width: 20px;
            height: 20px;
            background-color: red;
            border-radius: 50px;
            margin-left: 5px;
            margin-top: 5px;
        }
        .curyellow{
            width: 20px;
            height: 20px;
            background-color: yellow;
            border-radius: 50px;
            margin-left: 5px;
        }
        .curgreen{
            width: 20px;
            height: 20px;
            background-color: green;
            border-radius: 50px;
            margin-left: 5px;
        }
        .toptext{
            position: relative;
            left: 40%;
        }
    </style>
</head>

<body>

    <div class="container">
        <div class="row align-items-center">
            <div class="col">
                <button class="btn btn-primary" type="button" data-bs-toggle="collapse"
                    data-bs-target="#collapseExample" aria-expanded="false" aria-controls="collapseExample">
                    Show config Router1
                </button>

                <div class="collapse" id="collapseExample">
                    <div class="card card-body ex3 border ">
                        <div class="topcard">
                            <div class="curred"></div>
                            <div class="curyellow"></div>
                            <div class="curgreen"></div>
                            <p class="toptext">BEST</p>
                        </div>
                        <div class="textzone">"""+response1+"""
                    </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="container">
        <div class="row align-items-center">
            <div class="col">
                <button class="btn btn-primary" type="button" data-bs-toggle="collapse"
                    data-bs-target="#collapseExample2" aria-expanded="false" aria-controls="collapseExample2">
                    Show config Router2
                </button>

                <div class="collapse" id="collapseExample2">
                    <div class="card card-body ex3 border ">
                        <div class="topcard">
                            <div class="curred"></div>
                            <div class="curyellow"></div>
                            <div class="curgreen"></div>
                            <p class="toptext">BEST</p>
                        </div>
                        <div class="textzone">"""+response2+"""
                    </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <div class="container">
        <div class="row align-items-center">
            <div class="col">
                <button class="btn btn-primary" type="button" data-bs-toggle="collapse"
                    data-bs-target="#collapseExample3" aria-expanded="false" aria-controls="collapseExample3">
                    Show config Router3
                </button>

                <div class="collapse" id="collapseExample3">
                    <div class="card card-body ex3 border ">
                        <div class="topcard">
                            <div class="curred"></div>
                            <div class="curyellow"></div>
                            <div class="curgreen"></div>
                            <p class="toptext">BEST</p>
                        </div>
                        <div class="textzone">"""+response3+"""
                    </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>

"""

    return t