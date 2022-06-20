import time

class Timer:
    """Clase que funciona como timer para BGP"""
    def __init__(self, timeout):
        self.start_time = 0 # Tiempo en que se inicio el timer
        self.current_time = 0 # Tiempo actual del timer
        self.started = False # Booleano que indica si ya se inicio el timer
        self.stoped = False # Booleano que indica si ya se detuvo ese timer
        self.timed_out = False # Booleano que indica si ya hizo timeout ese timer
        self.timeout = timeout # Timeout del timer

    def start(self):
        """Se inicia el start_time y current_time y se marca como started el timer"""
        self.start_time = time.time()
        self.current_time = self.start_time
        self.started = True
        self.stoped = False

    def peek_timer(self):
        """Función que revisa el estado del timer"""
        print("Peeking at timer")
        # Si el timer ya fue iniciado y no se detuvo
        if self.started and not self.stoped:
            # Se actualiza el current_time
            self.current_time = time.time()
            print(f"Delta: {self.current_time - self.start_time}")
            # Se revisa si hizo timeout el timer
            if self.current_time - self.start_time > self.timeout:
                # Si hizo timeout, se marca
                self.timed_out = True
                self.started = False
                self.stoped = True

    def restart_timer(self):
        """Función que reinicia el timer"""
        print("Restarting timer")
        # Si el timer ya fue iniciado, se revisa el delta
        if self.started:
            print(f"Delta: {self.current_time - self.start_time}")
        # Se inicia el timer
        self.start()