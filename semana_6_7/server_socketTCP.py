from socket_tcp import socketTCP
server_socket = socketTCP("localhost", 5000)
server_socket.bind()
server_socket.accept()