from socket_tcp import socketTCP

client_socket = socketTCP("localhost", 5000)
tcp_dict = {}
tcp_dict["SYN"] = 1
tcp_dict["ACK"] = 0
tcp_dict["FIN"] = 0
tcp_dict["SEQ"] = 0
client_socket.connect(("localhost", 5000))