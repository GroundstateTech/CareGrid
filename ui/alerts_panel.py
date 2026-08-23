import tkinter as tk
from tkinter import ttk
class AlertsPanel:
    def __init__(self,app):self.app=app;self.tree=None
    def build(self,parent):
        bar=ttk.Frame(parent);bar.pack(fill=tk.X,padx=6,pady=6);ttk.Button(bar,text='Acknowledge All',command=self.app.ack_all).pack(side=tk.LEFT);ttk.Button(bar,text='Silence 2 min',command=lambda:self.app.silence(120)).pack(side=tk.LEFT,padx=4);ttk.Button(bar,text='Silence 5 min',command=lambda:self.app.silence(300)).pack(side=tk.LEFT,padx=4);self.tree=ttk.Treeview(parent,columns=('time','patient','summary','ack'),show='headings',height=10)
        for c,w in [('time',155),('patient',100),('summary',430),('ack',70)]:self.tree.heading(c,text=c.title());self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill=tk.BOTH,expand=True,padx=6,pady=(0,6));return self.tree
    def refresh(self):
        if not self.tree:return
        self.tree.delete(*self.tree.get_children())
        for a in reversed(self.app.alert_mgr.history()[-100:]):self.tree.insert('',tk.END,values=(a.get('time',''),a.get('patient',''),a.get('summary',''),'Yes' if a.get('acknowledged') else 'No'))
