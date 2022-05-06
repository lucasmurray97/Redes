class CongestionControl:
    def __init__(self, MSS):
        self.MSS = MSS
        self.current_state = "slow_start"
        self.cwnd = self.MSS
        self.ssthresh = None

    def event_ack_recieved(self):
        if self.current_state == "slow_start":
            self.cwnd += self.MSS
            self.check_state()
        elif self.current_state == "congestion_avoidance":
            print(f"Cwnd going to be increased in {self.MSS/self.cwnd}")
            self.cwnd+=self.MSS/self.cwnd
            self.check_state()
            
    
    def check_state(self):
        if self.current_state == "slow_start":
            if self.ssthresh == None:
                pass
            elif self.cwnd >= self.ssthresh:
                self.current_state = "congestion_avoidance"
    

    def event_timeout(self):
        if self.current_state == "slow_start":
            self.ssthresh = self.cwnd/2
            self.cwnd = self.MSS
            self.current_state = "congestion_avoidance"
        elif self.current_state == "congestion_avoidance":
            self.ssthresh = self.cwnd/2
            self.cwnd = self.MSS
            self.current_state = "slow_start"
    
    def get_cwnd(self):
        return self.cwnd