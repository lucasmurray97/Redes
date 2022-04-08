from email import message
from resolver import *
# -*- coding: utf-8 -*-
import socket
from dnslib import DNSRecord, DNSQuestion, RR, DNSHeader, A

# Socket no orientado a conexión
print('Creando socket - Servidor')
dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#definimos buffsize, message y port
bufsize = 1024
# end_of_message = "10"
port = 5053
adrs = ('localhost', port)
dgram_socket.bind(adrs)
print('... Esperando clientes')
cache = {}
# Nos quedamos esperando mensajes
while True:
    # Recibir mensajes. Este método nos entrega el mensaje junto a la dirección de origen del mensaje
    data, adrs = dgram_socket.recvfrom(bufsize)
    d = DNSRecord.parse(data)
    q_id = d.header.id
    q_dict = parserDNS(d)
    domain = q_dict["query_domain"]
    print(' -> Se ha preguntado por el siguiente dominio: ' + domain)
    answer, cache = resolver(domain[:-1], cache)
    d = DNSRecord(DNSHeader(id = q_id ,qr=1,aa=1,ra=1),q=DNSQuestion(domain[:-1]),a=RR(domain[:-1],rdata=A(answer)))   
    dgram_socket.sendto(bytes(d.pack()), adrs) 

