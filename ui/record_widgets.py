import datetime as dt
import tkinter as tk
from tkinter import ttk

SYMPTOMS=['None','Headache','Migraine','Fatigue','Brain Fog','Back Pain','Joint Pain','Congestion','Dizziness','Shortness of Breath','Other']
BODY=['Head','Neck','Chest','Abdomen','Back','Arm','Hand','Hip','Leg','Knee','Foot','Skin','Generalized','Other']
SEVERITY=[str(i) for i in range(11)]
MEALS=['Breakfast','Lunch','Dinner','Snack','Drink','Meal','Other']
SLEEP=['Sleep','Nap','Rest','Interrupted Sleep','Other']
FREQ=['Once','Daily','Twice Daily','Morning','Night','As Needed','Weekly','Other']

class ToolTip:
    def __init__(self,w,text):
        self.w=w;self.text=text;self.tip=None
        w.bind('<Enter>',self.show,add='+');w.bind('<Leave>',self.hide,add='+')
    def show(self,_=None):
        if self.tip or not self.text:return
        self.tip=tk.Toplevel(self.w);self.tip.overrideredirect(True)
        self.tip.geometry(f'+{self.w.winfo_rootx()+16}+{self.w.winfo_rooty()+self.w.winfo_height()+4}')
        tk.Label(self.tip,text=self.text,bg='#fffde7',fg='#222',relief='solid',bd=1,wraplength=320,justify='left',padx=6,pady=4,font=('Segoe UI',9)).pack()
    def hide(self,_=None):
        if self.tip:self.tip.destroy();self.tip=None

def field(parent,row,col,label,var,choices=None,tip='',width=20):
    ttk.Label(parent,text=label).grid(row=row,column=col*2,sticky='w',padx=4,pady=3)
    w=ttk.Combobox(parent,textvariable=var,values=choices,state='readonly',width=width) if choices else ttk.Entry(parent,textvariable=var,width=width)
    w.grid(row=row,column=col*2+1,sticky='ew',padx=4,pady=3)
    if tip:ToolTip(w,tip)
    return w

def today():return dt.date.today().strftime('%Y-%m-%d')
def now():return dt.datetime.now().strftime('%Y-%m-%d %H:%M')

def as_float(v):
    try:return float(v) if str(v).strip() else None
    except:return None
