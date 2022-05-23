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
    data = splited_message[3]
    return (final_dest_ip, final_dest_port, ttl, data)
# Forma un mensaje con la estructura de headers ip
def form_message(dest_ip, dest_port, ttl, data):
    return dest_ip+","+str(dest_port)+","+str(ttl)+","+data
# Loop que se queda esperando mensajes
while True:
    try:
        buffer, addres = router.recvfrom(64)
        message = buffer.decode()
        # Desarmamos el mensaje
        final_dest_ip, final_dest_port, ttl, data = get_final_dest(message)
        # Si el ttl del mensaje es 0, lo ignoramos
        if ttl == 0:
            print("TTL = 0, ignoramos el mensaje")
            continue
        # Si el mensaje va dirigido al router, lo imprimimos
        elif final_dest_ip == router_ip and final_dest_port == router_port:
            print(data)
        # Si no va dirido al router, tratamos de reenviarlo
        else:
            # Obtenemos la ruta a seguir a través de round robin
            hop_address = round_robin.get_route(final_dest_ip, final_dest_port)
            # Si existe una ruta, reedirigimos
            if hop_address != None:
                print(f"Redirigiendo paquete con destino final {(final_dest_ip, final_dest_port)} desde {(router_ip, router_port)} hacia {hop_address})")
                # Actualizamos el ttl
                message = form_message(final_dest_ip, final_dest_port, ttl-1, data)
                print(f"Mensaje enviado: {message}")
                # Enviamos reenviamos el mensaje al router que corresponda
                router.sendto(message.encode(), hop_address)
            # Si no hay una ruta, ignoramos el mensaje
            else:
                print(f"No hay rutas hacia {(final_dest_ip, final_dest_port)}")

        continue  
    except socket.timeout as e:
        print("Aun no recibimos nada...")
        continue




