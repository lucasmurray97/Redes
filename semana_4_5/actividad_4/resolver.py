from re import sub
import socket
from dnslib import DNSRecord
from dnslib.dns import CLASS, QTYPE

# Función del código de ejemplo:
def send_dns_message(query_name, address, port):
    # Acá ya no tenemos que crear el encabezado porque dnslib lo hace por nosotros, por default pregunta por el tipo A
    qname = query_name
    q = DNSRecord.question(qname)
    server_address = (address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # lo enviamos, hacemos cast a bytes de lo que resulte de la función pack() sobre el mensaje
        sock.sendto(bytes(q.pack()), server_address)
        # En data quedará la respuesta a nuestra consulta
        data, _ = sock.recvfrom(4096)
        # le pedimos a dnslib que haga el trabajo de parsing por nosotros
        d = DNSRecord.parse(data)
    finally:
        sock.close()
    # Ojo que los datos de la respuesta van en en una estructura de datos
    return d
# Función que parsea una dns reply obtenida por send_dns_message() y la lleva a una estructura de datos conveniente
def parserDNS(dns_reply):
    # Se genera un diccionario para almacenar la información de la dns_reply
    reply_dict = {}
    # Número de elementos de pregunta que vienen en la dns_reply
    reply_dict["n_query_elem"] = dns_reply.header.q
    # Número de elementos de respuesta que vienen en la dns_reply
    reply_dict["n_answer_elem"] = dns_reply.header.a
    # Número de elementos de authorization que vienen en la dns_reply
    reply_dict["n_auth_elem"] = dns_reply.header.auth
    # Número de elementos adicionales que vienen en la dns_reply
    reply_dict["n_add_elem"] = dns_reply.header.ar
    # Si vienen elementos de pregunta, se almacena el dominio por el que se pregunto en el diccionario, sino se rellena con ""
    if reply_dict["n_query_elem"]>0:
        first_query = dns_reply.get_q() # primer objeto en la lista all_querys
        reply_dict["query_domain"] = str(first_query.get_qname()) # nombre de dominio por el cual preguntamos
    else:
        reply_dict["query_domain"] = ""
    # Si vienen elementos de respuesta, se almacena la ip de respuesta en el diccionario, sino se rellena con ""
    if reply_dict["n_answer_elem"] > 0:
        first_answer = dns_reply.get_a()
        reply_dict["answer_rdata"] = first_answer.rdata
    else:
        reply_dict["answer_rdata"] = ""
    # Si vienen elementos de authorization, se almacenan el server al que hay que ir a preguntar
    if reply_dict["n_auth_elem"] > 0:
        authority_section_list = dns_reply.auth # contiene un total de number_of_authority_elements
        authority_section_RR_0 = authority_section_list[0]
        auth_type = QTYPE.get(authority_section_RR_0.rtype)
        authority_section_SOA = authority_section_RR_0.rdata # si recibimos auth_type = 'SOA' este es un objeto tipo dnslib.dns.SOA
        # Si es de tipo name server, se almacena directamente lo que viene en authority_section_RR_0.rdata
        if str(auth_type) == "NS":
            reply_dict["primary_name_server"] = str(authority_section_SOA)
        # Si no, es un SOA y se obtiene el nombre del servidor mediante get_mname
        else:
            reply_dict["primary_name_server"] = authority_section_SOA.get_mname() 
    # Si no viene nada, se rellena con ""
    else:
        reply_dict["primary_name_server"] = ""
    # Si vienen elementos adicionales, se toma la direccion que viene en esta sección y se guarda en add_address, sino se rellena con ""
    if reply_dict["n_add_elem"] > 0:
        reply_dict["add_address"] = dns_reply.ar[0].rdata
    else:
         reply_dict["add_address"] = ""
    return reply_dict
# Función que pregunta por un dominio "domain" a la ip "address" a través del puerto "port"
def ask_for_domain(domain, address, port):
    # Se manda una query a address, preguntando por domain
    dns_reply = send_dns_message(domain, address, port)
    # Se parsea la respuesta y se guarda en reply_dict
    reply_dict = parserDNS(dns_reply)
    # Si no hay elementos de respuesta, se revisa si hay elementos adicionales, si es que hay se retorna la direccion que viene ahí, sino
    # se vuelve a preguntar, pero esta vez por el primary_name_server. Si hay elementos de respuesta, se retorna la direccion en answer_rdata
    if reply_dict["n_answer_elem"] == 0:
        if reply_dict["n_add_elem"] > 0:
           return str(reply_dict["add_address"])
        else:
            dns_reply = send_dns_message(reply_dict["primary_name_server"], address, port)
            reply_dict = parserDNS(dns_reply)
    return str(reply_dict["answer_rdata"])
# Función que actúa como resolver: pregunta desde la raiz, construyendo el dominio a consultar iterativamente
def resolver(domain, cache):
    # Si la respuesta está en el cache, se retorna directamente la direccion almacenada en el.
    if domain in cache.keys():
        print("responded from cache")
        return cache[domain], cache
    # Si es primera vez que se pregunta por ese dominio:
    else:
        # Se divide el dominio consultado en varios subdominios. Ej: www.uchile.cl -> [www, uchile, cl]
        sub_domains = domain.split(".")
        # Se toma el primer subdominio y se le agrega un "." alfinal
        initial_daddy = sub_domains.pop() + "."
        initial_address = "8.8.8.8" # Se parte con la direccion "8.8.8.8"
        port = 53 #Se utiliza el puerto 53, dedicado a consultas dns
        address = ask_for_domain(initial_daddy, initial_address, port) # Se pregunta por el dominio mas cercano a la raiz y se printea la respuesta
        print(f"(debug) consultando el NS de .{initial_daddy} en raiz ... ok")
        # Se itera sobre los subdomains, construyendo dominios cada vez más "específicos"
        # Ej: se consulta por uchile.cl->www.uchile.cl
        while len(sub_domains)>0:
            initial_daddy =  sub_domains.pop() + "." + initial_daddy
            print(f"(debug) consultando el NS de .{initial_daddy} en raiz ... ok")
            address = ask_for_domain(initial_daddy, address, port)
        # Se printea la respuesta obtenida para el dominio original
        print(f"{domain} es {address}")
        # Se guarda la respuesta en el cache
        cache[domain] = address
        # Se retorna la direccion de respuesta y el cache actualizado
    return address, cache








