# -*- coding: utf-8 -*-
from audioop import add
import socket
from random import randrange
import sys
class socketTCP:
    def __init__(self, orig_address, port, dest_address = None):
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Socket no orientado a objetos
        self.address = (orig_address, port) # Par (dirección, puerto) de origen
        self.dest_adr = dest_address  # Dirección de destino
        self.seq = None # Secuencia asociada al socket
        self.data_to_recieve = 0 # Bytes por recibir de la comunicación actual
        self.starting_transaction = True # Booleano correspondiente a si el socket actualmente está partiendo una conexión o ya inició una
        self.established_conection = False # Booleano correspondiente a si el socket ya establecío una conexión

    def bind(self):
        """Función que hace bind en el socket sobre la dirección de origen."""
        self.socket_udp.bind((self.address))

    def connect(self, address):
        """Función que realiza el three-way handshake desde el emisor."""
        # Si el socket ya estableció una conexión arroja error
        if self.established_conection:
            raise NameError("You already established a connection!")
        # Se establece la dirección de destino
        self.dest_adr = address
        print(f"Original destiny address: {self.dest_adr}")
        # Se arma el mensaje tcp para iniciar el handshake
        dict_tcp = {}
        dict_tcp["SYN"] = 1
        dict_tcp["ACK"] = 0
        dict_tcp["FIN"] = 0
        dict_tcp["SEQ"] = randrange(101)
        self.seq = dict_tcp["SEQ"]
        print(f"Initial sequence: {self.seq}")
        message = self.dict_to_tcp(dict_tcp)
        message = message.encode()
        # Se envía el mensaje inicial y se queda esperando una respuesta
        self.socket_udp.sendto(message, address)
        while True:
            try:
                buffer, addres = self.socket_udp.recvfrom(64)
                break
            except socket.timeout as e:
                print("No se recibio el primer mensaje del handshake, intentamos denuevo...")
                self.socket_udp.sendto(message, address)
        dict_tcp = self.tcp_to_dict(buffer.decode())
        recieved_seq = dict_tcp["SEQ"]
        print(f"Recieved sequence: {recieved_seq}")
        # Se revisa si el mensaje recibido coincide con lo que se espera.
        if dict_tcp["SYN"] == 1 and dict_tcp["ACK"] == 1 and dict_tcp["SEQ"] == self.seq + 1:
            # Se arma el mensaje de respuesta y actualiza la secuencia del socket.
            dict_tcp["SYN"] = 0
            dict_tcp["ACK"] = 1
            dict_tcp["FIN"] = 0
            dict_tcp["SEQ"] += 1
            self.seq+=1
            message =  self.dict_to_tcp(dict_tcp)
            # Se responde con el mensaje correspondiente
            self.socket_udp.sendto(message.encode(), addres)
            # Se fija la secuencia del socket
            self.seq = dict_tcp["SEQ"]
            # Se marca como que el socket ya tiene una conexión establecida
            self.established_conection = True
            # Se guarda la dirección de destino
            self.dest_adr = addres
            print(f"New destiny address: {self.dest_adr}")
            print(f"Secuencia del socket: {self.seq}")
            print("Three-way handshake was succesfull")
        else:
            # Si la información del mensaje no corresponde, se levanta un error
            raise NameError("Three-way handshake wasn't succesfull")
    def accept(self):
        """Función que implementa el lado del receptor del three-way hanshake"""
        # De tenerse una conexón, se levanta un error
        if self.established_conection:
            raise NameError("You already established a connection!")
        # Se lleva la conexión a un nuevo puerto
        new_port = self.address[1]+1
        new_socketTCP = socketTCP(self.address[0], new_port)
        # Se hace bind en el nuevo puerto
        new_socketTCP.bind()
        # Se espera el mensaje del socket emisor
        while True:
            try:
                buffer, address = self.socket_udp.recvfrom(64)
                break
            except socket.timeout as e:
                print("No se recibió el primer mensaje del handshake, intentamos denuevo...")
        tcp_dict = self.tcp_to_dict(buffer.decode())
        # Si el mensaje no era de sincronización, se levanta un error
        if tcp_dict["SYN"] == 0:
            raise NameError("Message wasn't for sync")
        # Se arma el mansaje de respuesta y se espera la respuesta
        self.seq = tcp_dict["SEQ"]
        print(f"Recieved sequence: {self.seq}")
        tcp_dict["ACK"] = 1
        tcp_dict["SEQ"] +=  1
        self.seq += 1
        sent_sequence = tcp_dict["SEQ"]
        print(f"Sent sequence: {sent_sequence}")
        message = self.dict_to_tcp(tcp_dict)
        while True: 
            new_socketTCP.socket_udp.sendto(message.encode(), address)
            try:
                buffer, address = new_socketTCP.socket_udp.recvfrom(64)
                break
            except socket.timeout as e:
                print("No se recibió el segundo mensaje del handshake, intentamos denuevo...")
        tcp_dict = self.tcp_to_dict(buffer.decode())
        sequence2 = tcp_dict["SEQ"]
        print(f"Recieved sequence: {sequence2}")
        # Se revisa que la información coincida con lo que se espera
        if tcp_dict["ACK"] == 1 and tcp_dict["SEQ"] == self.seq +1:
            # Se actualiza la secuencia del socket, la dirección de destino y se marca como que el socket ya estableció una conexión
            self.seq += 1
            new_socketTCP.dest_adr = address
            new_socketTCP.seq = self.seq
            new_socketTCP.established_conection = True
            print(f"Secuencia del socket: {new_socketTCP.seq}")
            print("Three-way handshake was succesfull")
            return new_socketTCP, new_socketTCP.address
        else:
            # Si la información no calza, se levanta un error
            raise NameError("Three-way handshake wasn't succesfull")

    def tcp_to_dict(self, message):
        """ Función que pasa un mensaje tcp a un diccionario"""
        # [SYN]|||[ACK]|||[FIN]|||[SEQ]|||[DATOS]
        message_list = message.split("|||")
        tcp_dict = {}
        tcp_dict["SYN"] = int(message_list[0])
        tcp_dict["ACK"] = int(message_list[1])
        tcp_dict["FIN"] = int(message_list[2])
        tcp_dict["SEQ"] = int(message_list[3])
        # Si vienen datos, se guardan.
        try:
            tcp_dict["DATOS"] = message_list[4]
        except:
            pass
        return tcp_dict

    def dict_to_tcp(self, tcp_dict):
        """Función que pasa un diccionario, con la estructura del generado por tcp_to_dict(...), a un mensaje tcp"""
        tcp_message = str(tcp_dict["SYN"]) + "|||" + str(tcp_dict["ACK"]) + "|||" + str(tcp_dict["FIN"]) + "|||" + str(tcp_dict["SEQ"])
        try:
            tcp_message += "|||" + str(tcp_dict["DATOS"])
        except:
            pass
        return tcp_message

    def settimeout(self, timeout_in_seconds):
        """Función que establece un timeout para las funciones bloqueantes del socket"""
        self.socket_udp.settimeout(timeout_in_seconds)

    def send(self, message):
        """Función que envía un mensaje, habiendose establecido una conexión antes"""
        # Se revisa si el socket ya estableció una conexión, de no ser así se levanta un error
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
        # Calculamos la cantidad de "pedazos" en los que hay que dividir el mensaje
        mes_len = len(message)
        chunks, chunk_size = mes_len//64 +1, 64

        # Armamos un arreglo con los pedazos del mensaje
        chunked_array = []
        for i in range(chunks):
            if (i+1)*chunk_size<mes_len:
                chunked_array.append(message[i*chunk_size:(i+1)*chunk_size])
            else:
                chunked_array.append(message[i*chunk_size:mes_len])
        # Largo en bytes del mensaje:
        message_length = len(message.encode())
        print(f"Largo del mensaje a enviar: {message_length}")
        # Pasamos a tcp el mensaje
        tcp_dict = {}
        tcp_dict["SYN"] = 0
        tcp_dict["ACK"] = 0
        tcp_dict["FIN"] = 0
        tcp_dict["SEQ"] = self.seq
        tcp_dict["DATOS"] = message_length
        message_tcp = self.dict_to_tcp(tcp_dict)
        # Enviamos primero el largo del mensaje
        while True:
            self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)
            while True:
                try:
                    buffer, address = self.socket_udp.recvfrom(64)
                    break
                except socket.timeout as e:
                    print("No se obtuvo respuesta al enviar el largo del mensaje, intentamos denuevo...")
                    self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)    
            tcp_dict_ = self.tcp_to_dict(buffer.decode())
            # Si es que recibimos un acknowledge y la secuencia calza con el largo del mensaje que nosotros enviamos, dejamos de esperar/pedir el mensaje
            if tcp_dict_["ACK"] == 1 and tcp_dict_["SEQ"] == self.seq + len(str(message_length).encode()):
                self.seq += len(str(message_length).encode())
                print(f"Message-Lenght -> Secuencia: {self.seq}")
                break
            else:
                print("El mensaje recibido no coincide, tratamos denuevo...")
        # Actualizamos el tcp_dict
        tcp_dict = tcp_dict_
        # Enviamos uno por uno los pedazitos del mensaje original
        for m in chunked_array:
            # Armamos el mensaje tcp
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 0
            tcp_dict["FIN"] = 0
            tcp_dict["SEQ"] = self.seq
            tcp_dict["DATOS"] = m
            message_tcp = self.dict_to_tcp(tcp_dict)
            while True:
                # Enviamos el pedazito
                self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)
                # while True:
                    # Esperamos la respuesta
                try:
                    buffer, address = self.socket_udp.recvfrom(64)
                except socket.timeout as e:
                    print("No se obtuvo respuesta, intentamos denuevo...")
                    # self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)  
                    continue  
                # Pasamos la respuesta a un tcp_dict
                tcp_dict_ = self.tcp_to_dict(buffer.decode()) 
                # Si recibimos un acknowledge y la secuencia es igual a la secuencia anterior mas el largo en bytes del mensaje enviado pasamos al pedazo siguiente
                if tcp_dict_["ACK"] == 1 and tcp_dict_["SEQ"] == self.seq + len(m.encode()):
                    self.seq += len(m.encode())
                    print(f"Mensajes -> Secuencia: {self.seq}")
                    break
                else:
                    print("El mensaje recibido no coincide, tratamos denuevo...")
                    continue

    def recv(self, buff_size):
        """Función que recibe un mensaje con un buffer tamaño buff_size"""
        # Si tiene una conexion establecida, se levanta un error
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
        # En caso de que este empezando la transmision, esperamos el largo del mensaje:
        if self.starting_transaction:
            while True:
                try:
                    # Recibimos el mensaje
                    buffer, address = self.socket_udp.recvfrom(128)  # Recibimos el largo del mensaje
                    break
                except socket.timeout as e:
                    # Si no logramos recibirlo, nos quedamos esperando hasta recibirlo.
                    print("No se obtuvo respuesta acerca del largo del mensaje, intentamos denuevo...")
                    continue
            message = buffer.decode()
            tcp_dict = self.tcp_to_dict(message)
            # Si el mensaje contiene la secuencia de final, se maneja el close
            if tcp_dict["FIN"] == 1:
                # Se establece un máximo de timeouts de 4
                nmr_timeouts = 0
                print("Recieved terminating sequence!")
                # Se incrementa la secuencia en 1
                self.seq += 1
                # Se arma el mensaje de respuesta
                closing_dict = {}
                closing_dict["SYN"] = 0
                closing_dict["ACK"] = 1
                closing_dict["FIN"] = 1
                closing_dict["SEQ"] = self.seq
                while True:
                    print("Sent terminating sequence!")
                    self.socket_udp.sendto(self.dict_to_tcp(closing_dict).encode(), self.dest_adr)
                    # Nos quedamos esperando una respuesta
                    try:
                        buffer, address = self.socket_udp.recvfrom(128)
                    except socket.timeout as e:
                        # Si no la logramos recibir, volvemos a enviar el mensaje (hasta 4 veces)
                        print("No se obtuvo respuesta, intentamos denuevo...")
                        if nmr_timeouts >= 4:
                            self.starting_transaction = True
                            self.established_conection = False
                            self.socket_udp.close()
                            break
                        else:
                            nmr_timeouts+=1
                            continue
                            
                    ans_dict = self.tcp_to_dict(buffer.decode())
                    # Se revisa que el mensaje recibido cumple el patron de close, sino volvemos a comenzar.
                    if ans_dict["ACK"] == 1 and ans_dict["SEQ"] == self.seq + 1 or nmr_timeouts >= 4:
                        print("Recieved terminating sequence 2!")
                        self.starting_transaction = True
                        self.established_conection = False
                        self.socket_udp.close()
                        break
                return
            # Guardamos el largo del mensaje total en message_length
            message_length = int(tcp_dict["DATOS"])
            # Establecemos que quedan message_length bytes por recibir
            self.data_to_recieve = message_length
            # Actualizamos la secuencia
            self.seq = tcp_dict["SEQ"] + len(str(message_length).encode())
            # Armamos el mensaje tcp
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 1
            tcp_dict["FIN"] = 0
            tcp_dict["SEQ"] = self.seq
            # Avisamos que recibimos el mensaje y actualizamos la secuencia
            self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
            # Marcamos que el socket ya partió la transmision
            self.starting_transaction = False
            print(f"Message-Length -> Secuencia: {self.seq}")
        # Si ya se está recibiendo un mensaje y quedan datos por recibir
        if self.data_to_recieve > 0:
            message_recieved = ""
            # Mientras haya espacio en el buffer
            while buff_size > 0:
                while True:
                    # Nos quedamos esperando el mensaje
                    try:
                        buffer, address = self.socket_udp.recvfrom(128)
                        break
                    except socket.timeout as e:
                        # Si no lo recibimos, nos quedamos esperandolo
                        print("No se obtuvo respuesta, intentamos denuevo...")
                tcp_dict_ = self.tcp_to_dict(buffer.decode()) 
                # Si la secuencia del mensaje recibido es menor a la secuencia actual, respondemos con el mensaje original
                if tcp_dict_["SEQ"] < self.seq:
                    print("Mensaje repetido!")
                    # Armamos el mensaje de respuesta
                    tcp_dict= {}
                    tcp_dict["SYN"] = 0
                    tcp_dict["ACK"] = 1
                    tcp_dict["FIN"] = 0
                    tcp_dict["SEQ"] = self.seq
                    # Enviamos el mensaje de respuesta
                    self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                # Si la secuencia calza, seguimos
                else:
                    # Incrementamos la secuencia del socket
                    self.seq += len(tcp_dict_["DATOS"].encode())
                    print(f"Mensajes -> Secuencia: {self.seq}")
                    # Armamos el mensaje de respuesta
                    tcp_dict = {}
                    tcp_dict["SYN"] = 0
                    tcp_dict["ACK"] = 1
                    tcp_dict["FIN"] = 0
                    tcp_dict["SEQ"] = self.seq
                    # Enviamos la respuesta
                    self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                    # Agregamos el mensaje leido a lo que ya llevamos leido
                    message_recieved += tcp_dict_["DATOS"]
                    # Restamos lo leido a lo que nos queda por leer
                    self.data_to_recieve -= len(tcp_dict_["DATOS"].encode())
                    # Disminuimos el tamaño del buffer
                    buff_size -= len(tcp_dict_["DATOS"].encode())
                    # Si no nos queda data por recibir, marcamos como esperando conexion 
                    if self.data_to_recieve == 0:
                        print("Finished recieving message")
                        self.starting_transaction = True
                        break
        return message_recieved

    def close(self):
        # Creamos el mensaje de finalización
        tcp_dict = {}
        tcp_dict["SYN"] = 0
        tcp_dict["ACK"] = 0
        tcp_dict["FIN"] = 1
        tcp_dict["SEQ"] = self.seq
        while True:
            while True:
                # Se envia el mensaje
                self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                print("Sent terminating sequence!")
                # Se espera la respuesta
                try:
                    buffer, address = self.socket_udp.recvfrom(128)
                    break
                except socket.timeout as e:
                    # Si no se recibe la respuesta, vuelve a enviar el mensaje y se queda esperando
                    print("No se obtuvo respuesta, intentamos denuevo...")
            # Se pasa la respuesta a un diccionario
            ans_dict = self.tcp_to_dict(buffer.decode()) 
            # Se revisa si la respuesta cumple el patrón de término
            if ans_dict["FIN"] == 1 and ans_dict["ACK"]==1 and ans_dict["SEQ"] == self.seq + 1:
                print("Recieved terminating answer!")
                self.seq += 2
                tcp_dict["SEQ"] = self.seq
                tcp_dict["ACK"] = 1
                tcp_dict["FIN"] = 0
                # Se responde con el segundo mensaje de finalización
                self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                break
        # Se marca como en espera de una conexion, que no tiene una conexión establecida y se cierra el socket
        self.starting_transaction = True
        self.established_conection = False
        self.socket_udp.close()








