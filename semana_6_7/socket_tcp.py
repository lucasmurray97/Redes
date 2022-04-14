# -*- coding: utf-8 -*-
import socket
from random import randrange
class socketTCP:
    def __init__(self, orig_address, port, dest_address = None):
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (orig_address, port)
        self.dest_adr = dest_address
        self.nmr_seq = None
    def set_seq(self, nmr):
        self.nmr_seq = nmr
    def increase_seq(self, inc):
        self.nmr_seq += inc
    def bind(self):
        self.socket_udp.bind((self.address))
    def connect(self, address):
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
            buffer, address = self.recieve_message(64)
            break
        dict_tcp = self.tcp_to_dict(buffer)
        recieved_seq = dict_tcp["SEQ"]
        print(f"Recieved sequence: {recieved_seq}")
        if dict_tcp["SYN"] == 1 and dict_tcp["ACK"] == 1 and dict_tcp["SEQ"] == sequence + 1:
            dict_tcp["SYN"] = 0
            dict_tcp["ACK"] = 1
            dict_tcp["FIN"] = 0
            dict_tcp["SEQ"] += 1
            message =  self.dict_to_tcp(dict_tcp)
            self.socket_udp.sendto(message.encode(), address)
            print("Three-way handshake was succesfull")
        else:
            raise NameError("Three-way handshake wasn't succesfull")
    def accept(self):
        while True:
            buffer, address = self.recieve_message(64)
            break
        tcp_dict = self.tcp_to_dict(buffer)
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
             buffer, address = self.recieve_message(64)
             break
        tcp_dict = self.tcp_to_dict(buffer)
        sequence2 = tcp_dict["SEQ"]
        print(f"Recieved sequence: {sequence2}")
        if tcp_dict["ACK"] == 1 and tcp_dict["SEQ"] == sequence +2:
            print("Three-way handshake was succesfull")
            self.dest_adr = address[0]
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
            tcp_message += "|||" + tcp_dict["DATOS"] 
        except:
            pass
        return tcp_message
        
