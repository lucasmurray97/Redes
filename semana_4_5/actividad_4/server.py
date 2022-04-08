from email import message
from resolver import *
# -*- coding: utf-8 -*-
import socket
from dnslib import DNSRecord, DNSQuestion, RR, DNSHeader, A

# Se crea un socket no orientado a conexion
print('Creando socket - Servidor')
dgram_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#definimos buffsize, message y port
bufsize = 1024
# ocupé el puerto 5053 porque el 5353 me salía siempre ocupado :(
port = 5053
adrs = ('localhost', port)
# Se fija el socket a la address definida y lo dejamos esperando requests
dgram_socket.bind(adrs)
print('... Esperando clientes')
cache = {}
# Nos quedamos esperando mensajes
while True:
    # Recibimos mensajes y se almacena el mensaje en data y la direccion que hizo el request en adrs
    data, adrs = dgram_socket.recvfrom(bufsize)
    # La request es un mensaje dns, se parsea mediante la funcion parse de dnslib y se guarda en d
    d = DNSRecord.parse(data)
    # Se guarda el id de la request, para poder responder con la misma id
    q_id = d.header.id
    # Se ocupa la funcion parserDNS que se programo en resolver.py, guardandose la dns_reply en un diccionario
    q_dict = parserDNS(d)
    # Se guarda el dominio consultado en una variable domain
    domain = q_dict["query_domain"]
    print(' -> Se ha preguntado por el siguiente dominio: ' + domain)
    # Se pregunta por el domain mediante el resolver que se programo, al cual se le pasa un cache vacio inicialmente
    answer, cache = resolver(domain[:-1], cache) # Se guarda la respuesta en answer y el cache actualizado
    # Se crea mensaje dns con la respuesta
    d = DNSRecord(DNSHeader(id = q_id ,qr=1,aa=1,ra=1),q=DNSQuestion(domain[:-1]),a=RR(domain[:-1],rdata=A(answer)))   
    # Se responde a quien preguntó con la respuesta que se creó
    dgram_socket.sendto(bytes(d.pack()), adrs) 

