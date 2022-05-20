# -*- coding: utf-8 -*-
from audioop import add
from shutil import move
import socket
from random import randrange
import sys
import slidingWindow as sw
import timerList as tm
class socketTCP:
    def __init__(self, orig_address, port, dest_address = None):
        # Socket no orientado a objetos
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Dirección de origen
        self.address = (orig_address, port)
        # Dirección de destino de la conexión
        self.dest_adr = dest_address
        # Secuencia del socket
        self.seq = None
        # Datos por recibir
        self.data_to_recieve = 0
        # Secuencia inicial del socket
        self.init_seq = None
        # Booleano correspondiente a si el socket actualmente está partiendo una conexión o ya inició una
        self.starting_transaction = True
        # Booleano correspondiente a si el socket ya establecío una conexión
        self.established_conection = False
        # Tamaño del buffer del socket
        self.buff_size = None
        # Booleano correspondiente a si se recibió o no el mensaje
        self.message_recieved = None
        # Sliding window del socket
        self.recv_window = None
        # Tamaño de la sliding window
        self.window_size = None
        # Largo del mensaje a enviarse/recibir
        self.message_length = None

    def bind(self):
        """Función que hace bind en el socket sobre la dirección de origen."""
        self.socket_udp.bind((self.address))
    def connect(self, address):
        """Función que realiza el three-way handshake desde el emisor."""
        # Si el socket ya estableció una conexión arroja error
        if self.established_conection:
            raise NameError("You already established a connection!")
        # Se establece la dirección de destino
        self.dest_adr = address
        print(f"Original destiny address: {self.dest_adr}")
        # Se arma el mensaje tcp para iniciar el handshake
        dict_tcp = {}
        dict_tcp["SYN"] = 1
        dict_tcp["ACK"] = 0
        dict_tcp["FIN"] = 0
        dict_tcp["SEQ"] = randrange(101)
        self.seq = dict_tcp["SEQ"]
        print(f"Initial sequence: {self.seq}")
        message = self.dict_to_tcp(dict_tcp)
        message = message.encode()
        # Se envía el mensaje inicial y se queda esperando una respuesta
        self.socket_udp.sendto(message, address)
        while True:
            try:
                buffer, addres = self.socket_udp.recvfrom(64)
                break
            except socket.timeout as e:
                print("No se recibio el primer mensaje del handshake, intentamos denuevo...")
                self.socket_udp.sendto(message, address)
        dict_tcp = self.tcp_to_dict(buffer.decode())
        recieved_seq = dict_tcp["SEQ"]
        print(f"Recieved sequence: {recieved_seq}")
        # Se revisa si el mensaje recibido coincide con lo que se espera.
        if dict_tcp["SYN"] == 1 and dict_tcp["ACK"] == 1 and dict_tcp["SEQ"] == self.seq + 1:
            # Se arma el mensaje de respuesta y actualiza la secuencia del socket.
            dict_tcp["SYN"] = 0
            dict_tcp["ACK"] = 1
            dict_tcp["FIN"] = 0
            dict_tcp["SEQ"] += 1
            self.seq+=1
            message =  self.dict_to_tcp(dict_tcp)
            # Se responde con el mensaje correspondiente
            self.socket_udp.sendto(message.encode(), addres)
            # Se fija la secuencia del socket
            self.seq = dict_tcp["SEQ"]
            # Se marca como que el socket ya tiene una conexión establecida
            self.established_conection = True
            # Se guarda la dirección de destino
            self.dest_adr = addres
            print(f"New destiny address: {self.dest_adr}")
            print(f"Secuencia del socket: {self.seq}")
            print("Three-way handshake was succesfull")
        else:
            # Si la información del mensaje no corresponde, se levanta un error
            raise NameError("Three-way handshake wasn't succesfull")
    def accept(self):
        """Función que implementa el lado del receptor del three-way hanshake"""
        # De tenerse una conexón, se levanta un error
        if self.established_conection:
            raise NameError("You already established a connection!")
        # Se lleva la conexión a un nuevo puerto
        new_port = self.address[1]+1
        new_socketTCP = socketTCP(self.address[0], new_port)
        # Se hace bind en el nuevo puerto
        new_socketTCP.bind()
        # Se espera el mensaje del socket emisor
        while True:
            try:
                buffer, address = self.socket_udp.recvfrom(64)
                break
            except socket.timeout as e:
                print("No se recibió el primer mensaje del handshake, intentamos denuevo...")
        tcp_dict = self.tcp_to_dict(buffer.decode())
        # Si el mensaje no era de sincronización, se levanta un error
        if tcp_dict["SYN"] == 0:
            raise NameError("Message wasn't for sync")
        # Se arma el mansaje de respuesta y se espera la respuesta
        self.seq = tcp_dict["SEQ"]
        print(f"Recieved sequence: {self.seq}")
        tcp_dict["ACK"] = 1
        tcp_dict["SEQ"] +=  1
        self.seq += 1
        sent_sequence = tcp_dict["SEQ"]
        print(f"Sent sequence: {sent_sequence}")
        message = self.dict_to_tcp(tcp_dict)
        while True: 
            new_socketTCP.socket_udp.sendto(message.encode(), address)
            try:
                buffer, address = new_socketTCP.socket_udp.recvfrom(64)
                break
            except socket.timeout as e:
                print("No se recibió el segundo mensaje del handshake, intentamos denuevo...")
        tcp_dict = self.tcp_to_dict(buffer.decode())
        sequence2 = tcp_dict["SEQ"]
        print(f"Recieved sequence: {sequence2}")
        # Se revisa que la información coincida con lo que se espera
        if tcp_dict["ACK"] == 1 and tcp_dict["SEQ"] == self.seq +1:
            # Se actualiza la secuencia del socket, la dirección de destino y se marca como que el socket ya estableció una conexión
            self.seq += 1
            new_socketTCP.dest_adr = address
            new_socketTCP.seq = self.seq
            new_socketTCP.established_conection = True
            print(f"Secuencia del socket: {new_socketTCP.seq}")
            print("Three-way handshake was succesfull")
            return new_socketTCP, new_socketTCP.address
        else:
            # Si la información no calza, se levanta un error
            raise NameError("Three-way handshake wasn't succesfull")

    def tcp_to_dict(self, message):
        """ Función que pasa un mensaje tcp a un diccionario"""
        # [SYN]|||[ACK]|||[FIN]|||[SEQ]|||[DATOS]
        message_list = message.split("|||")
        tcp_dict = {}
        tcp_dict["SYN"] = int(message_list[0])
        tcp_dict["ACK"] = int(message_list[1])
        tcp_dict["FIN"] = int(message_list[2])
        tcp_dict["SEQ"] = int(message_list[3])
        # Si vienen datos, se guardan.
        try:
            tcp_dict["DATOS"] = message_list[4]
        except:
            pass
        return tcp_dict
    def dict_to_tcp(self, tcp_dict):
        """Función que pasa un diccionario, con la estructura del generado por tcp_to_dict(...), a un mensaje tcp"""
        tcp_message = str(tcp_dict["SYN"]) + "|||" + str(tcp_dict["ACK"]) + "|||" + str(tcp_dict["FIN"]) + "|||" + str(tcp_dict["SEQ"])
        try:
            tcp_message += "|||" + str(tcp_dict["DATOS"])
        except:
            pass
        return tcp_message
    def settimeout(self, timeout_in_seconds):
        """Función que establece un timeout para las funciones bloqueantes del socket"""
        self.socket_udp.settimeout(timeout_in_seconds)
    def chop_message(self, message):
        mes_len = len(message)
        # Largo en bytes del mensaje:
        message_length = len(message.encode())
        chunks, chunk_size = mes_len//64 +1, 64

        # Armamos un arreglo con los pedazos del mensaje
        chunked_list = [message_length]
        for i in range(chunks):
            if (i+1)*chunk_size<mes_len:
                chunked_list.append(message[i*chunk_size:(i+1)*chunk_size])
            else:
                chunked_list.append(message[i*chunk_size:mes_len])
        return chunked_list

    def send(self, message, mode="stop_and_wait"):
        """Función que envía un mensaje siguiendo el modo de comunicación que se especifique"""
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            self.send_using_go_back_n(message)
        elif mode == "selective_repeat":
            return self.send_using_selective_repeat(message)
    def recv(self, buff_size, mode="stop_and_wait"):
        """Función que recibe un mensaje siguiendo el modo de comunicación que se especifique"""
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)
        elif mode == "selective_repeat":
            return self.recv_using_selective_repeat(buff_size)
#######################################################################################################################################################
    def set_window_size(self, window_size):
        """Función que fija el tamaño de la sliding window"""
        self.window_size = window_size
########################################### GO BACK N ##################################################################################################
    def send_using_go_back_n(self, message):
        """Función que envía un mensaje mediante go back n"""
        # Se fija la secuencia inicial
        self.init_seq = self.seq
        # Se llena la ventana con los datos cortados en segmentos de 64 bytes
        data_list = self.chop_message(message)
        data_window = sw.SlidingWindow(self.window_size, data_list, self.seq)
        # Se fija el ultimo ack recibido inicial para que la ventana se mueva 1
        last_ack_received = self.seq - 1 # Debe estar entre Y+0 y Y+5
        # Variable que contiene la cantidad de espacios que se mueve la ventana
        step = self.window_size
        # Largo del timeout de la ventana
        timeout = 5
        # Booleando que determina si terminó el envio del mensaje
        finished = False
        # Booleano que determina si se llegó al final del mensaje
        partially_finished = False
        # Lista que contiene el timer de la ventana
        timer_list = tm.TimerList(timeout, 1)
        # para poder usar este timer vamos poner nuestro socket como no bloqueante
        self.socket_udp.setblocking(False)
        # Si el socket aun no tiene una conexión se levanta un error
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
        # Enviamos la ventana inicial
        (partially_finished, last_seq) = self.send_partial_window_go_back_n(data_window, self.window_size, 0, self.init_seq, timer_list)
        # Mientras el envío no haya terminado
        while finished == False:
            try:
                # en cada iteración vemos si nuestro timer hizo timeout
                timeouts = timer_list.get_timed_out_timers()
                # si hizo timeout reenviamos el último segmento
                if len(timeouts) > 0:
                    print("Hubo un timeout, reenviamos toda la ventana")
                    (partially_finished, last_seq) = self.resend_window_go_back_n(data_window, self.window_size, self.init_seq, timer_list)
                    # Si es que llegamos alfinal del mensaje
                    if partially_finished:
                        # Revisamos si recibimos el ack del ultimo mensaje correspondiente a la ultima ventana
                        if last_ack_received == last_seq:
                            # Si esque lo recibimos, termina el envío
                            finished = True
                            continue 

                # si no hubo timeout esperamos el ack del receptor
                if not partially_finished:
                    answer, address = self.socket_udp.recvfrom(64)

            except BlockingIOError:
                # como nuestro socket no es bloqueante, si no llega nada entramos aquí y continuamos (hacemos esto en vez de usar threads)
                continue

            else:
                # si no entramos al except (y no hubo otro error) significa que llegó algo!
                tcp_dict_ = self.tcp_to_dict(answer.decode())
                seq = tcp_dict_["SEQ"]
                print(f"recibimos el ack de: {seq}")
                # si la respuesta es un ack válido
                if tcp_dict_["ACK"]:
                    # detenemos el timer y calculamos el tamaño del step que debe moverse la ventana
                    timer_list.stop_timer(0)
                    if last_ack_received > tcp_dict_["SEQ"]:
                        step = (self.init_seq + 2*self.window_size -1 - last_ack_received) + (tcp_dict_["SEQ"]-self.init_seq)
                    elif last_ack_received == self.init_seq + 2*self.window_size -1:
                        step = (tcp_dict_["SEQ"]-self.init_seq) + 1
                    else:
                        step = tcp_dict_["SEQ"] - last_ack_received
                    print(f"last ack recieved: {last_ack_received}, seq recieved: {seq}")
                    print(f"Step: {step}")
                    # Guardamos la secuencia del mensaje que recibimos
                    last_ack_received = tcp_dict_["SEQ"]
                    # Si esque llegamos al final del mensaje
                    if partially_finished:
                        # Si recibimos la secuencia del ultimo mensaje enviado, marcamos como terminado el envío
                        if last_ack_received == last_seq:
                            print("Recieved last ack!")
                            finished = True
                            return
                        # Si no, volvemos a esperar el ack correspondiente
                        else: 
                            continue
                    # Movemos la ventana una cantidad step de espacios
                    data_window.move_window(step)
                    # Marcamos la posición desde la cual se envían los mensajes
                    start_pos = self.window_size - step   
                    # Enviamos la porción de la ventana que corresponda
                    (partially_finished, last_seq) = self.send_partial_window_go_back_n(data_window, self.window_size, start_pos, self.init_seq, timer_list)
    def send_partial_window_go_back_n(self, data_window, window_size, start_pos, initial_seq, timer_list):
        """Función que envía una ventana parcialmente, desde la posición start_pos"""
        print("Window:")
        print(data_window)
        # Iniciamos el timer de la ventana
        timer_list.start_timer(0)
        # Iteramos sobre los segmentos de la ventana, desde start_pos hasta el final
        for i in range(start_pos, window_size):
            # Armamos el mensaje tcp
            tcp_dict = {}
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 0
            tcp_dict["FIN"] = 0
            tcp_dict["DATOS"] = data_window.get_data(i)
            tcp_dict["SEQ"] = data_window.get_sequence_number(i)
            print(tcp_dict["DATOS"])
            # Si esque llegamos al final del mensaje, marcamos que llegamos al final y retornamos la secuencia del ultimo mensaje de la ventana
            if tcp_dict["DATOS"] == None:
                print("Partially Finished!")
                print(f"We must wait for the last ack: {data_window.get_sequence_number(i-1)}")
                return (True, data_window.get_sequence_number(i-1))
            # Actualizamos la secuencia del socket
            message_tcp = self.dict_to_tcp(tcp_dict)
            if self.seq == initial_seq + 2*window_size -1:
                self.seq = initial_seq
            else:
                self.seq += 1
            # Enviamos el segmento
            print(f"Enviamos: {message_tcp}")
            self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)
            # Si no hemos llegado al final del mensaje no lo marcamos y no retornamos la secuencia final
        return (False, None)
    def resend_window_go_back_n(self, data_window, window_size, initial_seq, timer_list):
        """Función que envía una ventana completa"""
        print("Reenviamos la siguiente ventana")
        print("Window:")
        print(data_window)
        # Se inicia el timer
        timer_list.start_timer(0)
        # Se itera sobre toda la ventana actual
        for i in range(0, window_size):   
            # Se arma el mensaje
            tcp_dict = {}
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 0
            tcp_dict["FIN"] = 0
            tcp_dict["DATOS"] = data_window.get_data(i)
            tcp_dict["SEQ"] = data_window.get_sequence_number(i)
            print(tcp_dict["DATOS"])
            # Se revisa si se llegó alfinal del mensaje
            if tcp_dict["DATOS"] == None:
                # Si esque se llegó, se marca como parcialmente finalizado el envío y se retorna la secuencia del ultimo mensaje de la ventana
                print("Partially Finished!")
                print(f"We must wait for the last ack: {data_window.get_sequence_number(i-1)}")
                return (True, data_window.get_sequence_number(i-1))
            message_tcp = self.dict_to_tcp(tcp_dict)
            # No actualizamos la secuencia del socket
            print(f"Enviamos: {message_tcp}")
            # Se envía el mensaje
            self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)
            # Si no se ha llegado alfinal del mensaje, no se marca y no se retorna la secuencia final
        return (False, None)
    
    def recv_using_go_back_n(self, buff_size):
        """Función que recibe un mensaje utilizando go back n"""
        # Si tiene una conexion establecida, se levanta un error
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
        # En caso de que este empezando la transmision, esperamos el largo del mensaje:
        if self.starting_transaction:
            while True:
                try:
                    # Recibimos el mensaje
                    buffer, address = self.socket_udp.recvfrom(128)  # Recibimos el largo del mensaje
                    message = buffer.decode()
                    tcp_dict = self.tcp_to_dict(message)
                    if tcp_dict["SEQ"] != self.seq:
                        continue
                    else:
                        break
                except socket.timeout as e:
                    # Si no logramos recibirlo, nos quedamos esperando hasta recibirlo.
                    print("No se obtuvo respuesta acerca del largo del mensaje, intentamos denuevo...")
                
            # Si el mensaje contiene la secuencia de final, se maneja el close
            if tcp_dict["FIN"] == 1:
                # Se establece un máximo de timeouts de 4
                nmr_timeouts = 0
                print("Recieved terminating sequence!")
                # Se incrementa la secuencia en 1
                self.seq += 1
                # Se arma el mensaje de respuesta
                closing_dict = {}
                closing_dict["SYN"] = 0
                closing_dict["ACK"] = 1
                closing_dict["FIN"] = 1
                closing_dict["SEQ"] = self.seq
                while True:
                    print("Sent terminating sequence!")
                    self.socket_udp.sendto(self.dict_to_tcp(closing_dict).encode(), self.dest_adr)
                    # Nos quedamos esperando una respuesta
                    try:
                        buffer, address = self.socket_udp.recvfrom(128)
                    except socket.timeout as e:
                        # Si no la logramos recibir, volvemos a enviar el mensaje (hasta 4 veces)
                        print("No se obtuvo respuesta, intentamos denuevo...")
                        if nmr_timeouts >= 4:
                            self.starting_transaction = True
                            self.established_conection = False
                            self.socket_udp.close()
                            break
                        else:
                            nmr_timeouts+=1
                            continue
                            
                    ans_dict = self.tcp_to_dict(buffer.decode())
                    # Se revisa que el mensaje recibido cumple el patron de close, sino volvemos a comenzar.
                    if ans_dict["ACK"] == 1 and ans_dict["SEQ"] == self.seq + 1 or nmr_timeouts >= 4:
                        print("Recieved terminating sequence 2!")
                        self.starting_transaction = True
                        self.established_conection = False
                        self.socket_udp.close()
                        break
                return
            # Guardamos el largo del mensaje total en message_length
            self.init_seq = self.seq
            print(f"initial sequence: {self.init_seq}")
            message_length = int(tcp_dict["DATOS"])
            # Establecemos que quedan message_length bytes por recibir
            self.data_to_recieve = message_length
            # Actualizamos la secuencia
            self.seq = tcp_dict["SEQ"]
            # Armamos el mensaje tcp
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 1
            tcp_dict["FIN"] = 0
            tcp_dict["SEQ"] = self.seq
            # Avisamos que recibimos el mensaje y actualizamos la secuencia
            self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
            self.seq += 1
            # Marcamos que el socket ya partió la transmision
            self.starting_transaction = False
            print(f"Message-Length -> Secuencia: {self.seq}")
        # Si ya se está recibiendo un mensaje y quedan datos por recibir
        if self.data_to_recieve > 0:
            print(f"Quedan {self.data_to_recieve} por recibir")
            message_recieved = ""
            # Mientras haya espacio en el buffer
            while buff_size > 0:
                while True:
                    # Nos quedamos esperando el mensaje
                    try:
                        buffer, address = self.socket_udp.recvfrom(128)
                        break
                    except socket.timeout as e:
                        # Si no lo recibimos, nos quedamos esperandolo
                        print("No se obtuvo respuesta, intentamos denuevo...")
                        continue
                tcp_dict_ = self.tcp_to_dict(buffer.decode()) 
                seq = tcp_dict_["SEQ"]
                # Si la secuencia del mensaje recibido es menor a la secuencia actual, volvemos a esperar un mensaje
                if seq < self.seq:
                    print(f"Mensaje repetido: {seq}, estamos en {self.seq}")
                    continue
                # Si la secuencia del mensaje recibido es mayor a la secuencia actual, descartamos el mensaje y volvemos a esperar un mensaje
                elif seq > self.seq:
                    print(f"Se perdió un mensaje, lo descartamos!, secuencia: {self.seq}, llego: {seq}")
                    continue
                # Si la secuencia calza, seguimos
                else:
                    print("Recibimos un mensaje")
                    print(f"Mensajes -> Secuencia: {self.seq}")
                    # Armamos el mensaje de respuesta
                    tcp_dict = {}
                    tcp_dict["SYN"] = 0
                    tcp_dict["ACK"] = 1
                    tcp_dict["FIN"] = 0
                    tcp_dict["SEQ"] = self.seq
                    # Actualizamos la secuencia del socket:
                    if seq == self.init_seq + 2*self.window_size -1:
                        self.seq = self.init_seq
                    else:
                        self.seq += 1
                    # Enviamos la respuesta
                    self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                    print(f"Respondemos: {self.dict_to_tcp(tcp_dict)}")
                    # Agregamos el mensaje leido a lo que ya llevamos leido
                    message_recieved += tcp_dict_["DATOS"]
                    print(message_recieved)
                    # Restamos lo leido a lo que nos queda por leer
                    self.data_to_recieve -= len(tcp_dict_["DATOS"].encode())
                    # Disminuimos el tamaño del buffer
                    buff_size -= len(tcp_dict_["DATOS"].encode())
                    # Si no nos queda data por recibir, marcamos como esperando conexion 
                    if self.data_to_recieve == 0:
                        print("Finished recieving message")
                        self.starting_transaction = True
                        self.init_seq = None
                        break
        return message_recieved 

########################################### Selective Repeat ##################################################################################################

    def send_using_selective_repeat(self, message):
        """Función que envía utilizando selective repeat"""
        # Secuencia inicial del envío
        self.init_seq = self.seq
        # Cargamos el mensaje en la ventana
        data_list = self.chop_message(message)
        data_window = sw.SlidingWindow(self.window_size, data_list, self.seq)
        # Secuencia del ultimo mensaje recibido
        last_ack_received = self.seq - 1 # Debe estar entre Y+0 y Y+5
        step = self.window_size
        # Timeout de los timers
        timeout = 5
        # Booleano que marca como finalizado el envío
        finished = False
        # Booleano que marca que se llegó alfinal de la ventana
        partially_finished = False
        # Lista de timers, tamaño window_size
        timeout_list = tm.TimerList(timeout, self.window_size)
        # Secuencias de los mensajes recibidos, no es histórica, se va actualizando
        recieved_acks = [] # [Y, Y+1, Y+2, ...]
        # Secuencias de los mensajes enviados, evita reenvios innecesarios
        sent = [] # [Y, Y+1, Y+2, ...]
        # Diccionario que asocia una secuencia con el indice del timer que le corresponde
        seq_timer = {}
        # para poder usar este timer vamos poner nuestro socket como no bloqueante
        self.socket_udp.setblocking(False)
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
        # Enviamos la ventana inicial
        (partially_finished, last_seq) = self.send_pending_seg(data_window, self.window_size, self.init_seq, timeout_list, recieved_acks, sent, seq_timer)
        while finished == False:
            try:
                # en cada iteración vemos si nuestro timer hizo timeout
                timeouts = timeout_list.get_timed_out_timers()
                # Si hay timeouts, reenviamos los mensajes correspondientes
                if len(timeouts) > 0:
                    print("Hubo un timeout, reenviamos toda la ventana")
                    (partially_finished, last_seq)= self.resend_timed_outs(data_window, self.window_size, timeouts, timeout_list, seq_timer, recieved_acks)
                    # Si esque se llegó alfinal de la ventana
                    if partially_finished:
                        finish = True
                        for i in range(self.window_size):
                            if data_window.get_sequence_number(i) not in recieved_acks and data_window.get_sequence_number(i) != None:
                                # Revisamos si se recibieron todos los acks de la ultima ventana
                                print(f"Haven't recieved {data_window.get_sequence_number(i)} acks yet")
                                finish = False
                        # Si se recibieron todos, se marca como finalizado el envío
                        if finish:
                            finished = True
                        continue
                # si no hubo timeout esperamos el ack del receptor
                answer, address = self.socket_udp.recvfrom(64)

            except BlockingIOError:
                # como nuestro socket no es bloqueante, si no llega nada entramos aquí y continuamos (hacemos esto en vez de usar threads)
                continue

            else:
                # si no entramos al except (y no hubo otro error) significa que llegó algo!
                # si la respuesta es un ack válido
                tcp_dict_ = self.tcp_to_dict(answer.decode())
                seq = tcp_dict_["SEQ"]
                last_ack_received = seq
                print(f"recibimos el ack de: {seq}")
                # Actualizamos los ack recibidos e intentamos movernos
                recieved_acks = self.check_recieved(tcp_dict_, data_window, self.window_size, recieved_acks, timeout_list, sent, seq_timer)
                # Si es que llegamos al final de la ventana
                if partially_finished:
                        # Revisamos si recibimos todos los acks correspondientes
                        finish = True
                        for i in range(self.window_size):
                            if data_window.get_sequence_number(i) not in recieved_acks and data_window.get_sequence_number(i) != None:
                                print(f"Haven't recieved {data_window.get_sequence_number(i)} acks yet")
                                finish = False
                        # De ser así, marcamos como finalizado el envío
                        if finish:
                            finished = True
                        continue
                # Enviamos los mensajes pendientes de la ventana que se movió
                (partially_finished, last_seq) = self.send_pending_seg(data_window, self.window_size, self.init_seq, timeout_list, recieved_acks, sent, seq_timer)

    def send_pending_seg(self, data_window, window_size, init_seq, timeout_list, recieved_acks, sent, seq_timer):
        """Función que envía los segmentos pendientes"""
        # Revisamos toda la ventana
        for i in range(window_size):
            sequence = data_window.get_sequence_number(i)
            # Si ya se recibió el ack de ese segmento, no se reenvía
            if sequence in recieved_acks or sequence in sent:
                continue
            # Armamos el mensaje tcp
            message = data_window.get_data(i)
            tcp_dict = {}
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 0
            tcp_dict["FIN"] = 0
            tcp_dict["DATOS"] = message
            tcp_dict["SEQ"] = sequence
            if tcp_dict["DATOS"] == None:
                print("Partially Finished!")
                return (True, data_window.get_sequence_number(i-1))
            message_tcp = self.dict_to_tcp(tcp_dict)
            # No actualizamos la secuencia del socket
            print(f"Enviamos: {message}, {sequence}")
            self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)
            # Iniciamos el timer de ese elemento de la ventana:
            for j in range(window_size):
                if timeout_list.timer_list[j] == False:
                    timeout_list.start_timer(j) # Como sabemos que no estaba ocupado?
                    seq_timer[sequence] = j # Asociamos el mensaje a un timer
                    break
            sent.append(sequence) # Agregamos la secuencia a los mensajes enviados
        return (False, None)
    
    def try_to_move(self, data_window, window_size, recieved_acks, sent):
        """Funcion que trata de mover la ventana todo lo que se pueda"""
        step = 0
        for i in range(window_size):
            sequence = data_window.get_sequence_number(i)
            # Si ya se recibió el ack de ese segmento, incrementamos step
            if sequence in recieved_acks:
                step+=1
                recieved_acks.remove(sequence)
            # Si no, dejamos de incrementar step
            else:
                break
        # Eliminamos los segmentos que ya no van a aparecer en la ventana actual de los mensajes enviados
        for i in range(step):
            sequence = data_window.get_sequence_number(i)
            sent.remove(sequence)
        # Movemos la ventana
        data_window.move_window(step)

    def resend_timed_outs(self, data_window, window_size, timeouts, timeout_list, seq_timer, recieved_acks):
        """Función que reenvía los segmentos cuyo timer haya echo timeout"""
        for i in range(window_size):
            sequence = data_window.get_sequence_number(i)
            # Si ya se recibió el ack de ese segmento o el segmento aun no hace timeout, no se reenvía
            if sequence in seq_timer.keys():
                if seq_timer[sequence] not in timeouts:
                    continue
            if sequence in recieved_acks:
                continue
            # Armamos el mensaje tcp
            message = data_window.get_data(i)
            tcp_dict = {}
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 0
            tcp_dict["FIN"] = 0
            tcp_dict["DATOS"] = message
            tcp_dict["SEQ"] = sequence
            if tcp_dict["DATOS"] == None:
                print("Partially Finished!")
                return (True, data_window.get_sequence_number(i-1))
            message_tcp = self.dict_to_tcp(tcp_dict)
            # No actualizamos la secuencia del socket
            print(f"Enviamos: {message}, {sequence}")
            self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)
            # Iniciamos el timer de ese elemento de la ventana:
            timeout_list.start_timer(seq_timer[sequence])
        return (False, None)
    def check_recieved(self, message_dict, data_window, window_size, recieved_acks, timeout_list, sent, seq_timer):
        """Función que revisa los acks que se han recibido en la ventana actual"""
        seq = message_dict["SEQ"]
        # Iteramos sobre la ventana, buscando el segmento con la secuencia que se recibió
        for i in range(window_size):
            sequence = data_window.get_sequence_number(i)
            if seq == sequence:
                # Si es que no estaba en los acks recibidos, se agrega
                if sequence not in recieved_acks:
                    recieved_acks.append(sequence)
                    # Paramos el timer del segmento asociado y marcamos el timer como desocupado
                    timeout_list.stop_timer(seq_timer[seq])
                    timeout_list.timer_list[seq_timer[seq]] = False
                    # Eliminamos la relación secuencia-timer de seq_timer
                    del seq_timer[seq]
        # Nos intentamos mover todo lo que podemos
        self.try_to_move(data_window, window_size, recieved_acks, sent)
        # Retornamos una lista con los mensajes para los cuales se han recibidos acks
        return recieved_acks

    def recv_using_selective_repeat(self, buff_size):
        """Función que recibe un mensaje ocupando selective repeat"""
        # Si tiene una conexion establecida, se levanta un error
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
        # En caso de que este empezando la transmision, esperamos el largo del mensaje:
        if self.starting_transaction:
            while True:
                try:
                    # Recibimos el mensaje
                    buffer, address = self.socket_udp.recvfrom(128)  # Recibimos el largo del mensaje
                    message = buffer.decode()
                    tcp_dict = self.tcp_to_dict(message)
                    if tcp_dict["SEQ"] != self.seq:
                        continue
                    else:
                        break
                except socket.timeout as e:
                    # Si no logramos recibirlo, nos quedamos esperando hasta recibirlo.
                    print("No se obtuvo respuesta acerca del largo del mensaje, intentamos denuevo...")
                
            # Si el mensaje contiene la secuencia de final, se maneja el close
            if tcp_dict["FIN"] == 1:
                # Se establece un máximo de timeouts de 4
                nmr_timeouts = 0
                print("Recieved terminating sequence!")
                # Se incrementa la secuencia en 1
                self.seq += 1
                # Se arma el mensaje de respuesta
                closing_dict = {}
                closing_dict["SYN"] = 0
                closing_dict["ACK"] = 1
                closing_dict["FIN"] = 1
                closing_dict["SEQ"] = self.seq
                while True:
                    print("Sent terminating sequence!")
                    self.socket_udp.sendto(self.dict_to_tcp(closing_dict).encode(), self.dest_adr)
                    # Nos quedamos esperando una respuesta
                    try:
                        buffer, address = self.socket_udp.recvfrom(128)
                    except socket.timeout as e:
                        # Si no la logramos recibir, volvemos a enviar el mensaje (hasta 4 veces)
                        print("No se obtuvo respuesta, intentamos denuevo...")
                        if nmr_timeouts >= 4:
                            self.starting_transaction = True
                            self.established_conection = False
                            self.socket_udp.close()
                            break
                        else:
                            nmr_timeouts+=1
                            continue
                            
                    ans_dict = self.tcp_to_dict(buffer.decode())
                    # Se revisa que el mensaje recibido cumple el patron de close, sino volvemos a comenzar.
                    if ans_dict["ACK"] == 1 and ans_dict["SEQ"] == self.seq + 1 or nmr_timeouts >= 4:
                        print("Recieved terminating sequence 2!")
                        self.starting_transaction = True
                        self.established_conection = False
                        self.socket_udp.close()
                        break
                return
            # Guardamos el largo del mensaje total en message_length
            self.init_seq = self.seq
            print(f"initial sequence: {self.init_seq}")
            self.message_length = int(tcp_dict["DATOS"])
            # Establecemos que quedan message_length bytes por recibir
            self.data_to_recieve = self.message_length
            # Creamos la ventana vacía:
            empty_list = [None for i in range(self.message_length)]
            self.recv_window = sw.SlidingWindow(self.window_size, empty_list, self.seq)
            self.add_to_window(self.seq, self.message_length, self.recv_window, self.window_size)
            # Actualizamos la secuencia
            self.seq = tcp_dict["SEQ"]
            # Armamos el mensaje tcp
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 1
            tcp_dict["FIN"] = 0
            tcp_dict["SEQ"] = self.seq
            # Avisamos que recibimos el mensaje y actualizamos la secuencia
            self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
            self.seq += 1
            # Marcamos que el socket ya partió la transmision
            self.starting_transaction = False
            print(f"Message-Length -> Secuencia: {self.seq}")
        # Si ya se está recibiendo un mensaje y quedan datos por recibir
        if self.data_to_recieve > 0:
            print(f"Quedan {self.data_to_recieve} por recibir")
            self.message_recieved = ""
            self.buff_size = buff_size
            # Mientras haya espacio en el buffer
            while self.buff_size > 0:
                while True:
                    # Nos quedamos esperando el mensaje
                    try:
                        buffer, address = self.socket_udp.recvfrom(128)
                        break
                    except socket.timeout as e:
                        # Si no lo recibimos, nos quedamos esperandolo
                        print("No se obtuvo respuesta, intentamos denuevo...")
                tcp_dict_ = self.tcp_to_dict(buffer.decode()) 
                # Si la secuencia del mensaje recibido es menor a la secuencia actual, respondemos con el mensaje original
                seq = tcp_dict_["SEQ"]
                # Revisamos si el mensaje recibido cae en el rango asociado a la ventana
                if self.check_range(self.recv_window, self.window_size, tcp_dict_, self.message_recieved, self.buff_size):
                    print(f"Aceptamos el mensaje con secuencia: {seq}")
                    print(f"Quedan {self.data_to_recieve} por recibir")
                    print(f"El buffer está en: {self.buff_size}")
                    if self.data_to_recieve == 0:
                        # Si no queda data por recibir, terminamos
                        print("Finished recieving message")
                        self.starting_transaction = True
                        self.init_seq = None
                        self.message_length = None
                        self.data_to_recieve = 0
                        break
                # Si la secuencia no calza, seguimos esperando mensajes
                else:
                    print(f"Descartamos el mensaje con secuencia: {seq}")
                    continue           
        return self.message_recieved

    # Revisa si el mensaje pertenece al rango esperado y responde con acks
    def check_range(self, recv_window, window_size, tcp_dict, message_recieved, buff_size):
        seq = tcp_dict["SEQ"]
        message = tcp_dict["DATOS"]
        # Si está en el rango
        if seq in self.expected_range(recv_window, window_size):
            # Agregamos el mensaje a la ventana
            self.add_to_window(seq, message, recv_window, window_size)
            # Enviamos el ack correspondiente
            self.send_ack(seq)
            # Nos intentamos mover
            self.try_to_move_r(recv_window, window_size, message_recieved, buff_size)
            return True
        # Si no, enviamos el ack solamente pero descartamos el mensaje
        else:
            self.send_ack(seq)
            return False
    # Nos entrega una lista con los posibles valores de la secuencia
    def expected_range(self, recv_window, window_size):
        exp_range = []
        for i in range(window_size):
            exp_range.append(recv_window.get_sequence_number(i))
        return exp_range
    
    # Agrega un mensaje a la ventana en el puesto que corresponde
    def add_to_window(self, seq, message, recv_window, window_size):
        # Iteramos sobre la ventana
        for i in range(window_size):
            if seq == recv_window.get_sequence_number(i):
                # Si encontramos el segmento donde debería ir, lo agregamos
                print(f"added message in slot {seq}-{recv_window.get_sequence_number(i)}")
                print(recv_window)
                print(i)
                recv_window.put_data(message, seq, i)

    # Trata de avanzar la ventana lo mas que pueda y agrega los mensajes que quedaron afuera al mensaje total
    def try_to_move_r(self, recv_window, window_size, message_recieved, buff_size):
        step = 0
        # Iteramos sobre toda la ventana
        for i in range(window_size):
            # Si no hemos llegado al final del mensaje, incrementamos step
            if recv_window.get_data(i) != None:
                step+=1
                # Si no corresponde al mensaje que contiene el largo
                if recv_window.get_data(i) != self.message_length:
                    # Agremos el segmento al mensaje, decrementamos la data por recibir y el tamaño restante del buffer
                    self.message_recieved+=str(recv_window.get_data(i))
                    self.data_to_recieve-=len(str(recv_window.get_data(i)).encode())
                    self.buff_size-=len(str(recv_window.get_data(i)).encode())
            else:
                break
        print(recv_window)
        # Movemos la ventana step espacios
        recv_window.move_window(step)

    # Envía el ack correspondiente:
    def send_ack(self, seq):
        tcp_dict = {}
        tcp_dict["SYN"] = 0
        tcp_dict["ACK"] = 1
        tcp_dict["FIN"] = 0
        tcp_dict["SEQ"] = seq
        # Avisamos que recibimos el mensaje y actualizamos la secuencia
        print(f"Sent ack for: {seq}")
        self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)

########################################### STOP AND WAIT ##################################################################################################

    def send_using_stop_and_wait(self, message):
        # Calculamos la cantidad de "pedazos" en los que hay que dividir el mensaje
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
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
        print(f"Largo del mensaje a enviar: {message_length}")
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
                try:
                    buffer, address = self.socket_udp.recvfrom(64)
                    break
                except socket.timeout as e:
                    print("No se obtuvo respuesta al enviar el largo del mensaje, intentamos denuevo...")
                    self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)    
            tcp_dict_ = self.tcp_to_dict(buffer.decode())
            # Si es que recibimos un acknowledge y la secuencia calza con el largo del mensaje que nosotros enviamos, dejamos de esperar/pedir el mensaje
            if tcp_dict_["ACK"] == 1 and tcp_dict_["SEQ"] == self.seq + len(str(message_length).encode()):
                self.seq += len(str(message_length).encode())
                print(f"Message-Lenght -> Secuencia: {self.seq}")
                break
            else:
                print("El mensaje recibido no coincide, tratamos denuevo...")
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
                        print("No se obtuvo respuesta, intentamos denuevo...")
                        self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)    
                # Pasamos la respuesta a un tcp_dict
                tcp_dict_ = self.tcp_to_dict(buffer.decode()) 
                # Si recibimos un acknowledge y la secuencia es igual a la secuencia anterior mas el largo en bytes del mensaje enviado pasamos al pedazo siguiente
                if tcp_dict_["ACK"] == 1 and tcp_dict_["SEQ"] == self.seq + len(m.encode()):
                    self.seq += len(m.encode())
                    print(f"Mensajes -> Secuencia: {self.seq}")
                    break
                else:
                   print("El mensaje recibido no coincide, tratamos denuevo...")
                   continue

    def recv_using_stop_and_wait(self, buff_size):
        # Si tiene una conexion establecida, se levanta un error
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
        # En caso de que este empezando la transmision, esperamos el largo del mensaje:
        if self.starting_transaction:
            while True:
                try:
                    # Recibimos el mensaje
                    buffer, address = self.socket_udp.recvfrom(128)  # Recibimos el largo del mensaje
                    break
                except socket.timeout as e:
                    # Si no logramos recibirlo, nos quedamos esperando hasta recibirlo.
                    print("No se obtuvo respuesta acerca del largo del mensaje, intentamos denuevo...")
            message = buffer.decode()
            tcp_dict = self.tcp_to_dict(message)
            # Si el mensaje contiene la secuencia de final, se maneja el close
            if tcp_dict["FIN"] == 1:
                # Se establece un máximo de timeouts de 4
                nmr_timeouts = 0
                print("Recieved terminating sequence!")
                # Se incrementa la secuencia en 1
                self.seq += 1
                # Se arma el mensaje de respuesta
                closing_dict = {}
                closing_dict["SYN"] = 0
                closing_dict["ACK"] = 1
                closing_dict["FIN"] = 1
                closing_dict["SEQ"] = self.seq
                while True:
                    print("Sent terminating sequence!")
                    self.socket_udp.sendto(self.dict_to_tcp(closing_dict).encode(), self.dest_adr)
                    # Nos quedamos esperando una respuesta
                    try:
                        buffer, address = self.socket_udp.recvfrom(128)
                    except socket.timeout as e:
                        # Si no la logramos recibir, volvemos a enviar el mensaje (hasta 4 veces)
                        print("No se obtuvo respuesta, intentamos denuevo...")
                        if nmr_timeouts >= 4:
                            self.starting_transaction = True
                            self.established_conection = False
                            self.socket_udp.close()
                            break
                        else:
                            nmr_timeouts+=1
                            continue
                            
                    ans_dict = self.tcp_to_dict(buffer.decode())
                    # Se revisa que el mensaje recibido cumple el patron de close, sino volvemos a comenzar.
                    if ans_dict["ACK"] == 1 and ans_dict["SEQ"] == self.seq + 1 or nmr_timeouts >= 4:
                        print("Recieved terminating sequence 2!")
                        self.starting_transaction = True
                        self.established_conection = False
                        self.socket_udp.close()
                        break
                return
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
            # Avisamos que recibimos el mensaje y actualizamos la secuencia
            self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
            # Marcamos que el socket ya partió la transmision
            self.starting_transaction = False
            print(f"Message-Length -> Secuencia: {self.seq}")
        # Si ya se está recibiendo un mensaje y quedan datos por recibir
        if self.data_to_recieve > 0:
            message_recieved = ""
            # Mientras haya espacio en el buffer
            while buff_size > 0:
                while True:
                    # Nos quedamos esperando el mensaje
                    try:
                        buffer, address = self.socket_udp.recvfrom(128)
                        break
                    except socket.timeout as e:
                        # Si no lo recibimos, nos quedamos esperandolo
                        print("No se obtuvo respuesta, intentamos denuevo...")
                tcp_dict_ = self.tcp_to_dict(buffer.decode()) 
                # Si la secuencia del mensaje recibido es menor a la secuencia actual, respondemos con el mensaje original
                if tcp_dict_["SEQ"] < self.seq:
                    print("Mensaje repetido!")
                    # Armamos el mensaje de respuesta
                    tcp_dict= {}
                    tcp_dict["SYN"] = 0
                    tcp_dict["ACK"] = 1
                    tcp_dict["FIN"] = 0
                    tcp_dict["SEQ"] = self.seq
                    # Enviamos el mensaje de respuesta
                    self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                # Si la secuencia calza, seguimos
                else:
                    # Incrementamos la secuencia del socket
                    self.seq += len(tcp_dict_["DATOS"].encode())
                    print(f"Mensajes -> Secuencia: {self.seq}")
                    # Armamos el mensaje de respuesta
                    tcp_dict = {}
                    tcp_dict["SYN"] = 0
                    tcp_dict["ACK"] = 1
                    tcp_dict["FIN"] = 0
                    tcp_dict["SEQ"] = self.seq
                    # Enviamos la respuesta
                    self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                    # Agregamos el mensaje leido a lo que ya llevamos leido
                    message_recieved += tcp_dict_["DATOS"]
                    # Restamos lo leido a lo que nos queda por leer
                    self.data_to_recieve -= len(tcp_dict_["DATOS"].encode())
                    # Disminuimos el tamaño del buffer
                    buff_size -= len(tcp_dict_["DATOS"].encode())
                    # Si no nos queda data por recibir, marcamos como esperando conexion 
                    if self.data_to_recieve == 0:
                        print("Finished recieving message")
                        self.starting_transaction = True
                        break
        return message_recieved 
    def close(self):
        # Creamos el mensaje de finalización
        tcp_dict = {}
        tcp_dict["SYN"] = 0
        tcp_dict["ACK"] = 0
        tcp_dict["FIN"] = 1
        tcp_dict["SEQ"] = self.seq
        while True:
            while True:
                # Se envia el mensaje
                self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                print("Sent terminating sequence!")
                # Se espera la respuesta
                try:
                    buffer, address = self.socket_udp.recvfrom(128)
                    break
                except socket.timeout as e:
                    # Si no se recibe la respuesta, vuelve a enviar el mensaje y se queda esperando
                    print("No se obtuvo respuesta, intentamos denuevo...")
            # Se pasa la respuesta a un diccionario
            ans_dict = self.tcp_to_dict(buffer.decode()) 
            # Se revisa si la respuesta cumple el patrón de término
            if ans_dict["FIN"] == 1 and ans_dict["ACK"]==1 and ans_dict["SEQ"] == self.seq + 1:
                print("Recieved terminating answer!")
                self.seq += 2
                tcp_dict["SEQ"] = self.seq
                tcp_dict["ACK"] = 1
                tcp_dict["FIN"] = 0
                # Se responde con el segundo mensaje de finalización
                self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
                break
        # Se marca como en espera de una conexion, que no tiene una conexión establecida y se cierra el socket
        self.starting_transaction = True
        self.established_conection = False
        self.socket_udp.close()








