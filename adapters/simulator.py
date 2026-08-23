import json,random,threading,time
class SimulatorAdapter:
    def __init__(self,on_record,interval=1.0):self.on_record=on_record;self.interval=interval;self.running=False
    def start(self):
        if self.running:return
        self.running=True;threading.Thread(target=self._run,daemon=True).start()
    def stop(self):self.running=False
    def _run(self):
        patients=['ICU-01','ICU-02','ICU-03','ICU-04','ICU-05','ICU-06']
        while self.running:
            for i,pid in enumerate(patients):
                if not self.running:break
                critical=pid=='ICU-03' and random.random()<0.22
                rec={'patient_id':pid,'device_type':'Simulator','device_id':f'MON-{i+1:02d}','hr':random.randint(68,105) if not critical else random.randint(155,175),'spo2':random.randint(94,100) if not critical else random.randint(82,87),'bp_sys':random.randint(105,145),'bp_dia':random.randint(60,90),'rr':random.randint(12,23),'temp':round(random.uniform(36.4,37.6),1),'source_type':'simulator','source_name':'CareGrid Demo','event':'Simulated telemetry'};rec['context']=json.dumps(rec);self.on_record(rec)
            time.sleep(self.interval)
