from posixpath import splitdrive
import sys
import socket
from round_robin import RoundRobin
from timer import Timer
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
    if "" in routes:
        routes.remove("")
    for i in range(len(routes)):
        routes_dict[i] = {}
        splited_route = routes[i].strip().split(" ")
        routes_dict[i]["net_ip"] = splited_route[0].split("/")[0]
        routes_dict[i]["ip_range"] = int(splited_route[0].split("/")[1])
        routes_dict[i]["next_hop_ip"] = splited_route[1]
        routes_dict[i]["next_hop_port"] = int(splited_route[2])
        routes_dict[i]["mtu"] = int(splited_route[3])
        routes_dict[i]["route_dest"] = int(splited_route[4])
        routes_dict[i]["bgp_route"] = []
        for j in range(5, len(splited_route)):
            routes_dict[i]["bgp_route"].append(int(splited_route[j]))
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
    bgp = False
    if "START_BGP" in data:
        bgp = True
    return (final_dest_ip, final_dest_port, ttl, id, offset, size, flag, data, bgp)
# Forma un mensaje con la estructura de headers ip
def form_message(dest_ip, dest_port, ttl, id, offset, size, flag, data):
    """Función que genera un mensaje ip a partir de los valores que lo componen"""
    return dest_ip+","+str(dest_port)+","+str(ttl)+","+id+","+str(offset)+","+size+","+flag+","+data
def fragment_ip_packet(IP_packet, mtu):
    """Función que fragmenta un mensaje ip en caso de que supere el tamaño asociado al mtu y retorna una lista con los fragmentos"""
    full_size = len(IP_packet.encode())
    # Si no supera el mtu, no lo fragmentamos
    if full_size <= mtu:
        final_dest_ip, final_dest_port, ttl, id, offset, size, flag, data, _ = get_final_dest(IP_packet)
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
        final_dest_ip, final_dest_port, ttl, id, offset, size, flag, data, _ = get_final_dest(fragment_list[0])
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
            _, _, _, _, offset, size, flag, data, _ = get_final_dest(fragment_list[i])
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

def create_BGP_message():
    """Crea un mensaje BGP_ROUTES en base al routes_dict actual"""
    first_line = "BGP_ROUTES\n"
    second_line = str(router_port) + "\n"
    message = first_line + second_line
    for i in routes_dict.keys():
        for j in routes_dict[i]["bgp_route"]:
            message += str(j) + " "
        message.strip()
        message += "\n"
    final_line = "END_ROUTES"
    message += final_line
    return message
def start_bgp(message):
    """Inicia el algoritmo bgp"""
    # Se revisan todas las rutas
    for i in routes_dict.keys():
        # Si es que es a un router vecino, se crea y envía el mensaje
        if len(routes_dict[i]["bgp_route"]) == 2:
            dest_ip = routes_dict[i]["next_hop_ip"]
            dest_port = routes_dict[i]["next_hop_port"]
            mtu = routes_dict[i]["mtu"]
            ttl = 500
            id = str(dest_port)
            offset = 0
            size = str(len(message.encode()))
            while len(size) < 8:
                size = "0" + size
            data = message
            message_to_send = form_message(dest_ip, dest_port, ttl, id, offset, size, flag, data)
            fragmented_message = fragment_ip_packet(message_to_send, mtu)
            hop_address = (dest_ip, dest_port)
            for fragment in fragmented_message:
                print(f"Enviando mensaje bgp a vecino: {(dest_ip, dest_port)} desde {(router_ip, router_port)})")
                print(f"Mensaje enviado: {fragment}")
                # Enviamos reenviamos el mensaje al router que corresponda
                router.sendto(fragment.encode(), hop_address)
def check_routes(bgp_message):
    """Función que revisa las rutas del routesr"""
    splited_message = bgp_message.split("\n")[2:][:-1]
    for i in splited_message:
        route = i.strip().split(" ")
        # Si el router está en la ruta, se descarta
        if str(router_port) in route:
            continue
        not_known = True
        updated = False
        # Se revisa si la ruta es conocida
        for i in routes_dict.keys():
            if int(route[0]) == routes_dict[i]["route_dest"]:
                not_known = False
        # Si la ruta es desconocida, se agrega y se marca como que la tabla es desconocida
        if not_known:
            print("Agregué una ruta nueva!")
            pos = len(routes_dict)
            routes_dict[pos] = {}
            routes_dict[pos]["net_ip"] = router_ip
            routes_dict[pos]["ip_range"] = 24
            routes_dict[pos]["bgp_route"] = [int(i) for i in route]
            routes_dict[pos]["bgp_route"].append(router_port)
            routes_dict[pos]["next_hop_ip"] = router_ip
            routes_dict[pos]["next_hop_port"] = routes_dict[pos]["bgp_route"][-2]
            routes_dict[pos]["mtu"] = 500
            routes_dict[pos]["route_dest"] = int(route[0])
            print(routes_dict[pos])
            updated = True
        # Si la ruta es conocida, se revisa si es más corta
        else:
            for i in routes_dict.keys():
                if int(route[0]) == routes_dict[i]["route_dest"]:
                    # Si la ruta es más corta, se actualiza la ruta conocida
                    if len(route) + 1 < len(routes_dict[i]["bgp_route"]):
                        print("Cambiamos ruta conocida")
                        del routes_dict[i]
                        routes_dict[i] = {}
                        routes_dict[i]["net_ip"] = router_ip
                        routes_dict[i]["ip_range"] = 24
                        routes_dict[i]["bgp_route"] = [int(i) for i in route]
                        routes_dict[i]["bgp_route"].append(router_port)
                        routes_dict[i]["next_hop_ip"] = router_ip
                        routes_dict[i]["next_hop_port"] = routes_dict[i]["bgp_route"][-2]
                        routes_dict[i]["mtu"] = 500
                        routes_dict[i]["route_dest"] = int(routes_dict[i]["bgp_route"][0])
                        updated = True
                        break
        # Si se modificó la tabla de rutas, se envía a los vecinos
        if updated:
            bgp_message = create_BGP_message()
            start_bgp(bgp_message)
    return None
def write_routes(wrote_routes):
    """Función que escriba las tablas de rutas una vez que convergen"""
    print("FINISHED BGP, here is the final table:")
    print(create_BGP_message())
    # Se escribe la nueva tabla de rutas en el archivo "bgp_table_router_port.txt, OJO, no puede existir ese archivo"
    table = ""
    for i in routes_dict.keys():
        table += routes_dict[i]["net_ip"] + "/"
        table += str(routes_dict[i]["ip_range"]) + " "
        table += str(routes_dict[i]["next_hop_ip"]) + " "
        table += str(routes_dict[i]["next_hop_port"]) + " "
        table += str(routes_dict[i]["mtu"]) + " "
        table += str(routes_dict[i]["route_dest"]) + " "
        for j in routes_dict[i]["bgp_route"]:
            table += str(j) + " "
        table += "\n"
    file_name = f"bgp_table_{router_port}.txt"
    open(file_name, "x")
    f = open(file_name, "w")
    f.write(table)
    f.close()
    return True
# Loop que se queda esperando mensajes
fragments_dict = {}
# Objeto timer, se inicia el timeout en 10 sec
timer = Timer(10)
router.settimeout(5)
# Booleano que indica si se escribieron las rutas
wrote_routes = False
while True:
    try:
        # Si el timer no hizo timeout, se revisa el timer
        if not timer.timed_out:
            timer.peek_timer()
        # Si el timer hizo timout, y no se ha escrito la nueva tabla de rutas, se escribe
        if timer.timed_out and not wrote_routes:
            wrote_routes = write_routes(wrote_routes)
        buffer, addres = router.recvfrom(256)
        message = buffer.decode()
        # Desarmamos el mensaje
        final_dest_ip, final_dest_port, ttl, id, offset, size, flag, data, bgp = get_final_dest(message)   
        # Si se recibió un mensaje BGP se inicia el algoritmo
        if bgp == True:
            # Si no se ha hecho timeout aún
            if not timer.timed_out:
                print("Starting BGP!")
                # Se reinicia el timer
                timer.restart_timer()
                bgp_message = create_BGP_message()
                start_bgp(bgp_message)
            continue
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
                # Si el mensaje es del tipo BGP_ROUTES
                if "BGP_ROUTES" in complete_message:
                    # Si es que se hizo timeout, se ignora
                    if timer.timed_out:
                        continue
                    # Sino, se reinicia el timer
                    timer.restart_timer()
                    print("Voy a revisar mis rutas")
                    # Se revisan las rutas
                    check_routes(complete_message)
                    continue
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
        continue




