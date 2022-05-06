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
    server_socket2.set_window_size(3)
    message = server_socket2.recv(256, "go_back_n")
    message+=server_socket2.recv(256, "go_back_n")
    print(message)
except socket.timeout as e: 
    print("Conection took too long")
    sys.exit(1)