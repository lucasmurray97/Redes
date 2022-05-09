# -*- coding: utf-8 -*-
from audioop import add
from shutil import move
import socket
from random import randrange
import sys
import slidingWindowCC as swcc
import timerList as tm
import congestion_control as cc
class socketTCP:
    def __init__(self, orig_address, port, dest_address = None):
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.address = (orig_address, port)
        self.dest_adr = dest_address
        self.seq = FileNotFoundError
        self.data_to_recieve = 0
        self.init_seq = None
        self.starting_transaction = True
        self.established_conection = False
        self.buff_size = None
        self.message_recieved = None
        self.recv_window = None
        self.window_size = None
        self.message_length = None
    def bind(self):
        self.socket_udp.bind((self.address))
    def connect(self, address):
        if self.established_conection:
            raise NameError("You already established a connection!")
        self.dest_adr = address
        print(f"Original destiny address: {self.dest_adr}")
        dict_tcp = {}
        dict_tcp["SYN"] = 1
        dict_tcp["ACK"] = 0
        dict_tcp["FIN"] = 0
        dict_tcp["SEQ"] = randrange(101)
        self.seq = dict_tcp["SEQ"]
        print(f"Initial sequence: {self.seq}")
        message = self.dict_to_tcp(dict_tcp)
        message = message.encode()
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
        if dict_tcp["SYN"] == 1 and dict_tcp["ACK"] == 1 and dict_tcp["SEQ"] == self.seq + 1:
            dict_tcp["SYN"] = 0
            dict_tcp["ACK"] = 1
            dict_tcp["FIN"] = 0
            dict_tcp["SEQ"] += 1
            self.seq+=1
            message =  self.dict_to_tcp(dict_tcp)
            self.socket_udp.sendto(message.encode(), addres)
            self.seq = dict_tcp["SEQ"]
            self.established_conection = True
            self.dest_adr = addres
            print(f"New destiny address: {self.dest_adr}")
            print(f"Secuencia del socket: {self.seq}")
            print("Three-way handshake was succesfull")
        else:
            raise NameError("Three-way handshake wasn't succesfull")
    def accept(self):
        if self.established_conection:
            raise NameError("You already established a connection!")
        new_port = self.address[1]+1
        new_socketTCP = socketTCP(self.address[0], new_port)
        new_socketTCP.bind()
        while True:
            try:
                buffer, address = self.socket_udp.recvfrom(64)
                break
            except socket.timeout as e:
                print("No se recibió el primer mensaje del handshake, intentamos denuevo...")
        tcp_dict = self.tcp_to_dict(buffer.decode())
        if tcp_dict["SYN"] == 0:
            raise NameError("Message wasn't for sync")
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
        if tcp_dict["ACK"] == 1 and tcp_dict["SEQ"] == self.seq +1:
            self.seq += 1
            new_socketTCP.dest_adr = address
            new_socketTCP.seq = self.seq
            new_socketTCP.established_conection = True
            print(f"Secuencia del socket: {new_socketTCP.seq}")
            print("Three-way handshake was succesfull")
            return new_socketTCP, new_socketTCP.address
        else:
            raise NameError("Three-way handshake wasn't succesfull")

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
            tcp_message += "|||" + str(tcp_dict["DATOS"])
        except:
            pass
        return tcp_message
    def settimeout(self, timeout_in_seconds):
        self.socket_udp.settimeout(timeout_in_seconds)
    def chop_message(self, message, size = 64):
        mes_len = len(message)
        # Largo en bytes del mensaje:
        message_length = len(message.encode())
        chunks, chunk_size = mes_len//size +1, size

        # Armamos un arreglo con los pedazos del mensaje
        chunked_list = [message_length]
        for i in range(chunks):
            if (i+1)*chunk_size<mes_len:
                chunked_list.append(message[i*chunk_size:(i+1)*chunk_size])
            else:
                chunked_list.append(message[i*chunk_size:mes_len])
        return chunked_list
    def send(self, message, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(message)
        elif mode == "go_back_n":
            self.send_using_go_back_n(message)
        elif mode == "selective_repeat":
            return self.send_using_selective_repeat(message)
    def recv(self, buff_size, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)
        elif mode == "selective_repeat":
            return self.recv_using_selective_repeat(buff_size)
#######################################################################################################################################################
    def set_window_size(self, window_size):
        self.window_size = window_size
########################################### GO BACK N ##################################################################################################
    def send_using_go_back_n(self, message):
        self.init_seq = self.seq
        # Cortamos el mensaje en segmentos de tamaño MSS = 8
        data_list = self.chop_message(message, 8)
        # Creamos un objeto CongestionControl, con MSS=8
        congestion_control = cc.CongestionControl(8)
        print(f"Window size: {congestion_control.get_cwnd()}")
        # Creamos una ventana que inicia con tamaño cwnd
        data_window = swcc.SlidingWindowCC(congestion_control.get_cwnd(), data_list, self.seq)
        last_ack_received = self.seq - 1 # Debe estar entre Y+0 y Y+5
        step = self.window_size
        timeout = 5
        finished = False
        partially_finished = False
        timer_list = tm.TimerList(timeout, 1)
        # para poder usar este timer vamos poner nuestro socket como no bloqueante
        self.socket_udp.setblocking(False)
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
        # Enviamos la ventana inicial
        (partially_finished, last_seq) = self.send_partial_window_go_back_n(data_window, data_window.window_size, 0, self.init_seq, timer_list)
        while finished == False:
            try:
                # en cada iteración vemos si nuestro timer hizo timeout
                timeouts = timer_list.get_timed_out_timers()
                # si hizo timeout reenviamos el último segmento
                if len(timeouts) > 0:
                    print("Hubo un timeout, reenviamos toda la ventana")
                    # Informamos a congestion_control que hubo un timeout
                    congestion_control.event_timeout()
                    # Actualizamos el tamaño de la ventana en congestion_control.get_cwnd()
                    data_window.update_window_size(int(congestion_control.get_cwnd()))
                    print(f"Window size: {congestion_control.get_cwnd()}")
                    (partially_finished, last_seq) = self.resend_window_go_back_n(data_window, data_window.window_size, self.init_seq, timer_list)
                    # Si llegamos al final del mensaje, revisamos si llegó el ack del ultimo segmento
                    if partially_finished:
                        if last_ack_received == last_seq:
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
                print(f"recibimos el ack de: {seq}")
                if tcp_dict_["ACK"]:
                    # detenemos el timer
                    if not partially_finished:
                        timer_list.stop_timer(0)
                    # Informamos que recibimos un ack
                    congestion_control.event_ack_recieved()
                    print(congestion_control.get_cwnd())
                    # Guardamos el tamaño de la ventana
                    old_size = data_window.window_size
                    # Actualizamos el tamaño de la ventana según congestion_control.get_cwnd())
                    data_window.update_window_size(int(congestion_control.get_cwnd()))
                    # Calculamos la diferencia de tamaño entre las ventanas
                    delta = data_window.window_size - old_size
                    print(f"Window size: {congestion_control.get_cwnd()}")
                    # Calculamos cuanto hay que avanzar la ventana
                    if last_ack_received > seq:
                        step = 0
                        for i in range(data_window.window_size):
                            if data_window.get_sequence_number(i) > last_ack_received:
                                break
                            step += 1 
                    else:
                        step = 0
                        for i in range(data_window.window_size):
                            if data_window.get_sequence_number(i) == None or data_window.get_sequence_number(i) > seq:
                                break
                            step += 1
                        step -= 1
                    print(f"last ack recieved: {last_ack_received}, seq recieved: {seq}")
                    print(f"Step: {step}")
                    last_ack_received = tcp_dict_["SEQ"]
                    # Si es que llegamos al final del mensaje, revisamos si recibimos el ultimo ack del ultimo segmento
                    if partially_finished:
                        # De ser así, marcamos que terminó el envío
                        if last_ack_received == last_seq:
                            print("We recieved the last ack")
                            finished = True
                            continue 
                        # Sino, movemos la ventana y continuamos el envío
                        else: 
                            data_window.move_window(step)
                            continue
                    # Intenamos de mover la ventana
                    data_window.move_window(step)
                    # Consideramos la diferencia entre el tamaño de las ventanas al generarse una actualización
                    start_pos = data_window.window_size - step - delta
                    # Enviamos la ventana
                    (partially_finished, last_seq) = self.send_partial_window_go_back_n(data_window, data_window.window_size, start_pos, self.init_seq, timer_list)

    def send_partial_window_go_back_n(self, data_window, window_size, start_pos, initial_seq, timer_list):
        """Función que envía una ventana parcialmente, desde la posición start_pos"""
        # Iniciamos el timer de la ventana
        timer_list.start_timer(0)
        for i in range(start_pos, window_size):
            # Si es que llegamos al final del mensaje, marcamos que terminamos parcialmente
            if data_window.get_data(i) == None:
                print("Partially Finished!")
                print(f"We must wait for the last ack: {data_window.get_sequence_number(i-1) + len(data_window.get_data(i-1).decode())}")
                return (True, data_window.get_sequence_number(i-1) + len(data_window.get_data(i-1).decode()))
            # Armamos el mensaje tcp
            tcp_dict = {}
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 0
            tcp_dict["FIN"] = 0
            tcp_dict["DATOS"] = data_window.get_data(i).decode()
            tcp_dict["SEQ"] = data_window.get_sequence_number(i)
            message_tcp = self.dict_to_tcp(tcp_dict)
            # Actualizamos la secuencia del socket
            self.seq += len(tcp_dict["DATOS"])
            print(f"Enviamos: {message_tcp}")
            # Enviamos el segmento
            self.socket_udp.sendto(message_tcp.encode(), self.dest_adr)
            # Si no hemos llegado al final del mensaje no lo marcamos y no retornamos la secuencia final
        return (False, None)
    def resend_window_go_back_n(self, data_window, window_size, initial_seq, timer_list):
        print("Reenviamos la siguiente ventana")
        # Se inicia el timer
        timer_list.start_timer(0)
        # Se itera sobre toda la ventana actual
        for i in range(0, window_size):  
            # Si es que llegamos al final del mensaje, marcamos que terminamos parcialmente 
            if data_window.get_data(i) == None:
                print("Partially Finished!")
                print(f"We must wait for the last ack: {data_window.get_sequence_number(i-1) + len(data_window.get_data(i-1).decode())}")
                return (True, data_window.get_sequence_number(i-1) + len(data_window.get_data(i-1).decode()))
            # Se arma el mensaje
            tcp_dict = {}
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 0
            tcp_dict["FIN"] = 0
            tcp_dict["DATOS"] = data_window.get_data(i).decode()
            tcp_dict["SEQ"] = data_window.get_sequence_number(i)
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
                    # Se envia la respuesta
                    print("Sent terminating sequence!")
                    self.socket_udp.sendto(self.dict_to_tcp(closing_dict).encode(), self.dest_adr)
                    while True:
                        # Nos quedamos esperando una respuesta
                        try:
                            buffer, address = self.socket_udp.recvfrom(128)
                            break
                        except socket.timeout as e:
                            # Si no la logramos recibir, volvemos a enviar el mensaje (hasta 4 veces)
                            if nmr_timeouts == 4:
                                break
                            nmr_timeouts+=1
                            print("No se obtuvo respuesta, intentamos denuevo...")
                    ans_dict = self.tcp_to_dict(buffer.decode())
                    # Se revisa que el mensaje recibido cumple el patron de close, sino volvemos a comenzar.
                    if ans_dict["ACK"] == 1 and ans_dict["SEQ"] == self.seq + 1 or nmr_timeouts == 4:
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
            self.seq = tcp_dict["SEQ"] + len(tcp_dict["DATOS"].encode())
            # Armamos el mensaje tcp
            tcp_dict["SYN"] = 0
            tcp_dict["ACK"] = 1
            tcp_dict["FIN"] = 0
            tcp_dict["SEQ"] = self.seq 
            # Avisamos que recibimos el mensaje
            self.socket_udp.sendto(self.dict_to_tcp(tcp_dict).encode(), self.dest_adr)
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
                tcp_dict_ = self.tcp_to_dict(buffer.decode()) 
                # Si la secuencia del mensaje recibido es menor a la secuencia actual, respondemos con el mensaje original
                seq = tcp_dict_["SEQ"]
                if seq < self.seq:
                    print(f"Mensaje repetido: {seq}, estamos en {self.seq}")
                    continue
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
                    tcp_dict["SEQ"] = self.seq + len(tcp_dict_["DATOS"].encode())
                    # Actualizamos la secuencia del socket:
                    self.seq += len(tcp_dict_["DATOS"].encode())
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
        self.init_seq = self.seq
        data_list = self.chop_message(message)
        data_window = swcc.SlidingWindowCC(self.window_size, data_list, self.seq)
        # Secuencia del ultimo mensaje recibido
        last_ack_received = self.seq - 1 # Debe estar entre Y+0 y Y+5
        step = self.window_size
        timeout = 5
        finished = False
        partially_finished = False
        # Lista de timers, tamaño window_size
        timeout_list = tm.TimerList(timeout, self.window_size)
        print(timeout_list.timer_list)
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
                    if partially_finished:
                        finish = True
                        for i in range(self.window_size):
                            if data_window.get_sequence_number(i) not in recieved_acks and data_window.get_sequence_number(i) != None:
                                print(f"Haven't recieved {data_window.get_sequence_number(i)} acks yet")
                                finish = False
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
                if partially_finished:
                        finish = True
                        for i in range(self.window_size):
                            if data_window.get_sequence_number(i) not in recieved_acks and data_window.get_sequence_number(i) != None:
                                print(f"Haven't recieved {data_window.get_sequence_number(i)} acks yet")
                                finish = False
                        if finish:
                            finished = True
                        continue
                # Enviamos los mensajes pendientes de la ventana que se movió
                (partially_finished, last_seq) = self.send_pending_seg(data_window, self.window_size, self.init_seq, timeout_list, recieved_acks, sent, seq_timer)

    # Envía los segmentos pendientes
    def send_pending_seg(self, data_window, window_size, init_seq, timeout_list, recieved_acks, sent, seq_timer):
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
            print(timeout_list.timer_list)
            for j in range(window_size):
                if timeout_list.timer_list[j] == False:
                    timeout_list.start_timer(j) # Como sabemos que no estaba ocupado?
                    seq_timer[sequence] = j # Asociamos el mensaje a un timer
                    break
            sent.append(sequence) # Agregamos la secuencia a los mensajes enviados
        return (False, None)
    
    # Trata de mover toda la ventana todo lo que se pueda:
    def try_to_move(self, data_window, window_size, recieved_acks, sent):
        step = 0
        for i in range(window_size):
            sequence = data_window.get_sequence_number(i)
            if sequence in recieved_acks:
                step+=1
                recieved_acks.remove(sequence)
            else:
                break
        for i in range(step):
            sequence = data_window.get_sequence_number(i)
            sent.remove(sequence)
        data_window.move_window(step)

    def resend_timed_outs(self, data_window, window_size, timeouts, timeout_list, seq_timer, recieved_acks):
        for i in range(window_size):
            sequence = data_window.get_sequence_number(i)
            # Si ya se recibió el ack de ese segmento o el segmento aun no hace timeout, no se reenvía
            print(seq_timer)
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
        seq = message_dict["SEQ"]
        for i in range(window_size):
            sequence = data_window.get_sequence_number(i)
            if seq == sequence:
                if sequence not in recieved_acks:
                    recieved_acks.append(sequence)
                    print(seq_timer)
                    timeout_list.stop_timer(seq_timer[seq])
                    timeout_list.timer_list[seq_timer[seq]] = False
                    del seq_timer[seq]
        self.try_to_move(data_window, window_size, recieved_acks, sent)
        return recieved_acks

    def recv_using_selective_repeat(self, buff_size):
        # Si tiene una conexion establecida, se levanta un error
        if not self.established_conection:
            raise NameError("You haven't established a connection yet")
        # Creamos la ventana vacía:
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
                    # Se envia la respuesta
                    print("Sent terminating sequence!")
                    self.socket_udp.sendto(self.dict_to_tcp(closing_dict).encode(), self.dest_adr)
                    while True:
                        # Nos quedamos esperando una respuesta
                        try:
                            buffer, address = self.socket_udp.recvfrom(128)
                            break
                        except socket.timeout as e:
                            # Si no la logramos recibir, volvemos a enviar el mensaje (hasta 4 veces)
                            if nmr_timeouts == 4:
                                break
                            nmr_timeouts+=1
                            print("No se obtuvo respuesta, intentamos denuevo...")
                    ans_dict = self.tcp_to_dict(buffer.decode())
                    # Se revisa que el mensaje recibido cumple el patron de close, sino volvemos a comenzar.
                    if ans_dict["ACK"] == 1 and ans_dict["SEQ"] == self.seq + 1 or nmr_timeouts == 4:
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
            empty_list = [None for i in range(self.message_length)]
            self.recv_window = swcc.SlidingWindowCC(self.window_size, empty_list, self.seq)
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
                if self.check_range(self.recv_window, self.window_size, tcp_dict_, self.message_recieved, self.buff_size):
                    print(f"Aceptamos el mensaje con secuencia: {seq}")
                    print(f"Quedan {self.data_to_recieve} por recibir")
                    print(f"El buffer está en: {self.buff_size}")
                    if self.data_to_recieve == 0:
                        print("Finished recieving message")
                        self.starting_transaction = True
                        self.init_seq = None
                        self.message_length = None
                        self.data_to_recieve = 0
                        break
                # Si la secuencia calza, seguimos
                else:
                    print(f"Descartamos el mensaje con secuencia: {seq}")
                    continue           
        return self.message_recieved

    # Revisa si el mensaje pertenece al rango esperado y responde con acks
    def check_range(self, recv_window, window_size, tcp_dict, message_recieved, buff_size):
        seq = tcp_dict["SEQ"]
        message = tcp_dict["DATOS"]
        if seq in self.expected_range(recv_window, window_size):
            self.add_to_window(seq, message, recv_window, window_size)
            self.send_ack(seq)
            self.try_to_move_r(recv_window, window_size, message_recieved, buff_size)
            return True
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
        for i in range(window_size):
            if seq == recv_window.get_sequence_number(i):
                print(f"added message in slot {seq}-{recv_window.get_sequence_number(i)}")
                print(recv_window)
                print(i)
                recv_window.put_data(message, seq, i)

    # Trata de avanzar la ventana lo mas que pueda y agrega los mensajes que quedaron afuera al mensaje total
    def try_to_move_r(self, recv_window, window_size, message_recieved, buff_size):
        step = 0
        for i in range(window_size):
            if recv_window.get_data(i) != None:
                step+=1
                if recv_window.get_data(i) != self.message_length:
                    self.message_recieved+=str(recv_window.get_data(i))
                    self.data_to_recieve-=len(str(recv_window.get_data(i)).encode())
                    self.buff_size-=len(str(recv_window.get_data(i)).encode())
            else:
                break
        print(recv_window)
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
                    # Se envia la respuesta
                    print("Sent terminating sequence!")
                    self.socket_udp.sendto(self.dict_to_tcp(closing_dict).encode(), self.dest_adr)
                    while True:
                        # Nos quedamos esperando una respuesta
                        try:
                            buffer, address = self.socket_udp.recvfrom(128)
                            break
                        except socket.timeout as e:
                            # Si no la logramos recibir, volvemos a enviar el mensaje (hasta 4 veces)
                            if nmr_timeouts == 4:
                                break
                            nmr_timeouts+=1
                            print("No se obtuvo respuesta, intentamos denuevo...")
                    ans_dict = self.tcp_to_dict(buffer.decode())
                    # Se revisa que el mensaje recibido cumple el patron de close, sino volvemos a comenzar.
                    if ans_dict["ACK"] == 1 and ans_dict["SEQ"] == self.seq + 1 or nmr_timeouts == 4:
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








