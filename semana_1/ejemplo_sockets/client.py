 # -*- coding: utf-8 -*-
import socket

print('Creando socket - Cliente')

# armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# lo conectamos al puerto acordado
client_socket.connect(('localhost', 8888))

# mandamos un mensajito
print("... Mandamos cositas")

# definimos un mensaje y una secuencia indicando el fin del mensaje
message = "Hola c:"
end_of_message = "0"

# socket debe recibir bytes, por lo que encodeamos el mensaje
send_message = (message + end_of_message).encode()

# enviamos el mensaje a través del socket
client_socket.send(send_message)
print("... Mensaje enviado")

# y esperamos una respuesta
message = client_socket.recv(1024)
print(' -> Respuesta del servidor: <<' + message.decode() + '>>')

# cerramos la conexión
client_socket.close()
