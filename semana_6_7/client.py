# -*- coding: utf-8 -*-
import socket

def contains_end_of_message(message, end_sequence):
    # Esta funcion revisa que message contenga la secuencia end_sequence al final
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
end_of_message = "FINAL"
port = 5000
adrs = ('localhost', port)
bufsize = 1024
# socket debe recibir bytes, por lo que encodeamos el mensaje

send_message = (message+end_of_message).encode()

# Calculamos la cantidad de "pedazos" en los que hay que dividir el mensaje
chunks, chunk_size = len(send_message)//64 +1, 64

# Armamos un arreglo con los pedazos del mensaje
chunked_array = []
for i in range(chunks):
    if (i+1)*chunk_size<len(send_message):
        chunked_array.append(send_message[i*chunk_size:(i+1)*chunk_size])
    else:
        chunked_array.append(send_message[i*chunk_size:len(send_message)])

# enviamos uno por uno los pedazos del mensaje
for m in chunked_array:
    client_socket.sendto(m, adrs)
print("... Mensaje enviado")

client_socket.close()
