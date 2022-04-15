from socket_tcp import socketTCP
import socket
import sys
server_socket = socketTCP("localhost", 5000)
server_socket.bind()
server_socket.settimeout(5)
try:
    server_socket.accept()
except socket.timeout as e: 
    print("Conection took too long")
    sys.exit(1)