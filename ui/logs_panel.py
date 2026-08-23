import tkinter as tk
from tkinter import ttk
class LogsPanel:
    def __init__(self,app):self.app=app;self.tree=None
    def build(self,parent):
        cols=('timestamp','patient_id','device_type','event','source_type','severity');self.tree=ttk.Treeview(parent,columns=cols,show='headings',height=12)
        for c,w in [('timestamp',155),('patient_id',100),('device_type',105),('event',260),('source_type',90),('severity',70)]:self.tree.heading(c,text=c.replace('_',' ').title());self.tree.column(c,width=w,anchor='w')
        self.tree.pack(fill=tk.BOTH,expand=True,padx=6,pady=6);return self.tree
    def refresh(self,rows):
        if not self.tree:return
        self.tree.delete(*self.tree.get_children())
        for r in reversed(rows[-500:]):self.tree.insert('',tk.END,values=tuple(r.get(c,'') for c in ('timestamp','patient_id','device_type','event','source_type','severity')))
