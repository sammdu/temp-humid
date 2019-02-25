import re
import serial
from http.server import HTTPServer, BaseHTTPRequestHandler
from time import sleep
import threading

c = threading.Condition()

tempc = "DEFAULT TEMP C"
tempf = "DEFAULT TEMP F"
humid = "DEFAULT HUMID"


def parse(data):

    # regex matching only the numbers in the data
    match = re.search(r'T = ([0-9.]+), H = ([0-9.]+)', data)

    tempc = float(match.group(1))
    humid = float(match.group(2))

    tempf = (tempc * 1.8) + 32  # calculate fahrenheit

    return tempc, tempf, humid

class thread_serial(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):

        global tempc, tempf, humid

        #with serial.Serial(baudrate = 9600, port = '/dev/cu.usbmodem1411', timeout = 10) as ser:
        with serial.Serial(baudrate = 9600, port = '/dev/ttyACM1', timeout = 10) as ser:
            while True:
                s = ser.readline()
                data = str(s)[2:20]
                c.acquire()
                tempc, tempf, humid = parse(data)
                c.release()
                sleep(0.5)

class thread_server(threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):

        class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

            def do_GET(self):

                global tempc, tempf, humid

                self.send_response(200)
                # allow access from remote server / client (CORS)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                # respond to client request
                c.acquire()
                if "tempc" in self.path:
                    self.wfile.write(str(tempc).encode())
                elif "tempf" in self.path:
                    self.wfile.write(str(tempf).encode())
                elif "humid" in self.path:
                    self.wfile.write(str(humid).encode())
                else:
                    self.wfile.write("ERROR".encode())
                c.release()

        # start http server
        httpd = HTTPServer(('0.0.0.0', 80), SimpleHTTPRequestHandler)
        httpd.serve_forever()


tserial = thread_serial("Temperature and Humidity, Serial")
tserver = thread_server("Temperature and Humidity, HTTP Server")

tserial.start()
tserver.start()
