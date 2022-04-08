 # -*- coding: utf-8 -*-
from email import header
from http import server
import re
import socket
import sys
import json
def receive_full_mesage(connection_socket, buff_size, end_of_message):
    # esta función se encarga de recibir el header de la request completo.
    # en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
    # llegue el resto

    # recibimos la primera parte del mensaje
    buffer = connection_socket.recv(buff_size)
    full_message = buffer.decode()

    # verificamos si llegó el mensaje completo o si aún faltan partes del mensaje
    is_end_of_message = contains_end_of_message(full_message, end_of_message)

    # si el mensaje no está completo (no contiene la secuencia de fin de mensaje)
    if not end_of_message:
        # entramos a un while para recibir el resto y seguimos esperando información
        # mientras el buffer no contenga secuencia de fin de mensaje
        while not is_end_of_message:
            # recibimos un nuevo trozo del mensaje
            buffer = connection_socket.recv(buff_size)
            # y lo añadimos al mensaje "completo"
            full_message += buffer.decode()

            # verificamos si es la última parte del mensaje
            is_end_of_message = contains_end_of_message(full_message, end_of_message)
    # Dividimos el header y la porción de body que podríamos haber recibido
    header_body = full_message.split(end_of_message)
    # Se guarda el header
    header = header_body[0]
    # Se divide el header por cada linea que viene en el encabezado
    header_list = header.split("\r\n")
    # Se guarda cada linea del encabezado en un diccionario
    header_dict = {}
    for i in header_list:
        header_dict[i.split(": ")[0]] = i.split(" ")[1]
    # Se agrega el correo a el header, mediante la funcion add_correo()
    (full_message, header_dict) = add_correo(header_dict, correo)
    # finalmente retornamos el header, el diccionario y el dominio por que el se hace el request
    return full_message, header_dict, list(header_dict.keys())[0].split(" ")[1]

# Esta función revisa que el el string mensaje contenga al final la seguencia end_of_message, retornando un booleano
def contains_end_of_message(message, end_of_message):
    if message.find(end_of_message) != -1:
        return True
    else:
        return False

# Recibir http response completa:
def recieve_response(connection_socket, buff_size, end_of_message, forbidden):
    # Recibe la response que responde el servidor y la almacena en buffer
    buffer = connection_socket.recv(buff_size)
    full_message = buffer.decode()
    # Divide la responde en header y body: [header, body]
    header_body = full_message.split(end_of_message)
    # Se almacena el header en header
    header = header_body[0]
    # Se almacena el body en body
    body = header_body[1]
    header_list = header.split("\r\n") # Se divide el header en la lineas que lo componen
    header_dict = {}
    # Se itera sobre las lineas del header y se guardan en header_dict
    for i in header_list:
        header_dict[i.split(": ")[0]] = i.split(" ")[1]
    # Se aplica la función replace_forbidden sobre el body
    body = replace_forbidden(body, forbidden)
    # Se vuelve a armar la response actualizada
    response = header + end_of_message + body
    # Se retorna la response, el header_dict y el body
    return response, header_dict, body

def check_forbidden_dom(first_line, blocked):
    # Revisa si el dominio está dentro de las direcciones bloqueadas, retornando un booleano
    if first_line in blocked:
        return True
    else:
        False
def replace_forbidden(body, forbidden):
    # Se itera sobre las palabras prohibidas y se reemplazan
    for f in forbidden:
        word = list(f.keys())[0]
        replacement = f[word]
        body = body.replace(word, replacement)
    # Se retorna el body actualizado
    return body
# Función que recibe el header_dict y agrega el encabezado "X-ElQuePrefgunta" con valor igual al correo
def add_correo(header_dict, correo):
    header_dict["X-ElQuePregunta"] = correo
    # Se vuelve a armar la request, con el ecabezado extra.
    fixed_request = list(header_dict.keys())[0] + "\r\n"
    for key in list(header_dict.keys())[1:]:
        fixed_request += key + ": " + header_dict[key] + "\r\n"
    # Se agrega el doble salto de linea
    fixed_request += "\r\n"
    return fixed_request, header_dict
# Recibimos parametros de la entrada estandar:
correo = ""
todos_los_argumentos = sys.argv
numero_de_argumentos = len(sys.argv)
if numero_de_argumentos >=0:
    configuration_file = sys.argv[1]
    with open(configuration_file) as file:
        # usamos json para manejar los datos
        data = json.load(file)
        # recolectamos el parametro correo del archivo
        correo = data["user"] # Se guarda el correo en correo
        blocked = data["blocked"] # Se guardan las direcciones prohibidas en blocked
        forbidden = data["forbidden_words"] # Se guardan las plabras prohibidas en forbidden_words


# definimos el tamaño del buffer de recepción 
buff_size = 1024
end_of_message = "\r\n\r\n"
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
    # Recibimos el header, request_h_dict y la direccion por la que se consulta
    (received_message, request_h_dict, start_line) = receive_full_mesage(connection, buff_size, end_of_message)
    print(' -> Se ha recibido el siguiente mensaje del cliente: \n' + received_message)
    # Si la direccion está dentro de las prohibidas, respondemos con un mensaje de erros y se envía al cliente
    if check_forbidden_dom(start_line, blocked):
        html = "<html><head><title>Bienvenida!</title></head><body><H1>No puedes acceder a este dominio!</H1></body></html>"
        error_message = (f"HTTP/1.1 403 forbiden\r\nContent-Type: text/html; charset=UTF-8\r\nX-ElQuePregunta: {correo}\r\nContent-Length: {len(html)}\r\n\r\n{html}").encode()
        connection.send(error_message)
    else:
        # Armamos un nuevo socket, para la comunicacion proxy<->server
        server_socket2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Se guarda el host en site
        site = request_h_dict["Host"]
        address_server = (site, 80)
        try: 
            server_socket2.connect(address_server) 
        except socket.gaierror as e: 
            print("Address-related error connecting to server: %s" % e) 
            sys.exit(1) 
        except socket.error as e: 
            print("Connection error: %s" % e) 
            sys.exit(1) 
        # Se envía la request que pasó por el proxy al servidor
        server_socket2.send(received_message.encode())
        print(' -> Se ha enviado el siguiente mensaje al servidor: \n' + received_message)
        # Se recibe la response que entrega el server, modificandose mediante la funcion recieve_response
        (response, response_h_dict, body) = recieve_response(server_socket2, buff_size, end_of_message, forbidden)
        print(' -> Se ha enviado el siguiente mensaje al cliente: \n' + response)
        # Se envía la response al cliente
        connection.send(response.encode())
        