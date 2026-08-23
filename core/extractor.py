import json
import re

class VitalsExtractor:
    RX={'patient_id':re.compile(r"\b(?:pid|patient_id|patient|pat|pt)[:=\s]+([A-Za-z0-9_-]+)\b",re.I),'device_id':re.compile(r"\b(?:device_id|device|bed|channel)[:=\s]+([A-Za-z0-9_.:-]+)\b",re.I),'device_type':re.compile(r"\b(ventilator|dialysis|infusion|pump|monitor|ekg|ecg|pulse\s*ox(?:imeter)?|spo2|telemetry)\b",re.I),'hr':re.compile(r"\b(?:HR|heart\s*rate)[:=\s]+(\d{2,3})\b",re.I),'spo2':re.compile(r"\b(?:SpO2|O2|sat(?:uration)?)[:=\s]+(\d{2,3})%?\b",re.I),'bp':re.compile(r"\b(\d{2,3})\s*/\s*(\d{2,3})\b"),'rr':re.compile(r"\b(?:RR|resp(?:iration|iratory)?\s*rate)[:=\s]+(\d{1,2})\b",re.I),'temp':re.compile(r"\b(?:Temp(?:erature)?)[:=\s]+(\d{2}(?:\.\d+)?)\b",re.I),'flow':re.compile(r"\b(?:flow|rate)[:=\s]+(\d{1,4}(?:\.\d+)?)\b",re.I)}
    def from_context(self,context):
        out={k:'' for k in ('patient_id','device_type','device_id','hr','spo2','bp_sys','bp_dia','rr','temp','flow')}
        if not context:return out
        try:obj=json.loads(context)
        except Exception:obj=None
        if isinstance(obj,dict):
            def pick(*names):
                for n in names:
                    if n in obj and obj[n] not in (None,''):return str(obj[n])
                return ''
            out['patient_id']=pick('patient_id','patient','pid','pt');out['device_id']=pick('device_id','device','bed','channel');out['device_type']=pick('device_type','type','monitor');out['hr']=pick('hr','HR','heart_rate');out['spo2']=pick('spo2','SpO2','o2','oxygen','sat');out['bp_sys']=pick('bp_sys','systolic');out['bp_dia']=pick('bp_dia','diastolic');bp=pick('bp')
            if bp and '/' in bp:
                try:out['bp_sys'],out['bp_dia']=bp.split('/',1)
                except Exception:pass
            out['rr']=pick('rr','RR','resp_rate');out['temp']=pick('temp','temperature');out['flow']=pick('flow','rate')
        text=str(context)
        for key in ('patient_id','device_id','device_type','hr','spo2','rr','temp','flow'):
            if not out[key]:
                m=self.RX[key].search(text)
                if m:out[key]=m.group(1).title() if key=='device_type' else m.group(1)
        if not out['bp_sys'] or not out['bp_dia']:
            m=self.RX['bp'].search(text)
            if m:out['bp_sys'],out['bp_dia']=m.group(1),m.group(2)
        return out
