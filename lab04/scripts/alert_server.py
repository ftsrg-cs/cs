from flask import Flask, request, json

app = Flask(__name__)


@app.route("/")
def welcome():
    return "Welcome to the Citical Systems Laboratory InfluxDB lab alert test service!"


@app.route("/co2", methods=['POST'])
def co2():
    data = json.loads(request.data)
    print("Notification sent to CO2 message: ")
    print(str(data["_message"]))
    return "Notification sent to CO2 ! "+str(request.data)


@app.route("/down", methods=['POST'])
def down():
    data = json.loads(request.data)
    print(str(data["_message"]))
    print("Notification sent to down")
    return "Notification sent to down"


@app.route("/diff", methods=['POST'])
def diff():
    data = json.loads(request.data)
    print(str(data["_message"]))
    print("Notification sent to diff")
    return "Notification sent to diff"
