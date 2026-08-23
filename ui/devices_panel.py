import tkinter as tk
from tkinter import ttk,messagebox
class DevicesPanel:
    def __init__(self,app):self.app=app;self.rows={}
    def build(self,parent):
        root=tk.Frame(parent);root.pack(fill=tk.BOTH,expand=True);ttk.Label(root,text='Connections',font=('Segoe UI',10,'bold')).pack(anchor='w',padx=8,pady=(8,4));lst=tk.Frame(root);lst.pack(fill=tk.X,padx=6)
        for name,label in [('simulator','Demo Simulator'),('serial','Serial / USB'),('mqtt','MQTT'),('hl7','HL7 v2'),('sdc','IEEE 11073 SDC'),('syslog','Syslog UDP')]:
            row=ttk.Frame(lst);row.pack(fill=tk.X,pady=2);ttk.Label(row,text=label,width=18).pack(side=tk.LEFT);status=tk.StringVar(value='Stopped');ttk.Label(row,textvariable=status,width=12).pack(side=tk.LEFT);ttk.Button(row,text='Start / Stop',command=lambda n=name:self.toggle(n)).pack(side=tk.LEFT);self.rows[name]=status
        ttk.Button(root,text='Connection Settings',command=self.app.show_settings).pack(anchor='w',padx=8,pady=8);return root
    def toggle(self,name):
        a=self.app.adapters.get(name)
        if not a:return
        try:a.stop() if getattr(a,'running',False) else a.start()
        except Exception as e:messagebox.showerror('Connection',str(e))
        self.refresh()
    def refresh(self):
        for name,var in self.rows.items():
            a=self.app.adapters.get(name);var.set('Running' if a and getattr(a,'running',False) else ('Error' if a and getattr(a,'last_error','') else 'Stopped'))
