from re import sub
import socket
from dnslib import DNSRecord
from dnslib.dns import CLASS, QTYPE


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

def parserDNS(dns_reply):
    reply_dict = {}
    reply_dict["n_query_elem"] = dns_reply.header.q
    reply_dict["n_answer_elem"] = dns_reply.header.a
    reply_dict["n_auth_elem"] = dns_reply.header.auth
    reply_dict["n_add_elem"] = dns_reply.header.ar
     # query section
    if reply_dict["n_query_elem"]>0:
        first_query = dns_reply.get_q() # primer objeto en la lista all_querys
        reply_dict["query_domain"] = str(first_query.get_qname()) # nombre de dominio por el cual preguntamos
    else:
        reply_dict["query_domain"] = ""
    if reply_dict["n_answer_elem"] > 0:
        first_answer = dns_reply.get_a()
        reply_dict["answer_rdata"] = first_answer.rdata
    else:
        reply_dict["answer_rdata"] = ""
    if reply_dict["n_auth_elem"] > 0:
        authority_section_list = dns_reply.auth # contiene un total de number_of_authority_elements
        authority_section_RR_0 = authority_section_list[0]
        auth_type = QTYPE.get(authority_section_RR_0.rtype)
        authority_section_SOA = authority_section_RR_0.rdata # si recibimos auth_type = 'SOA' este es un objeto tipo dnslib.dns.SOA
        if str(auth_type) == "NS":
            reply_dict["primary_name_server"] = str(authority_section_SOA)
        else:
            reply_dict["primary_name_server"] = authority_section_SOA.get_mname() 
    else:
        reply_dict["primary_name_server"] = ""
    if reply_dict["n_add_elem"] > 0:
        reply_dict["add_address"] = dns_reply.ar[0].rdata
    else:
         reply_dict["add_address"] = ""
    return reply_dict
def ask_for_domain(domain, address, port):
    dns_reply = send_dns_message(domain, address, port)
    reply_dict = parserDNS(dns_reply)
    if reply_dict["n_answer_elem"] == 0:
        if reply_dict["n_add_elem"] > 0:
           return str(reply_dict["add_address"])
        else:
            dns_reply = send_dns_message(reply_dict["primary_name_server"], address, port)
            reply_dict = parserDNS(dns_reply)
    return str(reply_dict["answer_rdata"])
def resolver(domain, cache):
    if domain in cache.keys():
        print("responded from cache")
        return cache[domain], cache
    else:
        sub_domains = domain.split(".")
        initial_daddy = sub_domains.pop() + "."
        initial_address = "8.8.8.8"
        port = 53
        address = ask_for_domain(initial_daddy, initial_address, port)
        print(f"(debug) consultando el NS de .{initial_daddy} en raiz ... ok")
        while len(sub_domains)>0:
            initial_daddy =  sub_domains.pop() + "." + initial_daddy
            print(f"(debug) consultando el NS de .{initial_daddy} en raiz ... ok")
            address = ask_for_domain(initial_daddy, address, port)
        print(f"{domain} es {address}")
        cache[domain] = address
    return address, cache








