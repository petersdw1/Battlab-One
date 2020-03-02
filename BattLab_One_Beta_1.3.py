import tkinter as tk
from tkinter import ttk
from tkinter import *
import csv
import time
import datetime
import math
import numpy as np
import serial
import matplotlib
from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
from tkinter import colorchooser
import os
import serial.tools.list_ports

from tkinter import messagebox
import pickle
from tkinter import filedialog

matplotlib.use('TkAgg')

#from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure


#################################################################################    
###     SETUP ROOT, FRAMES, & MATPLOTLIB CANVAS
#################################################################################

root = tk.Tk()
root.wm_title('IOTA_Beta_01')
root.resizable(True,True)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

s = ttk.Style() 
s.configure('TLabelframe', background='dark gray')

profile_frame = ttk.Frame(root,style='TLabelframe', width = 1440, height = 960)
#profile_frame = ttk.LabelFrame(root, text = 'IOTA Beta_08',style='TLabelframe', width = 1300, height = 740)
profile_frame.grid(row=0, column=0, padx=2,pady=(2,2),sticky = 'nswe')
#profile_frame.grid_propagate(False)

frame = ttk.Frame(profile_frame, borderwidth=5, relief='sunken', width=990, height=545)
frame.grid(row=3, column=6, rowspan=22,columnspan=20,padx=(10,30),pady=(20,2), sticky='nswe')

w = Canvas(frame, width=990, height=545)
w.config(background='black')
w.grid(row=0,column = 3,padx=2,pady=2,sticky = 'nswe')
#img = PhotoImage(file='BluebirdLogo.png')      
#w.create_image(10,5, anchor = NW, image=img)

print(plt.style.available)
plt.style.use('fast')
f = plt.figure(figsize=(9.5, 4.5), dpi=100,clear=True)

ax = f.add_subplot(111)

#################################################################################
###   SETUP GLOBAL VARIABLES
#################################################################################
sense_low = 0.204
sense_hi = 100.4

sense_resistor=tk.DoubleVar()
sense_resistor.set(sense_low)

LSB=0.0025

i_offset = 1

global si,x,y, avg_active_event_I

si = []
x = []
y = []
reading = StringVar()
data = StringVar()

baud_rate = 115200

ports=list(serial.tools.list_ports.comports())
for name in ports:
   print('{:10.5}'.format(str(name)))
   
#com_port = ('{:10.5}'.format(str(name)))
com_port= 'COM4'
i=tk.IntVar()
i.set(0)

#################################################################################
###    SETUP MENU FUNCTIONS
#################################################################################
def PrintFile():
    print ('Print File!')
    os.startfile('IOTA_ALPHA_0.7.py', 'print')
    
def NewFile():
    print ('New File!')
    
def OpenFile():
    name = filedialog.askopenfilename(initialdir = 'C:/Users/dwpete3/Desktop',title = 'Select file',
                                filetypes = (('Iota files','*.iot'),('all files','*.*')))
    file = open(name,'rb')
    object_file = pickle.load(file)
    file.close()
    output=object_file.get_values()
    print(output)
    print (name)

def SaveFile():
    root.filename =  filedialog.asksaveasfilename(initialdir = 'C:/Users/dwpete3/Desktop',title = 'Select file',
                                filetypes = (('Iota files','*.iot'),('all files','*.*')))

    current_profile = Profile('Profile'+ '-'+ str(datetime.datetime.now()),battery_capactity_entry_1.get(),battery_chem.get(),batt_cells.get(),voltage.get(),rt_dur.get(),
                                  ae_captured_average_current_2,max_current, min_current, samples, samples_per_sec)

    filehandler = open(root.filename+'.iot','wb')
    pickle.dump(current_profile,filehandler)
    filehandler.close()

    print (root.filename)
    
def Background():
    print ('This is a simple example of a background color')
    rgb_color,web_color = colorchooser.askcolor(parent=frame,initialcolor=(255, 0, 0))   
    w.config(background=web_color)
    print(rgb_color,web_color)

def Linecolor():
    print ('This is a simple example of a line color')
    rgb_color,web_color = colorchooser.askcolor(parent=frame,initialcolor=(255, 0, 0))   
    w.create_line(50, 100, 250, 200, fill=web_color, width=10)

def Linewidth():
    print ('This is a simple example of a line width')
    s_BX = Spinbox(filemenu,from_=0, to=10)
    s_BX.grid(row=0, column =0)
    w.create_line(50, 100, 250, 200, fill='white', width=s_BX.get())

def SetCommport():
    print (com_port)

def SetBaudrate(br):
    brr=br
    print (brr)

def About():
    print ('This is BBLabs first Product')
    
   
#################################################################################
###   SETUP MENU SYSTEM
#################################################################################
menu = Menu(root)

root.config(menu=menu)

filemenu = Menu(menu)
menu.add_cascade(label='File', menu=filemenu)
filemenu.add_command(label='Print', command=PrintFile)
filemenu.add_command(label='New', command=NewFile)
filemenu.add_command(label='Open...', command=OpenFile)
filemenu.add_command(label='Save...', command=SaveFile)
filemenu.add_separator()
filemenu.add_command(label='Exit', command=root.quit)

optionsmenu = Menu(menu)
menu.add_cascade(label='Options', menu=optionsmenu)
optionsmenu.add_command(label='Choose Background Color...', command=Background)
optionsmenu.add_command(label='Choose Line Color...', command=Linecolor)
optionsmenu.add_command(label='Choose Line Width...', command=Linewidth)

commsmenu = Menu(menu)
menu.add_cascade(label='Connect', menu=commsmenu)

cp_submenu = Menu(menu) # create a new menu
commsmenu.add_cascade(label='Choose COM Port ...',menu=cp_submenu) # attach it to a parent menu
cp_submenu.add_command(label='COM1', command=SetCommport)
cp_submenu.add_command(label='COM2', command=SetCommport)

br_submenu = Menu(menu) # create a new menu
commsmenu.add_cascade(label='Choose BAUD Rate ...',menu=br_submenu) # attach it to a parent menu
br_submenu.add_command(label='9600', command=SetBaudrate)
br_submenu.add_command(label='115200', command=SetBaudrate)

helpmenu = Menu(menu)
menu.add_cascade(label='Help', menu=helpmenu)
helpmenu.add_command(label='About...', command=About)

filemenu.entryconfigure(4, state=tk.DISABLED)


#################################################################################
###     DEFINE PROFILE CLASS
#################################################################################
class Profile(object):
    '''A Profile has the following properties:
    Attributes:
        name: A string representing the customer's name.
        bat_cap: battery capacity, An int tracking the battery capacity.
        bat_chem: battery chemistry, A string representing the battery chemistry.
        n_cells: number of cells: An int representing the number of cells.
        voltage: A float representing the PSU voltage set.
        duration: A float (or int?) representing the amount of time for data capture.
        avg_curr: Average Current:  float  
        max_curr:Max current: float
        min_curr: Min current:float
        samples: Samples: int
        samp_psec: Samples per second:int '''

    def __init__(self, name, bat_cap, bat_chem, n_cells, voltage, duration, avg_curr, max_curr,
                 min_curr, samples, samp_psec ):
        '''Set Profile attributes'''
        self.name = name
        self.bat_cap = bat_cap
        self.bat_chem = bat_chem
        self.n_cells = n_cells
        self.voltage = voltage
        self.duration = duration
        self.avg_curr = avg_curr
        self.max_curr = max_curr
        self.min_curr = min_curr
        self.samples = samples
        self.samp_psec = samp_psec

    def set_values(self, name, bat_cap, bat_chem, n_cells, voltage, duration, avg_curr,
                   max_curr, min_curr, samples, samp_psec):
        '''Return the balance remaining after withdrawing *amount*
        dollars.'''
        self.name = name
        self.bat_cap = bat_cap
        self.bat_chem = bat_chem
        self.n_cells = n_cells
        self.voltage = voltage
        self.duration = duration
        self.avg_curr = avg_curr
        self.max_curr = max_curr
        self.min_curr = min_curr
        self.samples = samples
        self.samp_psec = samp_psec

    def get_values(self):
        '''Return all values'''
        return self.name, self.bat_cap, self.bat_chem, self.n_cells, self.voltage, self.duration, self.avg_curr,\
               self.max_curr, self.min_curr, self.samples, self.samp_psec


class state(object):
    
    number_of_states=0

    def __init__(self, state_id, state_name, state_start, state_stop, state_duration,
                state_current, min_current, max_current):
        """Set Profile attributes"""
        self.id = state_id
        self.name = state_name
        self.start = state_start
        self.stop = state_stop
        self.duration = state_duration
        self.current = state_current
        self.min_current = min_current
        self.min_current = max_current

        state.number_of_states +=1

    def set_values(self, state_id, state_name, state_start, state_stop, state_duration,
                state_current, min_current, max_current):
        """Return the balance remaining after withdrawing *amount*
        dollars."""
        self.id = state_id
        self.name = state_name
        self.start = state_start
        self.stop = state_stop
        self.duration = state_duration
        self.current = state_current
        self.min_current = min_current
        self.min_current = max_current

    def get_values(self):
        """Return all values"""
        return self.id, self.name, self.start, self.stop,self.duration, self.current, self.min_current, self.min_current

   
#################################################################################
####     STEP1 SET BATTERY PARAMETERS AND PSU OUTPUT
#################################################################################

def set_battery_voltage():
    ser = serial.Serial(com_port, baud_rate, timeout = None)

    #Set sense resistor to low
    sense_resistor.set(sense_low)
    cmd = 'l'
    bytes_returned = ser.write(cmd.encode())
    print(bytes_returned)
    print(sense_resistor.get())
    
    if int(p_radio.get()) == 1:
        p_rad.config(foreground='green')
        p_rad1.config(foreground='black')

        if voltage.get()== '1.2':
           volts = 1.2   
           cmd = 'a'
           bytes_returned = ser.write(cmd.encode())
           print(bytes_returned)
        elif voltage.get()== '1.5':
           volts = 1.5   
           cmd = 'b'
           bytes_returned = ser.write(cmd.encode())
           print(bytes_returned)
        elif voltage.get()== '2.4':
           volts = 2.4   
           cmd = 'c'
           bytes_returned = ser.write(cmd.encode())
           print(bytes_returned)
        elif voltage.get()== '3.0':
           volts = 3.0   
           cmd = 'd'
           bytes_returned = ser.write(cmd.encode())
           print(bytes_returned)
        elif voltage.get()== '3.7':
           volts = 3.7
           cmd = 'e'
           bytes_returned = ser.write(cmd.encode())
           print(bytes_returned)
        elif voltage.get()== '4.2':
           volts = 4.2  
           cmd = 'f'
           bytes_returned = ser.write(cmd.encode())
           print(bytes_returned)
        elif voltage.get()== '4.5':
           volts = 4.5 
           cmd = 'g'
           bytes_returned = ser.write(cmd.encode())
           print(bytes_returned)

        cmd = 'h'
        bytes_returned = ser.write(cmd.encode())
        print(bytes_returned)
        print('Voltage On ' + voltage.get()+' volts')
        print('Radio Button', int(p_radio.get()))

    elif int(p_radio.get()) == 0:
        p_rad.config(foreground='black')
        p_rad1.config(foreground='red')
        cmd = 'i'
        bytes_returned = ser.write(cmd.encode())
        print('Voltage Off')
        print('Radio Button', int(p_radio.get()))
    
    ser.close()
    capture_active_event_button.configure(state=tk.NORMAL)
    trigger_box.config(state=tk.NORMAL)
    batt_cap.configure(state=tk.DISABLED)
    battery_chemistry_combo_box.configure(state=tk.DISABLED)
    battery_cells_combo_box.configure(state=tk.DISABLED)
    psu_combo_box.configure(state=tk.DISABLED)
    
    step1_label.configure(foreground='black')
    step2_label.configure(foreground='blue')
    
def set_voltage(eventObject):
    if (batt_chem.get() == 'ALKALINE' and batt_cells.get() == '1'):
        print(str(batt_chem.get()) + ' ' + str(batt_cells.get()))
        psu_combo_box.current(1)
        voltage.set(1.5)
        print(str(voltage.get()))
    elif(batt_chem.get() == 'ALKALINE' and batt_cells.get() == '2'):
        print(str(batt_chem.get()) + ' ' + str(batt_cells.get()))
        psu_combo_box.current(3)
        voltage.set(3.0)
        print(str(voltage.get()))
    elif(batt_chem.get() == 'ALKALINE' and batt_cells.get() == '3'):
        print(str(batt_chem.get()) + ' ' + str(batt_cells.get()))
        psu_combo_box.current(6)
        voltage.set(4.5)
        print(str(voltage.get()))
    elif(batt_chem.get() == 'LI-ION' and batt_cells.get() == '1'):
        print(str(batt_chem.get()) + ' ' + str(batt_cells.get()))
        psu_combo_box.current(5)
        voltage.set(3.7)
        print(str(voltage.get()))
    elif(batt_chem.get() == 'NiMH/NiCd' and batt_cells.get() == '1'):
        print(str(batt_chem.get()) + ' ' + str(batt_cells.get()))
        psu_combo_box.current(0)
        voltage.set(1.2)
        print(str(voltage.get()))
    elif(batt_chem.get() == 'NiMH/NiCd' and batt_cells.get() == '2'):
        print(str(batt_chem.get()) + ' ' + str(batt_cells.get()))
        psu_combo_box.current(1)
        voltage.set(2.4)
        print(str(voltage.get()))
    elif(batt_chem.get() == 'NiMH/NiCd' and batt_cells.get() == '3'):
        print(str(batt_chem.get()) + ' ' + str(batt_cells.get()))
        psu_combo_box.current(4)
        voltage.set(4.2)
        print(str(voltage.get()))
    else:
        print('ooops')
        messagebox.showerror('Battery Info Error', 'IOTA v1.0 only supports [1-LI-ION cell]')



#################################################################################
###    STEP2 CAPTURE PROFILE
#################################################################################

def capture_profile():
    
    try:
        ser = serial.Serial(com_port, baud_rate, timeout=None)
    except SerialException:
        print('Port is busy')
    
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.send_break(duration=0.25)
    
    counter = 0
    cntr = DoubleVar()
    
    my_file=open('raw_byte_file.txt', mode='w', buffering =(10*1024*1024))
    reading = StringVar()
    t=0
    print(rt_dur.get())
    
    progress_label = ttk.Label(profile_frame, text='',background='dark gray')
    progress_label.grid(row=12, column = 0, padx=(190,4),sticky='w')

    if trig_var.get()==1:
        print('Var 1')
        
        progress_label.config(text = 'Trigger capture...' )
        progress_label.config(foreground = 'red' )

        cmd = 'x'
        bytes_returned = ser.write(cmd.encode())
        time.sleep(5)
        print('Triggerbytes',bytes_returned)
        
        
        while (True):
            if ser.in_waiting > 0:         
                my_file.write(str(t))
                my_file.write(',')
                reading.set(ser.readline(2).hex())
                my_file.write(str(reading.get()))
                
                my_file.write('\n')
                t=t+1
                root.update()
                if str(reading.get()) == '0000':
                    print(str(reading.get()))
                    break 
        progress_label.config(text = 'Complete' )
        progress_label.config(foreground = 'green' )

    else:
        print('Var 0')
        
        pb_vd = ttk.Progressbar(profile_frame, orient='horizontal', mode='determinate',
                                maximum = float(rt_dur.get()),length=80, variable=cntr)
        
        pb_vd.grid(row=12,column = 0,columnspan=1,padx=(105,1),sticky = 'w')
        pb_vd.start()
    
        progress_label.config(text = 'Capturing...' )
        progress_label.config(foreground = 'red' )

        offset=time.clock()
        cmd = 'z'
        bytes_returned = ser.write(cmd.encode())
        print(bytes_returned)
        
        while counter < float(rt_dur.get()): 
            my_file.write(str(t))
            my_file.write(',')
            reading.set(ser.readline(2).hex())
            my_file.write(str(reading.get()))
            my_file.write('\n')

            t=int(time.clock()*1000)
            #t=t+1
            root.update()
        
            counter = time.clock()-offset
            cntr.set(counter)
            profile_frame.update()

        cmd = 'y'
        bytes_returned = ser.write(cmd.encode())
        print(bytes_returned)
        pb_vd.stop()
        pb_vd.destroy()
      
        progress_label.config(text = 'Complete')
        progress_label.config(foreground = 'green')

    my_file.close()
    print('profile completed')
    ser.close()
    
    with open('raw_byte_file.txt', 'r')as csvfile:
        inp = csv.reader(csvfile, delimiter = ',')
        for row in inp:
            x.append(int(row[0]))
            y.append(round((int(row[1],16)*LSB*i_offset)/float(sense_resistor.get()),5))
            #y.append(round(int(row[1],16)*LSB*i_offset,2))
    print('hex data converted to decimal')
        
    rows = zip(x,y)
    
    #Feed this to Matplotlib
    with open('outputfile.txt', 'w') as analysis:
        writer = csv.writer(analysis)
        for row in rows:
            writer.writerow(row)

    analysis.close()
    print('Output saved')

    #PLOT THE DATA
    global canvas,f,ax
   
    #ax = f.add_subplot(111, facecolor='gray')
    ax.set_title('Profile: ' +'Voltage = ' + voltage.get() + ' volts, ' + 'Time = '+ rt_dur.get() + ' seconds')
    
    ax.plot(x, y, color='blue', linewidth=.5)

    ax.grid(b=True, which='major', axis='both',color='black', linestyle='-', linewidth=.1)
    
    cursor = Cursor(ax,color='blue', linewidth=.3)
    
    canvas = FigureCanvasTkAgg(f, master=w)
    canvas.get_tk_widget().grid(row=0,column=6)

    toolbarFrame = ttk.Frame(master=frame)
    toolbarFrame.grid(row=10, column=3, sticky='w' )
    toolbar = NavigationToolbar2Tk(canvas, toolbarFrame)
    #toolbar = NavigationToolbar2TkAgg(canvas, toolbarFrame)
    canvas.draw()

#    with open('raw_byte_file.txt', 'r')as csvfile:
#       inp = csv.reader(csvfile, delimiter = ',')
#       for row in inp:
#          x.append(int(row[0]))
#         y.append(round((int(row[1],16)*LSB*i_offset)/float(sense_resistor.get()),5))
          #y.append(round(int(row[1],16)*LSB*i_offset,2))

    
    print('run completed')
    
    calc_batt_life_btn_4.configure(state=tk.NORMAL)


#Gather data and statistics
    global ae_captured_average_current_2, ae_captured_duration_2, max_current, min_current

    ae_captured_average_current_2 = sum(y)/(len(y))
    ae_captured_duration_2 = max(x)-min(x)

    avg_active_event_I_2.configure(text=str(round(ae_captured_average_current_2,2)))
 
    max_current = max(y)
    min_current = min(y)

# Update Results Step4 data
    ae_current_entry_4.delete(0, END)
    ae_current_entry_4.insert(0,round(ae_captured_average_current_2,2))

    ae_duration_entry_4.delete(0, END)
    ae_duration_entry_4.insert(0,round(ae_captured_duration_2,2))

    batt_cap_entry_4.delete(0,END)
    batt_cap_entry_4.insert(END,batt_cap.get())


    step2_label.configure(foreground='black')
    step3_label.configure(foreground='blue')

#################################################################################
###    STEP3 CAPTURE SLEEP CURRENT
#################################################################################

def capture_sleep_profile():
    
   sleep_reading = StringVar()
   counter1 = 0    
   cntr1 = DoubleVar()
   ser = serial.Serial(com_port, baud_rate, timeout = None)

#Set sense resistor to hi
   sense_resistor.set(sense_hi)
   cmd = 'k'
   bytes_returned = ser.write(cmd.encode())
   print(bytes_returned)
   print(sense_resistor.get())

   progress_label_s = ttk.Label(profile_frame, text='',background='dark gray')
   progress_label_s.grid(row=16, column = 0, padx=(190,4),sticky='w')

   pb_vd_s = ttk.Progressbar(profile_frame, orient='horizontal', mode='determinate',
                                maximum = float(rt_dur.get()),length=60, variable=cntr1)
        
   pb_vd_s.grid(row=16,column = 0,columnspan=1,padx=(105,1),sticky = 'w')
   pb_vd_s.start()
    
   progress_label_s.config(text = 'Capturing...' )
   progress_label_s.config(foreground = 'red' )

   offset1=time.clock()
   cmd = 'z'
   bytes_returned = ser.write(cmd.encode())
   print(bytes_returned)

   while counter1 < 5:
      sleep_reading.set(ser.readline(2).hex())
      si.append(round((int(sleep_reading.get(),16)*LSB*i_offset)/float(sense_resistor.get()),4))
      #y.append(round((int(row[1],16)*LSB*i_offset)/float(sense_resistor.get()),5))
      root.update()
      counter1 = time.clock()-offset1
      cntr1.set(counter1)
      profile_frame.update()
   
   cmd = 'y'
   bytes_returned = ser.write(cmd.encode())
   print(bytes_returned)
   pb_vd_s.stop()
   pb_vd_s.destroy()
      
   progress_label_s.config(text = 'Complete')
   progress_label_s.config(foreground = 'green')
   ser.close()

# Update Results Step4 data
   global sl_captured_average_current_3, total_event_duration

   sl_captured_average_current_3 = sum(si)/(len(si))
   
   avg_sleep_event_I.configure(text=str(round(sl_captured_average_current_3,4)))

   sl_current_entry_4.delete(0, END)
   sl_current_entry_4.insert(0,round(sl_captured_average_current_3,4))

   sl_duration_entry_4.insert(0,sl_duration_entry_3.get())

   total_event_duration = sl_duration_entry_4.get() + ae_duration_entry_4.get()

   si.clear()

   step3_label.configure(foreground='black')
   step4_label.configure(foreground='blue')
   
#################################################################################
###    STEP4 CAPTURED RESULTS 
#################################################################################
def calc_profile():
#Apply Captured data to graph
   captured_ae_current_graph_label.configure(text= str(round(ae_current_entry_4.get(),4)), foreground='black',background='dark gray')
   captured_ae_duration_graph_label.configure(text=str(round(ae_duration_entry_4.get(),4)), foreground='black',background='dark gray')
   captured_sl_current_graph_label.configure(text=str(round(sl_current_entry_4.get(),4)), foreground='black',background='dark gray')
   captured_sl_duration_graph_label.configure(text=str(float(rt_dur.get())),foreground='black',background='dark gray')
   captured_batt_cap_graph_label.configure(text=str(int(batt_cap_entry_4.get())),foreground='black',background='dark gray')
   captured_ae_min_current_graph.configure(text=str(round(min_current,4)),foreground='black',background='dark gray')
   captured_ae_max_current_graph.configure(text=str(round(max_current,4)),foreground='black',background='dark gray'
   
#Calculate Captured Battery Life Hours
   global battery_life_hours, battery_life_days

   average_current_all_events = float(((sl_duration_entry_4.get()* sl_current_entry_4.get()) + (ae_duration_entry_4*ae_current_entry_4))
                                           / (sl_duration_entry_4.get() + ae_duration_entry_4.get()))

   #battery_life_hours = capacity in mAH / mA
   battery_life_hours =  float(batt_cap_entry_4.get()/average_current_all_events)                                 
   battery_life_days = float(battery_life_hours/24)
                                       
   captured_battery_life_hours_graph.configure(text=str(round(battery_life_hours,4)),foreground='blue',background='dark gray'
   captured_battery_life_days_graph.configure(text=str(round(battery_life_days,4)),foreground='blue',background='dark gray'
                                           
   filemenu.entryconfigure(4, state=tk.NORMAL)
   opt_batt_life_btn_4.configure(state=tk.NORMAL)
   calc_batt_life_btn_4.configure(state=tk.DISABLED)

   print('capture completed')
                               

#################################################################################
###    STEP5 OPTIMIZED RESULTS 
#################################################################################
def optimize_profile():

#Apply Optimized data to graph
   optimized_ae_current_graph_label.configure(text= str(round(ae_current_entry_4.get(),4)), foreground='black',background='dark gray')
   optimized_ae_duration_graph_label.configure(text=str(round(ae_duration_entry_4.get(),4)), foreground='black',background='dark gray')
   optimized_sl_current_graph_label.configure(text=str(round(sl_current_entry_4.get(),4)), foreground='black',background='dark gray')
   optimized_sl_duration_graph_label.configure(text=str(float(rt_dur.get())),foreground='black',background='dark gray')
   optimized_batt_cap_graph_label.configure(text=str(int(batt_cap_entry_4.get())),foreground='black',background='dark gray')
   optimized_ae_min_current_graph.configure(text=str(round(min_current,4)),foreground='black',background='dark gray')
   optimized_ae_max_current_graph.configure(text=str(round(max_current,4)),foreground='black',background='dark gray'
   
#Calculate Optimized Battery Life Hours
   global battery_life_hours, battery_life_days, average_current_all_events

   average_current_all_events = float(((sl_duration_entry_4.get()* sl_current_entry_4.get()) + (ae_duration_entry_4*ae_current_entry_4))
                                           / total_event_duration)

   #battery_life_hours = capacity in mAH / mA                         
   battery_life_hours =  float(batt_cap_entry_4.get()/average_current_all_events)                                 
   battery_life_days = float(battery_life_hours/24)
                                       
   optimized_battery_life_hours_graph.configure(text=str(round(battery_life_hours,4)),foreground='blue',background='dark gray'
   optimized_battery_life_days_graph.configure(text=str(round(battery_life_days,4)),foreground='blue',background='dark gray'

   filemenu.entryconfigure(4, state=tk.NORMAL)
                                            
   print('optimize completed')

 
#################################################################################
###    RESET
#################################################################################

def reset():
    try:
      ser = serial.Serial(com_port, baud_rate, timeout=None)
    except SerialException:
       print('Port is busy')
       
    #Set sense resistor to low
    cmd = 'l'
    bytes_returned = ser.write(cmd.encode())
    print(bytes_returned)
    print("sense_low")
        
    calc_batt_life_btn_4.configure(state=tk.NORMAL)
    opt_batt_life_btn_4.configure(state=tk.NORMAL)

    capture_active_event_button.configure(state=tk.NORMAL)
    psu_combo_box.configure(state=tk.NORMAL)
    trigger_box.config(state=tk.NORMAL)
    batt_cap.configure(state=tk.NORMAL)
    battery_chemistry_combo_box.configure(state=tk.NORMAL)
    battery_cells_combo_box.configure(state=tk.NORMAL)

    cmd = 'i' #turn voltage off
    bytes_returned = ser.write(cmd.encode())
    print('Voltage Off')
                                               
    ser.close()
                                               
    p_rad.configure(value=1,foreground='black',background='dark gray')
    p_rad.deselect()
    p_rad1.configure(value=0,foreground='red',background='dark gray')
    p_rad1.select()
    
    x[:] = []
    y[:] = []
    ax.cla()
    #uncomment to blank out the canvas
    #canvas.draw()
    print('reset completed')

def get_config():
   try:
       ser = serial.Serial(com_port, baud_rate, timeout=None)
   except SerialException:
        print('Port is busy')

   cmd = 'j'
   bytes_returned = ser.write(cmd.encode())
   data.set(ser.readline(2).hex())
   print('MFR CAL ',data.get())
   data.set(ser.readline(2).hex())
   print('ADC CONFIG ',data.get())
   ser.close()
   
#################################################################################
###    SETUP LABELS AND BUTTONS
#################################################################################
    
# STEP 1 - INPUT BATTERY INFO & PSU OUTPUT
#Battery
battery_capacity_label_1 = Label(profile_frame, text='Battery Capacity (mAH)',background='dark gray')
battery_capacity_label_1.grid(row=4, column=0, padx=10,pady=2,sticky = 'w')
battery_capactity_entry_1 = Entry(profile_frame, width=12)
battery_capactity_entry_1.grid(row=4, column=0, padx=(150,4), sticky = 'w')
battery_capactity_entry_1.focus_set()
battery_capactity_entry_1.insert(0,230)

battery_chemistry_label_1 = Label(profile_frame, text='Battery Chemistry',background='dark gray')
battery_chemistry_label_1.grid(row=5, column=0, padx=10,pady=2,sticky = 'w')
batt_chem = tk.StringVar()
battery_chemistry_combo_box = ttk.Combobox(profile_frame, width=10, textvariable=batt_chem)
battery_chemistry_combo_box['values'] = ('ALKALINE', 'LI-ION','NiMH/NiCd') 
battery_chemistry_combo_box.grid(row=5, column=0,padx=(150,4),sticky = 'w')
battery_chemistry_combo_box.current(0)
battery_chemistry_combo_box.bind('<<ComboboxSelected>>', set_voltage)

battery_cells = Label(profile_frame, text='Number of Cells',background='dark gray')
battery_cells.grid(row=6, column=0, padx=10,pady=2,sticky = 'w')
batt_cells = tk.StringVar()
battery_cells_combo_box = ttk.Combobox(profile_frame, width=10, textvariable=batt_cells)
battery_cells_combo_box['values'] = (1, 2, 3) 
battery_cells_combo_box.grid(row=6, column=0,padx=(150,4),sticky = 'w')
battery_cells_combo_box.current(0)
battery_cells_combo_box.bind('<<ComboboxSelected>>', set_voltage)

#Voltage
volt_lab = Label(profile_frame, text='PSU Voltage Output',background='dark gray')
volt_lab.grid(row=8, column=0, padx=10,pady=2,sticky = 'w')

dut_cuttoff_voltage = Label(profile_frame, text='DUT Cutoff Voltage',background='dark gray')
dut_cuttoff_voltage.grid(row=7, column=0, padx=10,pady=2,sticky = 'w')
dut_cutoff_voltage_entry = Entry(profile_frame, width=8)
dut_cutoff_voltage_entry.grid(row=7, column=0, padx=(150,4), sticky = 'w')
dut_cutoff_voltage_entry.focus_set()
dut_cutoff_voltage_entry.insert(0,0.9)
dut_cuttoff_voltage_label = Label(profile_frame, text='volts',background='dark gray')
dut_cuttoff_voltage_label.grid(row=7, column=0, padx=(210,4),pady=2,sticky = 'w')

voltage = tk.StringVar()
psu_combo_box = ttk.Combobox(profile_frame, width=5, textvariable=voltage)
psu_combo_box['values'] = (1.2, 1.5, 2.4, 3.0, 3.7, 4.2, 4.5) 
psu_combo_box.grid(row=8, column=0,padx=(150,4),sticky = 'w')
psu_combo_box.current(0)
psu_combo_box_label = Label(profile_frame, text='volts',background='dark gray')
psu_combo_box_label.grid(row=8, column=0, padx=(210,4),pady=2,sticky = 'w')


psu_lab = Label(profile_frame, text='PSU Output',background='dark gray')
psu_lab.grid(row=9, column=0, padx=10,pady=2,sticky = 'w')

p_radio = IntVar()
p_rad = Radiobutton(profile_frame, text = 'On', variable = p_radio, value = 1,
                    command = set_battery_voltage,background='dark gray')
p_rad.grid(row=9, column=0, padx=100, sticky = 'w')

p_rad1 = Radiobutton(profile_frame, text = 'Off', variable = p_radio, value = 0, command = set_battery_voltage,
                     foreground='red',background='dark gray')
p_rad1.grid(row=9, column=0, padx=(140,10),pady=2, sticky = 'w')


#STEP2 - SET UP CAPTURE TIME AND EXECUTE CAPTURE
capt_lab = Label(profile_frame, text='Duration(s)',background='dark gray')
capt_lab.grid(row=11, column=0, padx=(10,2),pady=2,sticky = 'w')

rt_c = Label(profile_frame, text='Capture Duration',background='dark gray')
rt_c.grid(row=11, column=0, padx=10,pady=2,sticky = 'w')
rt_dur = Entry(profile_frame, width=6)
rt_dur.grid(row=11, column=0, padx=(110,4), sticky = 'w')
rt_dur.focus_set()
rt_dur.insert(0,15)

choice_lab = Label(profile_frame, text='-OR-',background='dark gray')
choice_lab.grid(row=11, column=0, padx=(150,2),pady=2,sticky = 'w')

trig_var = IntVar()
trigger_box = tk.Checkbutton(profile_frame, text='Ext Trig', variable=trig_var,background='dark gray',state=tk.DISABLED)
trigger_box.grid(row=11, column=0, padx=(180,4),pady= 2,sticky='w')

capture_active_event_button = tk.Button(profile_frame,text='Capture Active I',command=capture_profile,state=tk.DISABLED)
capture_active_event_button.grid(row=12,column=0, padx=(10,4),pady= 4,sticky = 'w')

avg_active_event_I_2 = ttk.Label(profile_frame, text='0.00',font=('Arial Bold',10), foreground = 'black',background='dark gray')
avg_active_event_I_2.grid(row=13, column = 0, padx= 86,pady= 4, sticky = 'w')

avg_active_event_I_units = ttk.Label(profile_frame, text='mA',font=('Arial Bold',10), foreground = 'black',background='dark gray')
avg_active_event_I_units.grid(row=13, column = 0, padx=(125,4),pady= 4, sticky = 'w')

#STEP3 - CAPTURE SLEEP EVENT CURRENT WIDGETS

sl_duration_labe1_3 = Label(profile_frame, text='Enter Sleep Duration',background='dark gray')
sl_duration_labe1_3.grid(row=15, column=0, padx=10,pady=4,sticky = 'w')
sl_duration_entry_3 = Entry(profile_frame, width=10)
sl_duration_entry_3.grid(row=15, column=0,padx=(130,4),sticky = 'w')
sl_duration_entry_3.insert(0,4250)
sl_duration_units_lab_3 = Label(profile_frame, text='S',background='dark gray')
sl_duration_units_lab_3.grid(row=15, column=0, padx=(200,2),pady=4,sticky = 'w')

capture_sleep_btn_3 = tk.Button(profile_frame,text='Capture Sleep I',command=capture_sleep_profile,state=tk.NORMAL)
capture_sleep_btn_3.grid(row=16,column=0, padx=(10,4),pady= 4,sticky = 'w')

avg_sleep_event_I = ttk.Label(profile_frame, text='0.0000',font=('Arial Bold',10), foreground = 'black',background='dark gray')
avg_sleep_event_I.grid(row=17, column = 0, padx= 80,pady= 4, sticky = 'w')

avg_sleep_event_I_units = ttk.Label(profile_frame, text='mA',font=('Arial Bold',10), foreground = 'black',background='dark gray')
avg_sleep_event_I_units.grid(row=17, column = 0, padx=(125,4),pady= 4, sticky = 'w')

#STEP4 - RESULTS AND OPTIMIZE  WIDGETS
#Section 4 Fields
   #Active Event Current
ae_current_label_4 = Label(profile_frame, text='Active Event Current',background='dark gray')
ae_current_label_4.grid(row=20, column=0, padx=10,pady=4,sticky = 'w')
ae_current_entry_4 = Entry(profile_frame, width=10)
ae_current_entry_4.grid(row=20, column=0,padx=(130,4),sticky = 'w')
ae_current_entry_4.insert(0,0)
ae_current_units_lab_4 = Label(profile_frame, text='mA',background='dark gray')
ae_current_units_lab_4.grid(row=20, column=0, padx=(200,2),pady=4,sticky = 'w')

   #Active Event Duration
ae_duration_label_4 = Label(profile_frame, text='Active Event Duration',background='dark gray')
ae_duration_label_4.grid(row=21, column=0, padx=10,pady=4,sticky = 'w')
ae_duration_entry_4 = Entry(profile_frame, width=10)
ae_duration_entry_4.grid(row=21, column=0,padx=(130,4),sticky = 'w')
ae_duration_entry_4.insert(0,int(rt_dur.get()))
ae_duration_units_lab_4 = Label(profile_frame, text='S',background='dark gray')
ae_duration_units_lab_4.grid(row=21, column=0, padx=(200,2),pady=4,sticky = 'w')

   #Sleep Event Current
sl_current_label_4 = Label(profile_frame, text='Sleep Current',background='dark gray')
sl_current_label_4.grid(row=22, column=0, padx=10,pady=4,sticky = 'w')
sl_current_entry_4 = Entry(profile_frame, width=10)
sl_current_entry_4.grid(row=22, column=0,padx=(130,4),sticky = 'w')
sl_current_entry_4.insert(0,1)
sl_current_units_lab_4 = Label(profile_frame, text='mA',background='dark gray')
sl_current_units_lab_4.grid(row=22, column=0, padx=(200,2),pady=4,sticky = 'w')

   #Sleep Event Duration
sl_duration_labe1_4 = Label(profile_frame, text='Sleep Duration',background='dark gray')
sl_duration_labe1_4.grid(row=23, column=0, padx=10,pady=4,sticky = 'w')
sl_duration_entry_4 = Entry(profile_frame, width=10)
sl_duration_entry_4.grid(row=23, column=0,padx=(130,4),sticky = 'w')
sl_duration_entry_4.insert(0,3600)
sl_duration_units_lab_4 = Label(profile_frame, text='S',background='dark gray')
sl_duration_units_lab_4.grid(row=23, column=0, padx=(200,2),pady=4,sticky = 'w')

   #Battery Capacity
batt_cap_label_4 = Label(profile_frame, text='Battery Capacity',background='dark gray')
batt_cap_label_4.grid(row=24, column=0, padx=10,pady=2,sticky = 'w')
batt_cap_entry_4 = Entry(profile_frame, width=10)
batt_cap_entry_4.grid(row=24, column=0, padx=(130,4), sticky = 'w')
batt_cap_entry_4.focus_set()
batt_cap_units_lab_4 = Label(profile_frame, text='mAh',background='dark gray')
batt_cap_units_lab_4.grid(row=24, column=0, padx=(200,2),pady=4,sticky = 'w')

#Calc Button
calc_batt_life_btn_4 = tk.Button(profile_frame,text='Calc',command=calc_profile,state=tk.DISABLED)
calc_batt_life_btn_4.grid(row=27, column=0, padx=(10,4),pady= 4,sticky = 'W')

#Captured Profile
captured_profile_label = ttk.Label(profile_frame, text='Captured Profile' ,foreground='black',background='dark gray')
captured_profile_label.grid(row=26, column = 6, padx=(5,1),sticky = 'w')

ae_captured_current_label_graph = ttk.Label(profile_frame, text='Active Event I (mA)',background='dark gray')
ae_captured_label_graph_entry.grid(row=25, column = 7,padx=(5,1),sticky = 'e')
captured_ae_current_graph_label = ttk.Label(profile_frame, text='-' ,foreground='black',background='dark gray')
captured_ae_current_graph.grid(row=26, column = 7, padx=(5,1),sticky = 'e')

ae_captured_duration_label = ttk.Label(profile_frame, text='Active Event Duration (s)',background='dark gray')
ae_captured_duration_label.grid(row=25, column = 8,padx=(5,1),sticky = 'e')
captured_ae_duration_graph_label = ttk.Label(profile_frame, text='-',background='dark gray')
captured_ae_duration_graph_label.grid(row=26, column = 8,padx=(5,1),sticky = 'e')

sl_captured_current_label = ttk.Label(profile_frame, text='Sleep I (mA)',background='dark gray')
sl_captured_current_label.grid(row=25, column = 9,padx=(5,1),sticky = 'e')
captured_sl_current_graph_label = ttk.Label(profile_frame, text='-',background='dark gray')
captured_sl_current_graph_label.grid(row=26, column = 9,padx=(5,1),sticky = 'e')

sl_captured_duration_graph_label = ttk.Label(profile_frame, text='Sleep Duration',background='dark gray')
sl_captured_duration_graph_label.grid(row=25, column = 10,padx=(5,1),sticky = 'e')
captured_sl_duration_graph_label = ttk.Label(profile_frame, text='-' ,foreground='black',background='dark gray')
captured_sl_duration_graph_label.grid(row=26, column = 10, padx=(5,1),sticky = 'e')

batt_cap_captured_graph_label = ttk.Label(profile_frame, text='Battery Capacity(mAH)',background='dark gray')
batt_cap_captured_graph_label.grid(row=25, column = 11,padx=(5,1),sticky = 'e')
captured_batt_cap_graph_label = ttk.Label(profile_frame, text='-' , foreground='black',background='dark gray')
captured_batt_cap_graph_label.grid(row=26, column = 11,padx=(5,1),sticky = 'e')

min_current_captured_graph_label = ttk.Label(profile_frame, text='Min Current (mA)',background='dark gray')
min_current_captured_graph_label.grid(row=25, column = 11,padx=(5,1),sticky = 'e')
captured_ae_min_current_graph = ttk.Label(profile_frame, text='-' , foreground='black',background='dark gray')
captured_ae_min_current_graph.grid(row=26, column = 11,padx=(5,1),sticky = 'e')

max_current_captured_graph_label = ttk.Label(profile_frame, text='Max Current (mA)',background='dark gray')
max_current_captured_graph_label.grid(row=25, column = 12,padx=(5,1),sticky = 'e')
captured_ae_max_current_graph = ttk.Label(profile_frame, text='-' ,background='dark gray')
captured_ae_max_current_graph.grid(row=26, column = 12,padx=(5,1),sticky = 'e')

batt_life_hours_captured_graph_label = ttk.Label(profile_frame, text='Battery Life(Hrs)',foreground = 'blue',background='dark gray')
batt_life_hours_captured_graph_label.grid(row=25, column=13, padx=(5,1), sticky = 'e')
captured_battery_life_hours_graph = ttk.Label(profile_frame, text='-',foreground='blue',background='dark gray')
captured_battery_life_hours_graph.grid(row=26, column = 13,padx=(5,1),sticky = 'e')

batt_life_days_captured_graph_label = ttk.Label(profile_frame, text='Battery Life (Days)', foreground = 'blue',background='dark gray')
batt_life_days_captured_graph_label.grid(row=25, column = 14,padx=(5,1),sticky = 'e')
captured_battery_life_days_graph = ttk.Label(profile_frame, text='-' ,foreground='blue',background='dark gray')
captured_battery_life_days_graph_graph.grid(row=26, column = 14,padx=(5,1),sticky = 'e')


#Optimized Profile
optimized_profile_label = Label(profile_frame, text='Optimized Profile',background='dark gray')
optimized_profile_label.grid(row=28, column=6, padx=(5,1),pady=4,sticky = 'w')

ae_optimized_current_label_graph = ttk.Label(profile_frame, text='Active Event I (mA)',background='dark gray')
ae_optimized_label_graph_entry.grid(row=25, column = 7,padx=(5,1),sticky = 'e')
optimized_ae_current_graph_label = ttk.Label(profile_frame, text='-' ,foreground='black',background='dark gray')
optimized_ae_current_graph.grid(row=26, column = 7, padx=(5,1),sticky = 'e')

ae_optimized_duration_label = ttk.Label(profile_frame, text='Active Event Duration (s)',background='dark gray')
ae_optimized_duration_label.grid(row=25, column = 8,padx=(5,1),sticky = 'e')
optimized_ae_duration_graph_label = ttk.Label(profile_frame, text='-',background='dark gray')
optimized_ae_duration_graph_label.grid(row=26, column = 8,padx=(5,1),sticky = 'e')

sl_optimized_current_label = ttk.Label(profile_frame, text='Sleep I (mA)',background='dark gray')
sl_optimized_current_label.grid(row=25, column = 9,padx=(5,1),sticky = 'e')
optimized_sl_current_graph_label = ttk.Label(profile_frame, text='-',background='dark gray')
optimized_sl_current_graph_label.grid(row=26, column = 9,padx=(5,1),sticky = 'e')

sl_optimized_duration_graph_label = ttk.Label(profile_frame, text='Sleep Duration',background='dark gray')
sl_optimized_duration_graph_label.grid(row=25, column = 10,padx=(5,1),sticky = 'e')
optimized_sl_duration_graph_label = ttk.Label(profile_frame, text='-' ,foreground='black',background='dark gray')
optimized_sl_duration_graph_label.grid(row=26, column = 10, padx=(5,1),sticky = 'e')

batt_cap_optimized_graph_label = ttk.Label(profile_frame, text='Battery Capacity(mAH)',background='dark gray')
batt_cap_optimized_graph_label.grid(row=25, column = 11,padx=(5,1),sticky = 'e')
captured_batt_cap_graph_label = ttk.Label(profile_frame, text='-' , foreground='black',background='dark gray')
captured_batt_cap_graph_label.grid(row=26, column = 11,padx=(5,1),sticky = 'e')

min_current_optimized_graph_label = ttk.Label(profile_frame, text='Min Current (mA)',background='dark gray')
min_current_optimized_graph_label.grid(row=25, column = 12,padx=(5,1),sticky = 'e')
optimized_ae_min_current_graph = ttk.Label(profile_frame, text='-' , foreground='black',background='dark gray')
optimized_ae_min_current_graph.grid(row=26, column = 12,padx=(5,1),sticky = 'e')

max_current_optimized_graph_label = ttk.Label(profile_frame, text='Max Current (mA)',background='dark gray')
max_current_optimized_graph_label.grid(row=25, column = 13,padx=(5,1),sticky = 'e')
optimized_ae_max_current_graph = ttk.Label(profile_frame, text='-' ,background='dark gray')
optimized_ae_max_current_graph.grid(row=26, column = 13,padx=(5,1),sticky = 'e')

batt_life_hours_optimized_graph_label = ttk.Label(profile_frame, text='Battery Life(Hrs)',foreground = 'blue',background='dark gray')
batt_life_hours_optimized_graph_label.grid(row=25, column=14, padx=(5,1), sticky = 'e')
optimized_battery_life_hours_graph = ttk.Label(profile_frame, text='-',foreground='blue',background='dark gray')
optimized_battery_life_hours_graph.grid(row=26, column = 14,padx=(5,1),sticky = 'e')

batt_life_days_optimized_graph_label = ttk.Label(profile_frame, text='Battery Life (Days)', foreground = 'blue',background='dark gray')
batt_life_days_optimized_graph_label.grid(row=25, column = 15,padx=(5,1),sticky = 'e')
optimized_battery_life_days_graph = ttk.Label(profile_frame, text='-' ,foreground='blue',background='dark gray')
optimized_battery_life_days_graph_graph.grid(row=26, column = 15,padx=(5,1),sticky = 'e')

#Optimize Button
opt_batt_life_btn_4 = tk.Button(profile_frame,text='Optimize',command=optimize_profile,state=tk.DISABLED)
opt_batt_life_btn_4.grid(row=28, column=0, padx=(10,4),pady= 4,sticky = 'W')

##RESET
reset_button = tk.Button(profile_frame,text='Reset',command=reset,state=tk.DISABLED)
reset_button.grid(row=29,column=0, padx=(10,4),pady= 4,sticky = 'w')

#STEP LABELS
step1_label = ttk.Label(profile_frame, text='Step1 - Battery Info and PSU Output',font=('Arial Bold',11), foreground = 'blue',background='dark gray')
step1_label.grid(row=3, column = 0, padx=2,pady=(20,2), sticky = 'w',columnspan=2)

step2_label = ttk.Label(profile_frame, text='Step2 - Active Event',font=('Arial Bold',11), background='dark gray')
step2_label.grid(row=10, column = 0, padx=2,pady=4,sticky = 'w',columnspan=2)

step3_label = ttk.Label(profile_frame, text='Step3 - Sleep Event',font=('Arial Bold',11), background='dark gray')
step3_label.grid(row=14, column = 0, padx=2, pady=4, sticky = 'w')

step4_label = ttk.Label(profile_frame, text='Step4 - Results and Optimization',font=('Arial Bold',11), background='dark gray')
step4_label.grid(row=19, column = 0, padx=2, pady=4, sticky = 'w')

BUTTON = tk.Button(profile_frame,text='GET CONFIG',command=get_config,state=tk.NORMAL)
BUTTON.grid(row=37,column=0, padx=(10,4),pady= 4,sticky = 'w')

root.mainloop()
