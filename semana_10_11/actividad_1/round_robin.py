from itertools import cycle
class RoundRobin:
    """Clase que maneja las rutas de los mensajes a través del algoritmo round robin"""
    def __init__(self, routes_dict):
        self.routes_dict = routes_dict # Recibe un diccionario con las rutas
        self.cache = {} # Memoria del algoritmo, parte vacía

    def ip_to_bin(self, ip):
        """Función que transforma una direccion ip en su entero de 32 bits asociado"""
        return ''.join([format(int(i), "8b") for i in ip.split(".")])

    def calc_posible_routes(self, dest_ip, dest_port):
        """Función que revisa las rutas posibles para un par (dest_ip, dest_port) y retorna una lista con las entradas del routes_dict posibles. Retorna un objeto cycle, 
        que permite ciclar por las entradas obtenidas"""
        posible_routes_idx = []
        dest_address_bin = self.ip_to_bin(dest_ip)
        for i in self.routes_dict.keys():
            net_ip = self.ip_to_bin(self.routes_dict[i]["net_ip"])
            ip_range = self.routes_dict[i]["ip_range"]
            port_range = self.routes_dict[i]["port_range"]
            if dest_address_bin[:ip_range] == net_ip[:ip_range] and (port_range[0] <= dest_port <= port_range[1]):
                posible_routes_idx.append(i)
        return cycle(posible_routes_idx) if len(posible_routes_idx) > 0 else None
    
    def get_route(self, dest_ip, dest_port):
        """Función que entrega la ruta por la cual se debe reenviar un mensaje dirigido a (dest_ip, dest_port), retorna (next_hop_ip, next_hop_port)
        si existe una ruta, sino None"""
        posible_routes_idx = self.calc_posible_routes(dest_ip, dest_port) # Obtenemos todas las posibles rutas
        # Si existen rutas
        if posible_routes_idx != None: 
            # Si nunca se ha enviado un mensaje a ese par (dest_ip, dest_port), retornamos la primera ruta disponible
            if (dest_ip, dest_port) not in self.cache.keys():
                key = next(posible_routes_idx)
                self.cache[(dest_ip, dest_port)] = key
                return (self.routes_dict[key]["next_hop_ip"], self.routes_dict[key]["next_hop_port"])
            # Si ya se han enviado mensajes a ese destino
            else:
                # Revisamos cual fue la ultima ruta utilizada
                key = self.cache[(dest_ip, dest_port)]
                while True:
                    if next(posible_routes_idx) == key:
                        # Buscamos la ruta que le sigue
                        next_key = next(posible_routes_idx)
                        # Guardamos esta ruta como la ultima utilizada
                        self.cache[(dest_ip, dest_port)] = next_key
                        # Retornamos esa ruta
                        return (self.routes_dict[next_key]["next_hop_ip"], self.routes_dict[next_key]["next_hop_port"])
        # Si no existen rutas, retornamos NoneS
        else:
            return None


