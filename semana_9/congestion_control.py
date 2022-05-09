class CongestionControl:
    def __init__(self, MSS):
        # Cantidad max de datos a enviar dentro de un segmento
        self.MSS = MSS
        # Estado del envío
        self.current_state = "slow_start"
        # Cantidad maxima de segmento a enviar
        self.cwnd = self.MSS
        # Slow start threshold, define cuando pasar a congestion_avoidance
        self.ssthresh = None

    def event_ack_recieved(self):
        # Si el estado es slow start
        if self.current_state == "slow_start":
            # Incrementamos cwnd en un MSS
            self.cwnd += self.MSS
            # Revisamos si pasamos a congestion_avoidance
            self.check_state()
        # Si estamos en congestion avoidance
        elif self.current_state == "congestion_avoidance":
            print(f"Cwnd going to be increased in {self.MSS/self.cwnd}")
            # Incrementamos cwnd en MSS/cwnd
            self.cwnd+=self.MSS/self.cwnd
            # Revisamos si pasamos a slow_start
            self.check_state()
            
    
    def check_state(self):
        # Si estamos en slow_start
        if self.current_state == "slow_start":
            if self.ssthresh == None:
                pass
            # Si cwnd es mayot a ssthresh, pasamos a congestion_avoidance
            elif self.cwnd >= self.ssthresh:
                self.current_state = "congestion_avoidance"
    

    def event_timeout(self):
        # Si estamos en slow_start
        if self.current_state == "slow_start":
            # Fijamos ssthresh = cwnd/2
            self.ssthresh = self.cwnd/2
            # Fijamos cwnd = MSS
            self.cwnd = self.MSS
            # Pasamos a congestion_avoidance
            self.current_state = "congestion_avoidance"
        # Si estamos en congestion_avoidance
        elif self.current_state == "congestion_avoidance":
            # Fijamo ssthresh en cwnd/2
            self.ssthresh = self.cwnd/2
            # Fijamos cwnd = MSS
            self.cwnd = self.MSS
            # Pasamos a slow_start
            self.current_state = "slow_start"
    
    def get_cwnd(self):
        # Retorna cwnd
        return self.cwnd