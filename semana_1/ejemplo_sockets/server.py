 # -*- coding: utf-8 -*-
import socket
 
 
def receive_full_mesage(connection_socket, buff_size, end_of_message):
    # esta función se encarga de recibir el mensaje completo desde el cliente
    # en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
    # llegue el resto

    # recibimos la primera parte del mensaje
    buffer = connection_socket.recv(buff_size)
    full_message = buffer.decode()

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
            buffer = connection_socket.recv(buff_size)
            # y lo añadimos al mensaje "completo"
            full_message += buffer.decode()

            # verificamos si es la última parte del mensaje
            is_end_of_message = contains_end_of_message(full_message, end_of_message)
            if is_end_of_message:
                # removemos la secuencia de fin de mensaje
                full_message = full_message[0:(len(full_message) - len(end_of_message))]

    # finalmente retornamos el mensaje
    return full_message


def contains_end_of_message(message, end_sequence):
    print("hola")
    if end_sequence == message[(len(message) - len(end_sequence)):len(message)]:
        print(message[(len(message) - len(end_sequence)):len(message)])
        return True
    else:
        return False

# definimos el tamaño del buffer de recepción ¿Cómo se ven los trozos de mensaje recibidos si usamos 'buff_size = 2' ?
buff_size = 64
end_of_message = "0"
address = ('localhost', 8888)

print('Creando socket - Servidor')
# armamos el socket
# los parámetros que recibe el socket indican el tipo de conexión
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# lo conectamos al server, en este caso espera mensajes localmente en el puerto 8888
server_socket.bind(address)

# hacemos que sea un server socket y le decimos que tenga a lo mas 3 peticiones de conexión encoladas
# si recibiera una 4ta petición de conexión la va a rechazar
server_socket.listen(3)

# nos quedamos esperando, como buen server, a que llegue una petición de conexión
print('... Esperando clientes')
while True:
    # cuando llega una petición de conexión la aceptamos
    # y sacamos los datos de la conexión entrante (objeto, dirección)
    connection, address = server_socket.accept()

    # luego recibimos el mensaje usando la función que programamos
    received_message = receive_full_mesage(connection, buff_size, end_of_message)

    print(' -> Se ha recibido el siguiente mensaje: ' + received_message)

    # respondemos
    response_message = ("Mensaje \"{}\" ha sido recibido con éxito".format(received_message)).encode()
    connection.send(response_message)

    # cerramos la conexión
    # notar que la dirección que se imprime indica un número de puerto distinto al 8888
    connection.close()
    print("conexión con " + str(address) + " ha sido cerrada")

    # seguimos esperando por si llegan otras conexiones