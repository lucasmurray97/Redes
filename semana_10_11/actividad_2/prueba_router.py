import sys
import socket
# Abrimos el archivo a enviar
with open("test.txt", 'r') as file:
    full_message = file.read()
splited_message = full_message.split("\n")
print(splited_message)
# Recibimos el header, y la direccion del router al que va dirigido
headers = sys.argv[1]
router_ip = sys.argv[2]
router_port = int(sys.argv[3])
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print(headers, router_ip, router_port)
# Enviamos cada linea del archivo por separado al router ingresado
for message in splited_message:
    message = headers + "," + message
    sock.sendto(message.encode(), (router_ip, router_port))
