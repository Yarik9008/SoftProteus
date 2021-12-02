# запускать в отдельных окнах редактора 

from time import sleep
from comm import *


log = MedaLogging()
server = ServerMain('127.0.0.1', 1234, log)

outputdata = {'hello': 'hello server', 'int': 1, 'float': 1.1233, 'list': [1, 2, 3, 4, 45]}

while True:
    server.ServerControl(outputdata)
    inputdata =  server.ServerReceiver()
    print(inputdata)
    sleep(1)

