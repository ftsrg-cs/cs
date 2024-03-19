from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, ASYNCHRONOUS
from datetime import datetime, timedelta
from time import sleep
import pandas as pd

data = pd.read_csv("areas.csv")
piv = data.pivot(index="TIME",  columns="AREA NAME", values="MW")
tags = {
    "host": "simulator",
    "name": "device",
    "type": "holding_register",
    "slave_id": "1"
}


# alternatively: client = InfluxDBClient(url="localhost:8086", token="INSERT TOKEN HERE", org="InfluxData")
client = InfluxDBClient.from_config_file("config.ini")
writer = client.write_api(write_options=SYNCHRONOUS)
for (idx, cols) in piv.iterrows():
    time = datetime.now()
    point = Point("modbus")
    for (key, val) in cols.to_dict().items():
        point.field(key, 0.0 if(val == 9999) else val)
    for (key, val) in tags.items():
        point.tag(key, val)
    writer.write("node8", record=point)
    print(point.to_line_protocol())
    sleep(2)
