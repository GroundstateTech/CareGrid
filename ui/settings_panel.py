import tkinter as tk
from tkinter import ttk,filedialog,messagebox
class SettingsWindow:
    def __init__(self,app):self.app=app;self.win=None
    def show(self):
        if self.win and self.win.winfo_exists():self.win.lift();return
        self.win=tk.Toplevel(self.app);self.win.title('CareGrid — Settings');self.win.geometry('720x700');canvas=tk.Canvas(self.win);scroll=ttk.Scrollbar(self.win,orient='vertical',command=canvas.yview);body=ttk.Frame(canvas);body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')));canvas.create_window((0,0),window=body,anchor='nw');canvas.configure(yscrollcommand=scroll.set);canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=True);scroll.pack(side=tk.RIGHT,fill=tk.Y);self.vars={};s=self.app.settings
        sec=ttk.LabelFrame(body,text='Alert Thresholds');sec.pack(fill=tk.X,padx=10,pady=8)
        for i,(key,defs) in enumerate(self.app.default_thresholds.items()):
            current=s.get('thresholds',{}).get(key,defs);low=tk.StringVar(value=current.get('low',''));high=tk.StringVar(value=current.get('high',''));self.vars[key]=(low,high);ttk.Label(sec,text=key.upper(),width=10).grid(row=i,column=0,padx=5,pady=3);ttk.Label(sec,text='Low').grid(row=i,column=1);ttk.Entry(sec,textvariable=low,width=8).grid(row=i,column=2);ttk.Label(sec,text='High').grid(row=i,column=3);ttk.Entry(sec,textvariable=high,width=8).grid(row=i,column=4)
        conn=ttk.LabelFrame(body,text='Connectivity');conn.pack(fill=tk.X,padx=10,pady=8);fields=[('serial_port','Serial port','COM3'),('serial_baud','Serial baud','9600'),('mqtt_host','MQTT host','localhost'),('mqtt_port','MQTT port','1883'),('mqtt_topic','MQTT topic','caregrid/+/+/vitals'),('hl7_port','HL7 port','2575'),('syslog_port','Syslog port','5514')];self.cfg={}
        for i,(key,label,default) in enumerate(fields):v=tk.StringVar(value=s.get(key,default));self.cfg[key]=v;ttk.Label(conn,text=label,width=18).grid(row=i,column=0,sticky='w',padx=5,pady=3);ttk.Entry(conn,textvariable=v,width=40).grid(row=i,column=1,sticky='w')
        run=ttk.LabelFrame(body,text='Runtime');run.pack(fill=tk.X,padx=10,pady=8);self.watch=tk.StringVar(value=s.get('watch_folder',''));self.poll=tk.StringVar(value=s.get('poll_interval',1.0));self.snap=tk.StringVar(value=s.get('snapshot_every_min',15));self.webhook=tk.StringVar(value=s.get('webhook',''));ttk.Label(run,text='Watch folder').grid(row=0,column=0,sticky='w',padx=5);ttk.Entry(run,textvariable=self.watch,width=45).grid(row=0,column=1);ttk.Button(run,text='Browse',command=self.browse).grid(row=0,column=2);ttk.Label(run,text='Polling seconds').grid(row=1,column=0,sticky='w',padx=5);ttk.Entry(run,textvariable=self.poll,width=10).grid(row=1,column=1,sticky='w');ttk.Label(run,text='Snapshot minutes').grid(row=2,column=0,sticky='w',padx=5);ttk.Entry(run,textvariable=self.snap,width=10).grid(row=2,column=1,sticky='w');ttk.Label(run,text='Webhook').grid(row=3,column=0,sticky='w',padx=5);ttk.Entry(run,textvariable=self.webhook,width=45).grid(row=3,column=1);ttk.Button(body,text='Save & Apply',command=self.save).pack(anchor='w',padx=10,pady=12)
    def browse(self):
        p=filedialog.askdirectory()
        if p:self.watch.set(p)
    def save(self):
        try:
            th={}
            for key,(lo,hi) in self.vars.items():
                th[key]={}
                if lo.get().strip()!='':th[key]['low']=float(lo.get())
                if hi.get().strip()!='':th[key]['high']=float(hi.get())
                if key=='spo2':th[key]['warn_low']=92
            self.app.apply_settings({'thresholds':th,'watch_folder':self.watch.get(),'poll_interval':float(self.poll.get()),'snapshot_every_min':int(float(self.snap.get())),'webhook':self.webhook.get(),**{k:v.get() for k,v in self.cfg.items()}});messagebox.showinfo('CareGrid','Settings saved.')
        except Exception as e:messagebox.showerror('Settings',str(e))
