 # -*- coding: utf-8 -*-
import socket

def contains_end_of_message(message, end_sequence):
    message = message.rstrip()
    print(message)
    if end_sequence == message[(len(message) - (len(end_sequence))):len(message)]:
        return True
    else:
        return False

print('Creando socket - Cliente')

# armamos el socket, los parámetros que recibe el socket indican el tipo de conexión
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# mandamos un mensajito
print("... Mandamos cositas")

# definimos un mensaje y una secuencia indicando el fin del mensaje
with open('mensaje.txt', 'r') as file:
    message = file.read()
end_of_message = "10"
port = 5000
adrs = ('localhost', port)
bufsize = 1024
# socket debe recibir bytes, por lo que encodeamos el mensaje

send_message = (message+end_of_message).encode()

chunks, chunk_size = len(send_message)//1024 +1, 1024

chunked_array = []

for i in range(chunks):
    if (i+1)*chunk_size<len(send_message):
        chunked_array.append(send_message[i*chunk_size:(i+1)*chunk_size])
    else:
        chunked_array.append(send_message[i*chunk_size:len(send_message)])

# enviamos el mensaje a través del socket
for m in chunked_array:
    client_socket.sendto(m, adrs)
print("... Mensaje enviado")

# recibimos el mensaje
print("...Esperando mensaje")
message = ""
while True:
    message, address = client_socket.recvfrom(bufsize)
    print(' -> Se ha recibido el siguiente mensaje: ' + message.decode())
    if contains_end_of_message(message.decode(), end_of_message):
        break
# cerramos la conexión
client_socket.close()
