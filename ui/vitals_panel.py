import tkinter as tk
from tkinter import ttk
from ui import theme
class VitalsPanel:
    def __init__(self,app):self.app=app;self.tree=None
    def build(self,parent):
        cols=('patient','device','hr','spo2','bp','rr','temp','updated','status');self.tree=ttk.Treeview(parent,columns=cols,show='headings');heads={'patient':'Patient / Bed','device':'Device','hr':'HR','spo2':'SpO₂','bp':'Blood Pressure','rr':'RR','temp':'Temp','updated':'Last Update','status':'Status'};widths={'patient':140,'device':135,'hr':60,'spo2':70,'bp':100,'rr':60,'temp':70,'updated':165,'status':90}
        for c in cols:self.tree.heading(c,text=heads[c]);self.tree.column(c,width=widths[c],anchor='center')
        self.tree.tag_configure('ok',background=theme.OK);self.tree.tag_configure('warn',background=theme.WARN);self.tree.tag_configure('crit',background=theme.CRIT);self.tree.pack(fill=tk.BOTH,expand=True,padx=6,pady=6);self.tree.bind('<Double-1>',lambda e:self.app.open_selected_patient());return self.tree
    def refresh(self):
        if not self.tree:return
        self.tree.delete(*self.tree.get_children());latest=self.app.ds.latest_by_patient();ordered=sorted(latest.items(),key=lambda kv:({'crit':0,'warn':1,'ok':2}.get(self.app.alert_mgr.evaluate_status(kv[1]),3),kv[0]))
        for pid,r in ordered:
            status=self.app.alert_mgr.evaluate_status(r);bp=f"{r.get('bp_sys') or '—'}/{r.get('bp_dia') or '—'}";vals=(pid,r.get('device_id') or r.get('device_type') or '—',r.get('hr') or '—',r.get('spo2') or '—',bp,r.get('rr') or '—',r.get('temp') or '—',r.get('timestamp') or '—',status.upper());self.tree.insert('',tk.END,iid=f'p:{pid}',values=vals,tags=(status,))
