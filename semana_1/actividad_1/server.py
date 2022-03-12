# -*- coding: utf-8 -*-
import socket

def receive_full_mesage(dgram_socket, buff_size, end_of_message):
    # esta función se encarga de recibir el mensaje completo desde el cliente
    # en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
    # llegue el resto

    # recibimos la primera parte del mensaje
    buffer, address = dgram_socket.recvfrom(buff_size)
    full_message = buffer.decode().rstrip()
    # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
    is_end_of_message = contains_end_of_message(full_message, end_of_message)
    # si el mensaje llegó completo (o sea que contiene la secuencia de fin de mensaje) removemos la secuencia de fin de mensaje
    if is_end_of_message:
        full_message = full_message[0:(len(full_message) - len(end_of_message))]

    # si el mensaje no está completo (no contiene la secuencia de fin de mensaje)
    else:
        # entramos a un while para recibir el resto y seguimos esperando información
        # mientras el buffer no contenga secuencia de fin de mensaje
        while not is_end_of_message:
            # recibimos un nuevo trozo del mensaje
            buffer, address = dgram_socket.recvfrom(buff_size)
            # y lo añadimos al mensaje "completo"
            full_message += buffer.decode()

            # verificamos si es la última parte del mensaje
            is_end_of_message = contains_end_of_message(full_message, end_of_message)
            if is_end_of_message:
                # removemos la secuencia de fin de mensaje
                full_message = full_message[0:(len(full_message) - len(end_of_message))]

    # finalmente retornamos el mensaje
    return full_message, address


def contains_end_of_message(message, end_sequence):
    if end_sequence == message[(len(message) - (len(end_sequence))):len(message)]:
        return True
    else:
        return False

# Socket no orientado a conexión
print('Creando socket - Servidor')
dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#definimos buffsize, message y port
bufsize = 1024
end_of_message = "10"
port = 5000
adrs = ('localhost', port)
dgram_socket.bind(adrs)
print('... Esperando clientes')

while True:
    # Recibir mensajes. Este método nos entrega el mensaje junto a la dirección de origen del mensaje
    message, address = receive_full_mesage(dgram_socket, bufsize, end_of_message)
    print(' -> Se ha recibido el siguiente mensaje: ' + message)
    print("Echo")
    dgram_socket.sendto(message.encode(), address)
