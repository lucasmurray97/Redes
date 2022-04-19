from socket_tcp import socketTCP
import socket
import sys
client_socket = socketTCP("localhost", 5000)
tcp_dict = {}
tcp_dict["SYN"] = 1
tcp_dict["ACK"] = 0
tcp_dict["FIN"] = 0
tcp_dict["SEQ"] = 0
client_socket.settimeout(5)
try:
    client_socket.connect(("localhost", 5000))
except socket.timeout as e: 
    print("Conection took too long")
    sys.exit(1)

with open('mensaje.txt', 'r') as file:
    message = file.read()
try:
    client_socket.send(message)
except socket.timeout as e: 
    print("Conection took too long")
    sys.exit(1)
