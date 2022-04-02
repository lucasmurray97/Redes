import socket

request_http = "GET http://cc4303.bachmann.cl/ HTTP/1.1\r\nHost: cc4303.bachmann.cl\r\nUser-Agent: curl/7.64.1\r\nAccept: */*\r\nProxy-Connection: Keep-Alive\r\n\r\n"
test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
test_socket.connect(("cc4303.bachmann.cl", 80))
test_socket.send(request_http.encode())
response_http = test_socket.recv(1024)
print(response_http.decode())
