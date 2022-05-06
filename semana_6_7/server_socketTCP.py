from socket_tcp import socketTCP
import socket
import sys
server_socket = socketTCP("localhost", 5000)
server_socket.bind()
server_socket.settimeout(10)
try:
    server_socket2, address = server_socket.accept()
except socket.timeout as e: 
    print("Conection took too long")
    sys.exit(1)

try:
    print("Primer recv")
    message = server_socket2.recv(128)
    print("Segundo recv")
    message += server_socket2.recv(128)
    print("Tercer recv")
    message += server_socket2.recv(128)
    print(message)
    server_socket2.recv(128)
except socket.timeout as e: 
    print("Conection took too long")
    sys.exit(1)
