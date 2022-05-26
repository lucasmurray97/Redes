import sys
import socket
from round_robin import RoundRobin
# Recibimos la dirección, puerto y tablas asociadas al router
router_ip = sys.argv[1]
router_port = int(sys.argv[2])
router_table = sys.argv[3]
address = (router_ip, router_port)
print(f"Router ip: {router_ip}, port: {router_port}")
# Leemos la tabla de rutas asociada al router
with open(str(router_table), 'r') as file:
    routes_table = file.read()
def routes_to_dict(routes_table):
    """Función que pasa el .txt con las rutas con la tabla de rutas a un diccionario"""
    routes_dict = {}
    routes = routes_table.split("\n")
    for i in range(len(routes)):
        routes_dict[i] = {}
        splited_route = routes[i].split(" ")
        routes_dict[i]["net_ip"] = splited_route[0].split("/")[0]
        routes_dict[i]["ip_range"] = int(splited_route[0].split("/")[1])
        routes_dict[i]["port_range"] = (int(splited_route[1]), int(splited_route[2]))
        routes_dict[i]["next_hop_ip"] = splited_route[3]
        routes_dict[i]["next_hop_port"] = int(splited_route[4])
        routes_dict[i]["mtu"] = int(splited_route[5])
    return routes_dict
# Pasamos las rutas a un diccionario
routes_dict = routes_to_dict(routes_table)
# Creamos una instancia del algoritmo de round robin
round_robin = RoundRobin(routes_dict)
# Creamos el socket del router
router = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bindeamos el router a la direccion (ip, puerto)
router.bind(address)
# Dejamos al router esperando un mensaje
def get_final_dest(message):
    """Función que toma el mensaje y retorna: (dest_ip, data)"""
    splited_message = message.split(",")
    final_dest_ip = splited_message[0]
    final_dest_port = int(splited_message[1])
    ttl = int(splited_message[2])
    id = splited_message[3]
    offset = int(splited_message[4])
    size = splited_message[5]
    flag = splited_message[6]
    data = splited_message[7]
    return (final_dest_ip, final_dest_port, ttl, id, offset, size, flag, data)
# Forma un mensaje con la estructura de headers ip
def form_message(dest_ip, dest_port, ttl, id, offset, size, flag, data):
    """Función que genera un mensaje ip a partir de los valores que lo componen"""
    return dest_ip+","+str(dest_port)+","+str(ttl)+","+id+","+str(offset)+","+size+","+flag+","+data
def fragment_ip_packet(IP_packet, mtu):
    """Función que fragmenta un mensaje ip en caso de que supere el tamaño asociado al mtu y retorna una lista con los fragmentos"""
    full_size = len(IP_packet.encode())
    # Si no supera el mtu, no lo fragmentamos
    if full_size <= mtu:
        final_dest_ip, final_dest_port, ttl, id, offset, size, flag, data = get_final_dest(IP_packet)
        return [form_message(final_dest_ip, final_dest_port, ttl-1, id, offset, size, flag, data)]
    # Si es que supera el tamaño del mtu, lo fragmentamos
    else:
        fragmented_message = []
        # Recuperamos los valores del mensaje
        splited_message = IP_packet.split(",")
        final_dest_ip = splited_message[0]
        final_dest_port = int(splited_message[1])
        ttl = int(splited_message[2])
        id = splited_message[3]
        offset = int(splited_message[4])
        size = splited_message[5]
        flag = splited_message[6]
        data = splited_message[7]
        data_size = len(data.encode())
        # Tomamos el header original y calculamos el tamaño de los fragmentos
        orig_header = final_dest_ip+","+str(final_dest_port)+","+str(ttl)+","+id+","+str(offset)+","+size+","+flag+","
        header_size = len(orig_header.encode())
        fragment_size = mtu-header_size
        # indice donde parte el fragmento a construirse
        initial_idx = 0
        while data_size > 0:
            # El fragmento parte desde initial_idx y llega hasta initial_idx+fragment_size
            message = data[initial_idx:initial_idx+fragment_size]
            len_message = len(message)
            fragment_size_header = str(len_message)
            # Tomamos el largo del mensaje y lo rellenamos con ceros para que sea de largo 8
            while len(fragment_size_header) < 8:
                fragment_size_header = "0" + fragment_size_header
            # Disminuimos el tamaño restante del mensaje a procesar
            data_size -= fragment_size
            # En caso de que se haya llegado al final del mensaje y tenga flag 0, le asignamos la flag 0 a ese fragmento
            if data_size <= 0 and flag == "0":
                header = final_dest_ip+","+str(final_dest_port)+","+str(ttl-1)+","+id+","+str(offset)+","+fragment_size_header+","+"0"+","
            # Sino, le asignamos la flag 1
            else:
                header = final_dest_ip+","+str(final_dest_port)+","+str(ttl-1)+","+id+","+str(offset)+","+fragment_size_header+","+"1"+","
            # Agregamos el fragmento a la lista
            fragmented_message.append(header+message)
            # Aumentamos el offset en fragment_size
            offset += fragment_size
            # Incrementamos el indice en fragmento_size
            initial_idx+= fragment_size
        return fragmented_message
    
def reassemble_IP_packet(fragment_list):
    """Función que toma una lista de fragmentos, rearma el mensaje original y lo retorno"""
    # Si esque la lista es de tamaño 1
    if len(fragment_list) == 1:
        final_dest_ip, final_dest_port, ttl, id, offset, size, flag, data = get_final_dest(fragment_list[0])
        # Si esque el mensaje no ha sido fragmentado
        if offset == 0 and flag == "0":
            return data
        # Solo nos llegó el fragmento final :(
        else:
            return None
    # Si es que el mensaje viene fragmentado, procesamos los fragmentos
    else:
        # Lista con diccionarios asociados a cada fragmento
        frag_dicts = []
        # Iteramos sobre lo fragmentos
        for i in range(len(fragment_list)):
            # Armamos los diccionarios
            frag_dict = {}
            _, _, _, _, offset, size, flag, data = get_final_dest(fragment_list[i])
            frag_dict["offset"] = offset
            frag_dict["size"] = int(size)
            frag_dict["data"] = data
            frag_dict["flag"] = flag
            frag_dicts.append(frag_dict)
        # Variable con la posicion en donde debería ir el fragmento, en orden
        min_offset = 0
        # Variable con el mensaje reconstruido
        ordered_frags = ""
        finished = False
        # Vamos completando el mensaje en orden
        while not finished:
            partially_completed = False
            for i in range(len(frag_dicts)):
                # Buscamos el mensaje que debería ir en la posicion actual
                if frag_dicts[i]["offset"] == min_offset:
                    min_offset = min_offset + frag_dicts[i]["size"]
                    partially_completed = True
                    # Agregamos el mensaje
                    ordered_frags += frag_dicts[i]["data"]
                    # Si esque llegamos a la ultima posicion, terminamos
                    if frag_dicts[i]["flag"] == "0":
                        finished = True
                    break
            # Si es que no encontramos el mensaje que debería ir en la posición actual, el mensaje no venía completo y retornamos None
            if not partially_completed and not finished:
                print("Message is not complete yet")
                return None
        return ordered_frags

# Loop que se queda esperando mensajes
fragments_dict = {}
while True:
    try:
        buffer, addres = router.recvfrom(256)
        message = buffer.decode()
        # Desarmamos el mensaje
        final_dest_ip, final_dest_port, ttl, id, offset, size, flag, data = get_final_dest(message)
        # Si el ttl del mensaje es 0, lo ignoramos
        if ttl == 0:
            print("TTL = 0, ignoramos el mensaje")
            continue
        # Si el mensaje va dirigido al router, lo imprimimos
        elif final_dest_ip == router_ip and final_dest_port == router_port:
            if id not in fragments_dict.keys():
                fragments_dict[id] = []
            fragments_dict[id].append(message)
            complete_message = reassemble_IP_packet(fragments_dict[id])
            if complete_message != None:
                fragments_dict[id] = []
                print("Me llegó un mensaje:")
                print(complete_message)
        # Si no va dirido al router, tratamos de reenviarlo
        else:
            # Obtenemos la ruta a seguir a través de round robin
            hop_address, mtu = round_robin.get_route(final_dest_ip, final_dest_port)
            # Si existe una ruta, reedirigimos
            if hop_address != None:
                # Fragmentamos el mensaje
                fragmented_message = fragment_ip_packet(message, mtu)
                # Iteramos sobre los fragmentos y los enviamos uno por uno
                for fragment in fragmented_message:
                    print(f"Redirigiendo paquete con destino final {(final_dest_ip, final_dest_port)} desde {(router_ip, router_port)} hacia {hop_address})")
                    print(f"Mensaje enviado: {fragment}")
                    # Enviamos reenviamos el mensaje al router que corresponda
                    router.sendto(fragment.encode(), hop_address)
            # Si no hay una ruta, ignoramos el mensaje
            else:
                print(f"No hay rutas hacia {(final_dest_ip, final_dest_port)}")

        continue  
    except socket.timeout as e:
        print("Aun no recibimos nada...")
        continue




