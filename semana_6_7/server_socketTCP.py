from socket_tcp import socketTCP
import socket
import sys
server_socket = socketTCP("localhost", 5000)
server_socket.bind()
server_socket.settimeout(10)
try:
    server_socket.accept()
except socket.timeout as e: 
    print("Conection took too long")
    sys.exit(1)

try:
    message = server_socket.recv(32)
    print(message)
except socket.timeout as e: 
    print("Conection took too long")
    sys.exit(1)
