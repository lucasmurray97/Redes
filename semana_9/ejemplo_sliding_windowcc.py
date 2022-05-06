import slidingWindowCC as swcc
window_size = 3
initial_seq = 3
message = "Esta es una prueba de sliding window"
message_length = len(message.encode())

# mensaje "Esta es una prueba de sliding window." separado en grupos de 4 caracteres.
data_list = [message_length, "Esta", " es ", "una ", "prue", "ba", "e sl", "idin", "g wi", "ndow"]

# creamos un objeto SlidingWindow
data_window = swcc.SlidingWindowCC(window_size, data_list, initial_seq)

# Podemos imprimir la ventana inicial
print(data_window)
data_window.move_window(1)
print(data_window)
data_window.move_window(1)
print(data_window)
data_window.move_window(1)
print(data_window)
data_window.move_window(1)
print(data_window)
data_window.move_window(1)
print(data_window)
data_window.move_window(1)
print(data_window)
data_window.move_window(1)
print(data_window)
data_window.move_window(1)
print(data_window)
data_window.update_window_size(5)
print(data_window)