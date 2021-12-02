# запускать в отдельных окнах редактора

from time import sleep
from comm import *


log = MedaLogging()
client = ClientMain('127.0.0.1', 1234, log)

outputdata = {'hello': 'hello client', 'int': 1, 'float': 1.1233, 'list': [1, 2, 3, 4, 45]}

while True:
    inputdata = client.ClientReceivin()
    client.ClientDispatch(outputdata)
    print(inputdata)
    sleep(1)

