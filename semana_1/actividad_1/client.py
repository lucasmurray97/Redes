 # -*- coding: utf-8 -*-
import socket

print('Creando socket - Cliente')

# armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# mandamos un mensajito
print("... Mandamos cositas")

# definimos un mensaje y una secuencia indicando el fin del mensaje
message = "Hola c:"
end_of_message = "10"
port = 5000
adrs = ('localhost', port)
bufsize = 1024
# socket debe recibir bytes, por lo que encodeamos el mensaje
send_message = (message+end_of_message).encode()

# enviamos el mensaje a través del socket
client_socket.sendto(send_message, adrs)
print("... Mensaje enviado")

# recibimos el mensaje
print("...Esperando mensaje")
message, address = client_socket.recvfrom(bufsize)
print(' -> Se ha recibido el siguiente mensaje: ' + message.decode())
# cerramos la conexión
client_socket.close()
