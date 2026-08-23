import json
try:
    import paho.mqtt.client as mqtt
except Exception:
    mqtt=None
class MQTTAdapter:
    def __init__(self,on_record,host='localhost',port=1883,topic='caregrid/+/+/vitals'):
        self.on_record=on_record;self.host=host;self.port=int(port);self.topic=topic;self.client=None;self.running=False;self.last_error=''
    def start(self):
        if self.running:return
        if not mqtt:raise RuntimeError('paho-mqtt is not installed')
        try:
            try:self.client=mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
            except Exception:self.client=mqtt.Client()
            self.client.on_connect=self._on_connect;self.client.on_message=self._on_message;self.client.connect(self.host,self.port,60);self.client.loop_start();self.running=True
        except Exception as e:self.last_error=str(e);self.running=False;raise
    def stop(self):
        self.running=False
        try:
            if self.client:self.client.loop_stop();self.client.disconnect()
        except Exception:pass
    def _on_connect(self,client,userdata,flags,rc,*args):
        if rc==0:client.subscribe(self.topic)
        else:self.last_error=f'MQTT connect code {rc}'
    def _on_message(self,client,userdata,msg):
        text=msg.payload.decode('utf-8',errors='ignore')
        try:payload=json.loads(text)
        except Exception:payload={'context':text}
        if not isinstance(payload,dict):payload={'context':text}
        payload.setdefault('source_type','mqtt');payload.setdefault('source_name',msg.topic);payload.setdefault('event','MQTT message')
        if 'context' not in payload:payload['context']=json.dumps(payload,default=str)
        self.on_record(payload)
