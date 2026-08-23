import json
import os
from threading import Lock

class Settings:
    def __init__(self,path):self.path=path;self._data={};self._lock=Lock()
    def load(self):
        with self._lock:
            try:
                if os.path.exists(self.path):
                    with open(self.path,'r',encoding='utf-8') as f:self._data=json.load(f)
            except Exception:self._data={}
        return self
    def save(self):
        with self._lock:
            os.makedirs(os.path.dirname(self.path) or '.',exist_ok=True);tmp=self.path+'.tmp'
            with open(tmp,'w',encoding='utf-8') as f:json.dump(self._data,f,indent=2)
            os.replace(tmp,self.path)
    def get(self,key,default=None):return self._data.get(key,default)
    def set(self,key,value):self._data[key]=value
    def as_dict(self):return dict(self._data)
