# -*- coding: utf-8 -*-
import socket
from random import randrange
class socketTCP:
    def __init__(self, orig_address, port, dest_address = None):
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (orig_address, port)
        self.dest_adr = dest_address
        self.nmr_seq = None
        self.seq = FileNotFoundError
        self.data_to_recieve = 0
        self.starting_transaction = True
    def set_seq(self, nmr):
        self.nmr_seq = nmr
    def increase_seq(self, inc):
        self.nmr_seq += inc
    def bind(self):
        self.socket_udp.bind((self.address))
    def connect(self, address):
        self.dest_adr = address
        dict_tcp = {}
        dict_tcp["SYN"] = 1
        dict_tcp["ACK"] = 0
        dict_tcp["FIN"] = 0
        dict_tcp["SEQ"] = randrange(101)
        sequence = dict_tcp["SEQ"]
        print(f"Initial sequence: {sequence}")
        message = self.dict_to_tcp(dict_tcp)
        message = message.encode()
        self.socket_udp.sendto(message, address)
        while True:
            buffer, address = self.socket_udp.recvfrom(64)
            break
        dict_tcp = self.tcp_to_dict(buffer.decode())
        recieved_seq = dict_tcp["SEQ"]
        print(f"Recieved sequence: {recieved_seq}")
        if dict_tcp["SYN"] == 1 and dict_tcp["ACK"] == 1 and dict_tcp["SEQ"] == sequence + 1:
            dict_tcp["SYN"] = 0
            dict_tcp["ACK"] = 1
            dict_tcp["FIN"] = 0
            dict_tcp["SEQ"] += 1
            message =  self.dict_to_tcp(dict_tcp)
            self.socket_udp.sendto(message.encode(), address)
            self.seq = dict_tcp["SEQ"]
            print(f"Secuencia del socket: {self.seq}")
            print("Three-way handshake was succesfull")
        else:
            raise NameError("Three-way handshake wasn't succesfull")
    def accept(self):
        while True:
            buffer, address = self.socket_udp.recvfrom(64)
            break
        tcp_dict = self.tcp_to_dict(buffer.decode())
        if tcp_dict["SYN"] == 0:
            raise NameError("Message wasn't for sync")
        sequence = tcp_dict["SEQ"]
        print(f"Recieved sequence: {sequence}")
        tcp_dict["ACK"] = 1
        tcp_dict["SEQ"] +=  1
        sent_sequence = tcp_dict["SEQ"]
        print(f"Sent sequence: {sent_sequence}")
        message = self.dict_to_tcp(tcp_dict)
        self.socket_udp.sendto(message.encode(), address)
        while True: 
             buffer, address = self.socket_udp.recvfrom(64)
             break
        tcp_dict = self.tcp_to_dict(buffer.decode())
        sequence2 = tcp_dict["SEQ"]
        print(f"Recieved sequence: {sequence2}")
        if tcp_dict["ACK"] == 1 and tcp_dict["SEQ"] == sequence +2:
            self.dest_adr = address
            self.seq = tcp_dict["SEQ"]
            print(f"Secuencia del socket: {self.seq}")
            print("Three-way handshake was succesfull")
            return self, self.address
        else:
            raise NameError("Three-way handshake wasn't succesfull")
    def recieve_message(self, buff_size):
        buffer, address = self.socket_udp.recvfrom(buff_size)
        return buffer.decode(), address
    def tcp_to_dict(self, message):
        # [SYN]|||[ACK]|||[FIN]|||[SEQ]|||[DATOS]
        message_list = message.split("|||")
        tcp_dict = {}
        tcp_dict["SYN"] = int(message_list[0])
        tcp_dict["ACK"] = int(message_list[1])
        tcp_dict["FIN"] = int(message_list[2])
        tcp_dict["SEQ"] = int(message_list[3])
        try:
            tcp_dict["DATOS"] = message_list[4]
        except:
            pass
        return tcp_dict
    def dict_to_tcp(self, tcp_dict):
        tcp_message = str(tcp_dict["SYN"]) + "|||" + str(tcp_dict["ACK"]) + "|||" + str(tcp_dict["FIN"]) + "|||" + str(tcp_dict["SEQ"])
        try:
            tcp_message += "|||" + str(tcp_dict["DATOS"])
        except:
            pass
        return tcp_message
    def settimeout(self, timeout_in_seconds):
        self.socket_udp.settimeout(timeout_in_seconds)
    def send(self, message):
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
                buffer, address = self.socket_udp.recvfrom(64)
                break
            tcp_dict_ = self.tcp_to_dict(buffer.decode())
            # Si es que recibimos un acknowledge y la secuencia calza con el largo del mensaje que nosotros enviamos, dejamos de esperar/pedir el mensaje
            if tcp_dict_["ACK"] == 1 and tcp_dict_["SEQ"] == self.seq + len(str(message_length).encode()):
                self.seq += len(str(message_length).encode())
                break
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
                while True:
                    # Esperamos la respuesta
                    try:
                        buffer, address = self.socket_udp.recvfrom(64)
                        break
                    except socket.timeout as e:
                        self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)    
                # Pasamos la respuesta a un tcp_dict
                tcp_dict_ = self.tcp_to_dict(buffer.decode()) 
                # Si recibimos un acknowledge y la secuencia es igual a la secuencia anterior mas el largo en bytes del mensaje enviado pasamos al pedazo siguiente
                if tcp_dict_["ACK"] == 1 and tcp_dict_["SEQ"] == self.seq + len(m.encode()):
                    self.seq += len(m.encode())
                    break

            # Actualizamos el tcp_dict
            tcp_dict = tcp_dict_
    def recv(self, buff_size):
        # En caso de que este empezando la transmision, esperamos el largo del mensaje:
        if self.starting_transaction:
            while True:
                buffer, address = self.socket_udp.recvfrom(buff_size)
                break
            message = buffer.decode()
            tcp_dict = self.tcp_to_dict(message)
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
            self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
            # Marcamos que el socket ya partió la transmision
            self.starting_transaction = False
        if self.data_to_recieve > 0:
            while True:
                buffer, address = self.socket_udp.recvfrom(buff_size)
                break
            tcp_dict_ = self.tcp_to_dict(buffer.decode()) 
            # Si la secuencia del mensaje recibido es menor a la secuencia actual, respondemos con el mensaje original
            if tcp_dict_["SEQ"] < self.seq:
                print("Mensaje repetido!")
                self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
            else:
                self.seq += len(tcp_dict_["DATOS"].encode())
                tcp_dict["SYN"] = 0
                tcp_dict["ACK"] = 1
                tcp_dict["FIN"] = 0
                tcp_dict["SEQ"] = self.seq
                self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                message_recieved = tcp_dict_["DATOS"]
                self.data_to_recieve -= len(tcp_dict_["DATOS"].encode())
                if self.data_to_recieve == 0:
                    self.starting_transaction = True
        return message_recieved








