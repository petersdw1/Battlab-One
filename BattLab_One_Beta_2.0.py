
import tkinter as tk
from tkinter import ttk
from tkinter import *
import csv
import time
import datetime
import serial
import serial.tools.list_ports
from serial.tools import list_ports
import matplotlib
from matplotlib.widgets import Cursor
import matplotlib.pyplot as plt
from tkinter import colorchooser
import os
import pkg_resources.py2_warn

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
root.wm_title('BattLab One')
root.resizable(True,True)
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)
root.iconbitmap('bbirdlogo.ico')

s = ttk.Style() 
s.configure('TLabelframe', background='dark gray')

profile_frame = ttk.Frame(root,style='TLabelframe', width = 1440, height = 960)
#profile_frame = ttk.LabelFrame(root, text = 'IOTA Beta_08',style='TLabelframe', width = 1300, height = 740)
profile_frame.grid(row=0, column=0, padx=2,pady=(2,2),sticky = 'w')
#profile_frame.grid_propagate(False)

frame = ttk.Frame(profile_frame, borderwidth=5, relief='sunken', width=990, height=545)
frame.grid(row=3, column=5, rowspan=22,columnspan=20,padx=(10,30),pady=(20,2), sticky='nswe')

w = Canvas(frame, width=990, height=545)
w.config(background='black')
w.grid(row=0,column = 3,padx=2,pady=2,sticky = 'nswe')
#img = PhotoImage(file='bbirdlogo_png.png')      
#w.create_image(30,5, anchor = SE, image=img)

#################################################################################
###   SETUP GLOBAL VARIABLES
#################################################################################
global si,x,y, avg_active_event_I,hi_offset, hi_offset, line_color, sleep_timer

x = []
y = []
si = []
soc = []
ocv = []
esr = []

hi_offset=tk.DoubleVar()
hi_offset.set(1.0)

lo_offset=tk.DoubleVar()
lo_offset.set(0)

sleep_timer=tk.IntVar()
sleep_timer.set(10)
   
sense_hi = 97

LSB=0.0025

line_color = StringVar()
line_color.set("blue")

line_width = DoubleVar()
line_width.set(0.5)

reading = StringVar()
data = StringVar()
sense_resistor=tk.DoubleVar()

#################################################################################
###   GET SERIAL PORT AND CONNECT
#################################################################################

baud_rate = 115200
com_port = "NONE"

def get_ports():
   ports = list(serial.tools.list_ports.comports())
   cpl = []
   for p in ports:
      cpl.append(p.device)   
   return cpl

def popupmsg(msg):
    popup = tk.Tk()
    popup.iconbitmap('bbirdlogo.ico')
    popup.wm_title("About")
    label = ttk.Label(popup, text=msg,)
    label.grid(row=0,column=0, padx=(10,10),pady= (10,10),sticky = 'nsew')
    pop_up_button = tk.Button(popup, text="Okay",command = popup.destroy,state=tk.NORMAL)
    pop_up_button.grid(row=3,column=0,padx=30,pady=(10,10),sticky = 'w')
    popup.mainloop()

def popupmsg1(msg):
    popup1 = tk.Tk()
    popup1.iconbitmap('bbirdlogo.ico')
    popup1.wm_title("Sleep Capture Duration")
    label2 = ttk.Label(popup1, text="Current Duration in Seconds (10 recommended) = "+ str(sleep_timer.get()))
    label2.grid(row=1,column=0, padx=(10,10),pady= (10,10),sticky = 'nsew')
    sleep_dur__combo_box = ttk.Combobox(popup1, width=5, textvariable=sleep_timer)
    sleep_dur__combo_box['values'] = (1, 3, 5, 10) 
    sleep_dur__combo_box.grid(row=3, column=0,padx=(150,4),sticky = 'w')
    sleep_dur__combo_box.insert(0,sleep_timer.get())
    def set_sleep_time():
      sleep_timer.set(float(sleep_dur__combo_box.get()))
      print("Sleep Timer = ", sleep_timer.get())
      popup1.destroy()
    label1 = ttk.Label(popup1, text=msg,)
    label1.grid(row=0,column=0, padx=(10,10),pady= (10,10),sticky = 'nsew')
    pop_up_button2 = tk.Button(popup1, text="Set Time",command = set_sleep_time,state=tk.NORMAL)
    pop_up_button2.grid(row=3,column=0,padx=80,pady=(10,10),sticky = 'w')
    popup1.mainloop()

ser_port_combo_box = ttk.Combobox(profile_frame, values = get_ports(), width=10)
ser_port_combo_box.grid(row=2, column=0,padx=(10,4),sticky = 'w')

ser_port_cct = Label(profile_frame, text="BB1 Port = ",background='dark gray')
ser_port_cct.grid(row=1, column=0, padx=(10,4),pady=2,sticky = 'w')

reset_comm = tk.Button(profile_frame,text='Connect',command=lambda:init(str(ser_port_combo_box.get())),state=tk.NORMAL)
reset_comm.grid(row=2,column=0, padx=(160,4),pady= 2,sticky = 'w')

reset_list = tk.Button(profile_frame,text='Refresh',command=lambda:update_ports(),state=tk.NORMAL)
reset_list.grid(row=2,column=0, padx=(100,4),pady= 2,sticky = 'w')
   
def init(ser_port):
   global ser, sense_low
   
   try:
      ser = serial.Serial(ser_port, baud_rate, timeout= None)
      ser_port_cct.configure(text = "Battlab Connected(" + ser.name+")", foreground='green', font=('Arial Bold',10))
      cmd = 'j'
      bytes_returned = ser.write(cmd.encode())
      data.set(ser.readline(2).hex())
      #print('Res_code_Lo1 ',int(data.get(),16)/1000)
      sense_low = int(data.get(),16)/1000
      sense_resistor.set(sense_low)
      ser_port_combo_box.insert(0,ser.name)
   except serial.SerialException as e:
      messagebox.showinfo("Error No Battlab Device Connected",e)
      pass
      
ports = list(serial.tools.list_ports.comports())

for p in ports:
   
   if p.vid == 0x0403 and p.pid == 0x6001:
      ser_num_prefix = p.serial_number[0] + p.serial_number[1]
      if ser_num_prefix == 'BB':
         com_port = list(list_ports.grep("0403:6001"))[0][0]       
         init(com_port)

if com_port == 'NONE':
   ser_port_cct.configure(text="Not Connected!", foreground='red')

def update_ports():
   ports = list(serial.tools.list_ports.comports())
   cpl = []
   for p in ports:
      cpl.append(p.device)
   ser_port_combo_box.configure(values=cpl)


#################################################################################
###    SETUP MENU FUNCTIONS
#################################################################################

    
def OpenFile():
    name = filedialog.askopenfilename(initialdir = 'C:/Users/dwpete3/Desktop',title = 'Select file',
                                filetypes = (('Battlab files','*.bbl'),('all files','*.*')))
    file = open(name,'rb')
    object_file = pickle.load(file)
    file.close()
    output=object_file.get_values()


def SaveFile():
    root.filename =  filedialog.asksaveasfilename(initialdir = 'C:/Users/dwpete3/Desktop',title = 'Select file',
                                filetypes = (('Battlab files','*.bbl'),('all files','*.*')))

    current_profile = Profile('Profile'+ '-'+ str(datetime.datetime.now()),batt_chem.get(), batt_cells.get(), float(dut_cutoff_captured_label_4.cget("text")), voltage.get(), \
                     float(ae_captured_current_label_4.cget("text")), float(ae_captured_duration_label_4.cget("text")), float(sl_captured_current_label_4.cget("text")),\
                    float(batt_cap_captured_label_4.cget("text")), float(average_current_profile_captured_label_4.cget("text")),\
                   float(captured_battery_life_hours_graph.cget("text")), float(captured_battery_life_days_graph.cget("text")), max_current, min_current)

    filehandler = open(root.filename+'.bbl','wb')
    pickle.dump(current_profile,filehandler)
    filehandler.close()

def Linecolor():
    ln_color, hex_color = colorchooser.askcolor(parent=frame,initialcolor=(255, 0, 0))   
    line_color.set(hex_color)

def SleepDurationTime():
    popupmsg1("Please choose the duration for sleep capture mode in seconds")
    
    
def About():
    #messagebox.showinfo("Battlab-One Version 1.0 \n\r Contact www.bluebird-labs.com/support for issues")
    popupmsg("Battlab-One Version 1.0 \n\r Contact www.bluebird-labs.com/support for issues")
   
#################################################################################
###   SETUP MENU SYSTEM
#################################################################################
menu = Menu(root)

root.config(menu=menu)

filemenu = Menu(menu)
menu.add_cascade(label='File', menu=filemenu)
filemenu.add_command(label='Open...', command=OpenFile)
filemenu.add_command(label='Save...', command=SaveFile)
filemenu.add_separator()
filemenu.add_command(label='Exit', command=root.quit)

optionsmenu = Menu(menu)
menu.add_cascade(label='Options', menu=optionsmenu)
optionsmenu.add_command(label='Choose Line Color...', command=Linecolor)
optionsmenu.add_command(label='Choose Duration for Sleep Capture...', command=SleepDurationTime)


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
        name: A string representing the profile's name and other details; string/system generated
        bat_chem: battery chemistry, A string representing the battery chemistry. string/user entered.
        n_cells: number of cells: An int representing the number of cells. integer/user entered.
        cuttoff_voltage: The voltage at which the DUT stops working; float. float/user entered
        psu_voltage: A float representing the PSU voltage set. float/user entered
        active_event_duration: A float representing the amount of time for the active current event. float/captured data
        active_event_current: Average Current for the active event:  float/captured data
        active_event_duraton: Time duration of the active event (either user set or from trigger). float/captured data
        sleep_current: Sleep current captured; float/captured data
        effective_bat_cap: effective battery capacity, The battery capacity based on the SOC data for the selected battery. float/system generated
        battery_life_hours: The expected battery life based on the effective battery capacity and the average total profile current; float/system generated
        average_ciurrent_profile: Total Current for the Profile; float/captured data
        battery_life_days: The expected battery life in days divided by 24 hours; float/system generated
        max_current:Maximium current of active event: float / data captured
        min_current: Minimum current of active event: float / data captured
    ''' 

    def __init__(self, name, bat_chem, n_cells, cuttoff_voltage, psu_voltage,  active_event_current, active_event_duration, sleep_current,
                 effective_bat_cap, average_current_profile, battery_life_hours, battery_life_days, max_current, min_current):
        '''Set Profile attributes'''
        self.name = name
        self.bat_chem = bat_chem
        self.n_cells = n_cells
        self.cutoff_voltage = cuttoff_voltage
        self.psu_voltage = psu_voltage
        self.active_event_current = active_event_current
        self.active_event_duration = active_event_duration
        self.sleep_current = sleep_current
        self.effective_bat_cap = effective_bat_cap
        self.average_current_profile = average_current_profile
        self.battery_life_hours = battery_life_hours
        self.battery_life_days = battery_life_days
        self.max_current = max_current
        self.min_current = min_current
        

    def set_values(self, name, bat_chem, n_cells, cuttoff_voltage, psu_voltage, active_event_current,active_event_duration,\
                   sleep_current, effective_bat_cap, average_current_profile, battery_life_hours, battery_life_days, max_current, min_current):
       
        self.name = name
        self.bat_chem = bat_chem
        self.n_cells = n_cells
        self.cutoff_voltage = cuttoff_voltage
        self.psu_voltage = psu_voltage
        self.active_event_current = active_event_current
        self.active_event_duration = active_event_duration
        self.sleep_current = sleep_current
        self.effective_bat_cap = effective_bat_cap
        self.battery_life_hours = battery_life_hours
        self.battery_life_days = battery_life_days
        self.max_current = max_current
        self.min_current = min_current

    def get_values(self):
        '''Return all values'''
        return self.name, self.bat_chem, self.n_cells, self.cutoff_voltage, self.psu_voltage, self.active_event_current,\
        self.active_event_duration, self.sleep_current, self.effective_bat_cap, self.average_current_profile, self.battery_life_hours, self.battery_life_days,\
        self.max_current, self.min_current


#################################################################################
####     STEP1 SET BATTERY PARAMETERS AND PSU OUTPUT
#################################################################################

def set_battery_voltage():
   
    #Turn OFF low current sense resistor
    sense_resistor.set(sense_low)
    cmd = 'l'
    bytes_returned = ser.write(cmd.encode())
    
    if int(p_radio.get()) == 1:
        p_rad.config(foreground='green')
        p_rad1.config(foreground='black')

        if voltage.get()== '1.2':
           volts = 1.2   
           cmd = 'a'
           bytes_returned = ser.write(cmd.encode())
           hi_offset.set(0.625)
           lo_offset.set(0.0017)
        elif voltage.get()== '1.5':
           volts = 1.5   
           cmd = 'b'
           bytes_returned = ser.write(cmd.encode())
           hi_offset.set(0.77)
           lo_offset.set(0.0028)
        elif voltage.get()== '2.4':
           volts = 2.4   
           cmd = 'c'
           bytes_returned = ser.write(cmd.encode())
           hi_offset.set(0.96)
           lo_offset.set(0.0032)
        elif voltage.get()== '3.0':
           volts = 3.0   
           cmd = 'd'
           bytes_returned = ser.write(cmd.encode())
           hi_offset.set(1.0)
        elif voltage.get()== '3.6':
           volts = 3.6   
           cmd = 'n'
           bytes_returned = ser.write(cmd.encode())
           hi_offset.set(1.02)
           lo_offset.set(0.009)
        elif voltage.get()== '3.7':
           volts = 3.7
           cmd = 'e'
           bytes_returned = ser.write(cmd.encode())
           hi_offset.set(1.027)
        elif voltage.get()== '4.2':
           volts = 4.2  
           cmd = 'f'
           bytes_returned = ser.write(cmd.encode())
           hi_offset.set(1.041)
        elif voltage.get()== '4.5':
           volts = 4.5 
           cmd = 'g'
           bytes_returned = ser.write(cmd.encode())
           hi_offset.set(1.22)
           
        cmd = 'h'
        bytes_returned = ser.write(cmd.encode())
   

    elif int(p_radio.get()) == 0:
        p_rad.config(foreground='black')
        p_rad1.config(foreground='red')
        cmd = 'i'
        bytes_returned = ser.write(cmd.encode())
        
    capture_active_event_button.configure(state=tk.NORMAL)
    trigger_box.config(state=tk.NORMAL)
    battery_chemistry_combo_box.configure(state=tk.DISABLED)
    battery_cells_combo_box.configure(state=tk.DISABLED)
    psu_combo_box.configure(state=tk.DISABLED)
    
    step1_label.configure(foreground='black')
    step2_label.configure(foreground='blue')
    
def set_voltage(eventObject):
    if ((batt_chem.get() == 'AA-Alkaline' or batt_chem.get() == 'AAA-Alkaline') and batt_cells.get() == '1'):
        psu_combo_box.current(1)
        voltage.set(1.5)
    elif((batt_chem.get() == 'AA-Alkaline' or batt_chem.get() == 'AAA-Alkaline') and batt_cells.get() == '2'):
        psu_combo_box.current(3)
        voltage.set(3.0)
    elif((batt_chem.get() == 'AA-Alkaline' or batt_chem.get() == 'AAA-Alkaline') and batt_cells.get() == '3'):
        psu_combo_box.current(6)
        voltage.set(4.5)
    elif(batt_chem.get() == 'LI-Ion' and batt_cells.get() == '1'):
        psu_combo_box.current(5)
        voltage.set(3.7)
    elif(batt_chem.get() == 'LiFepo4' and batt_cells.get() == '1'):
        psu_combo_box.current(5)
        voltage.set(3.2)
    elif(batt_chem.get() == 'NiMH/NiCd' and batt_cells.get() == '1'):
        psu_combo_box.current(0)
        voltage.set(1.2)
    elif(batt_chem.get() == 'NiMH/NiCd' and batt_cells.get() == '2'):
        psu_combo_box.current(1)
        voltage.set(2.4)
    elif(batt_chem.get() == 'Li-Coin' or batt_chem.get() == 'CR123' and batt_cells.get() == '1'):
        psu_combo_box.current(4)
        voltage.set(3.0)
    elif(batt_chem.get() == 'NiMH/NiCd' and batt_cells.get() == '3'):
        psu_combo_box.current(4)
        voltage.set(4.2)
    else:
        messagebox.showerror('Battery Info Error')


#################################################################################
###    STEP2 CAPTURE PROFILE
#################################################################################
def TrigArmed():
    trigger_box.configure(foreground='red')
  
def capture_profile():

    global canvas,f,ax, ae_captured_average_current_2, ae_captured_duration_2, max_current, min_current, offset

    f = plt.figure(figsize=(9.5, 4.5), dpi=100,clear=True)
    ax = f.add_subplot(111)
    
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    ser.send_break(duration=0.25)
    
    ae_captured_average_current_2 = 0
    ae_captured_duration_2 = 0
    counter = 0
    cntr = DoubleVar()
    reading = StringVar()
    u = 0
    t=0
    delay=0
    
    my_file=open('raw_byte_file.txt', mode='w', buffering =(10*1024*1024))
    
    progress_label = ttk.Label(profile_frame, text='',background='dark gray')
    progress_label.grid(row=12, column = 0, padx=(230,4),sticky='w')

       #USE TRIGGER FOR CAPTURE
    if trig_var.get()==1:

        progress_label.config(text = 'Capturing...' )
        progress_label.config(foreground = 'red' )

        #Start the data logger
        cmd = 'x'
        bytes_returned = ser.write(cmd.encode())
        #time.sleep(0.5)
        
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
                    break 
        progress_label.config(text = 'Complete' )
        progress_label.config(foreground = 'green' )

        #USE TIME (DURATION) FOR CAPTURE
    else:
        pb_vd = ttk.Progressbar(profile_frame, orient='horizontal', mode='determinate',
                                maximum = float(rt_dur.get()),length=100, variable=cntr)
        
        pb_vd.grid(row=12,column = 0,columnspan=1,padx=(120,1),sticky = 'w')
        pb_vd.start()
    
        progress_label.config(text = 'Capturing...' )
        progress_label.config(foreground = 'red' )
        
        cmd = 'z'
        bytes_returned = ser.write(cmd.encode())
        #time.sleep(0.5)
      
        offset=time.clock()
           
        while counter < (float(rt_dur.get())*0.81): 
            my_file.write(str(t))
            my_file.write(',')
            reading.set(ser.readline(2).hex())
            my_file.write(str(reading.get()))
            my_file.write('\n')

            #t=int(time.clock()*1000)
            t=t+1
            root.update()
        
            counter = time.clock()-offset
            cntr.set(counter)
            profile_frame.update()

        cmd = 'y'
        bytes_returned = ser.write(cmd.encode())
        delay = delay+0.05*100
        
        pb_vd.stop()
        pb_vd.destroy()
      
        progress_label.config(text = 'Complete')
        progress_label.config(foreground = 'green')

    my_file.close()
    
    with open('raw_byte_file.txt', 'r')as csvfile:
        inp = csv.reader(csvfile, delimiter = ',')
        for row in inp:        
            if round((int(row[1],16)*LSB)/float(sense_resistor.get()),5) < 990 \
                  and round((int(row[1],16)*LSB)/float(sense_resistor.get()),5) != 0.0:
              x.append(int(row[0]))
              y.append(round((int(row[1],16)*LSB*hi_offset.get())/float(sense_resistor.get()),5))
            else:
              u=u+1  #Do Nothing

    csvfile.close()
    rows = zip(x,y)
    
    #Feed this to Matplotlib
    with open('outputfile.txt', 'w') as analysis:
        writer = csv.writer(analysis)
        for row in rows:
            writer.writerow(row)
    analysis.close()

    #PLOT THE DATA
   
    #print(plt.style.available)
    plt.style.use('fast')
    
    ax.set_title('Profile: ' +'Voltage = ' + voltage.get() + ' volts, ' + 'Time = '+ rt_dur.get() + ' seconds')
    ax.set_xlabel('Milliseconds')
    ax.set_ylabel('Milliamps')
 
    ax.plot(x, y, color=line_color.get(), linewidth=line_width.get())

    ax.grid(b=True, which='major', axis='both',color='black', linestyle='-', linewidth=.1)
    
    cursor = Cursor(ax,color=line_color.get(), linewidth=.3)
    
    canvas = FigureCanvasTkAgg(f, master=w)
    canvas.get_tk_widget().grid(row=0,column=6)

    toolbarFrame = ttk.Frame(master=frame)
    toolbarFrame.grid(row=14, column=3, sticky='w' )
    toolbar = NavigationToolbar2Tk(canvas, toolbarFrame)
    #toolbar = NavigationToolbar2TkAgg(canvas, toolbarFrame)
    canvas.draw()

#Gather data and statistics
    ae_captured_average_current_2 = sum(y)/(len(y))
    
    ae_captured_duration_2 = (max(x)-min(x))/1000
    
    max_current = max(y)
    min_current = min(y)

    print("Capture Duration = ", ae_captured_duration_2)
    print("Maximum Current = ", max_current)
    print("Minimum Current = ", min_current)

    avg_active_event_I_2.configure(text=str(round(ae_captured_average_current_2,2)))

    #Fill out partial Step 4 Actuals  
    ae_captured_current_label_4.configure(text=str(round(float(ae_captured_average_current_2),2)), foreground='black',background='dark gray') 
    ae_captured_duration_label_4.configure(text=str(round(float(ae_captured_duration_2),2)), foreground='black',background='dark gray')
    dut_cutoff_captured_label_4.configure(text=str(float(dut_cutoff_voltage_entry.get())), foreground='black',background='dark gray')
    

    #Copy partial Step 4 Actuals to Optimized
    ae_optimized_current_entry_4.insert(0,str(round(float(ae_captured_average_current_2),2)))
    ae_optimized_duration_entry_4.insert(0,str(round(float(ae_captured_duration_2),2)))
    dut_cutoff_optimized_entry_4.insert(0,str(float(dut_cutoff_voltage_entry.get())))
    

    avg_active_event_I_2.configure(foreground='green',state=tk.NORMAL)
    avg_active_event_I_units.configure(foreground='green',state=tk.NORMAL)

    step2_label.configure(foreground='black')
    step3_label.configure(foreground='blue')

    #Turn ON low current sense resistor
    sense_resistor.set(sense_hi)
    cmd = 'k'
    bytes_returned = ser.write(cmd.encode())

    time.sleep(0.5)

#################################################################################
###    STEP3 CAPTURE SLEEP CURRENT
#################################################################################

def capture_sleep_profile():

   soc_state = 0
    
   sleep_reading = StringVar()
   counter1 = 0    
   cntr1 = DoubleVar()
 
   progress_label_s = ttk.Label(profile_frame, text='',background='dark gray')
   progress_label_s.grid(row=15, column = 0, padx=(230,4),sticky='w')

   pb_vd_s = ttk.Progressbar(profile_frame, orient='horizontal', mode='determinate',
                                maximum = sleep_timer.get(),length=100, variable=cntr1)
        
   pb_vd_s.grid(row=15,column = 0,columnspan=1,padx=(120,1),sticky = 'w')
   pb_vd_s.start()
    
   progress_label_s.config(text = 'Capturing...' )
   progress_label_s.config(foreground = 'red' )
   
   sleep_file=open('sleep_current.txt', mode='w', buffering =(10*1024*1024))
   
   offset1=time.clock()
   cmd = 'z'
   bytes_returned = ser.write(cmd.encode())

   while counter1 < sleep_timer.get():
      sleep_reading.set(ser.readline(2).hex())
      if round((int(sleep_reading.get(),16)*LSB)/float(sense_resistor.get()),4) < 990 \
                  and round((int(sleep_reading.get(),16)*LSB)/float(sense_resistor.get()),4) != 0.0:
        si.append(round((int(sleep_reading.get(),16)*LSB)/float(sense_resistor.get()),4))
        sleep_file.write(str(round((int(sleep_reading.get(),16)*LSB)/float(sense_resistor.get()),4)))
        sleep_file.write('\n')
      root.update()
      counter1 = time.clock()-offset1
      cntr1.set(counter1)
      profile_frame.update()

   sleep_file.close()

   cmd = 'y'
   bytes_returned = ser.write(cmd.encode())
   
   pb_vd_s.stop()
   pb_vd_s.destroy()
      
   progress_label_s.config(text = 'Complete')
   progress_label_s.config(foreground = 'green')
#   ser.close()

   if batt_chem.get() == 'AA-Alkaline' or batt_chem.get() == 'AAA-Alkaline':
      soc_file = 'AA_AAA.csv'     
   elif batt_chem.get() == 'LI-Ion' or batt_chem.get()=='LiFepo4':
      soc_file = 'LiIon.csv'
   elif batt_chem.get() == 'NiMH/NiCd':
      soc_file = 'NiMH_AA_AAA.csv'
   elif batt_chem.get() == 'Li-Coin':
      soc_file = 'CoinCell.csv'
   elif batt_chem.get() == 'CR123':
      soc_file = 'CR123.csv'
       
   with open(soc_file, 'r')as csvfile:
      inp = csv.reader(csvfile, delimiter = ',')
      headers = next(inp, None)
      headers1= next(inp, None)
      headers2 = next(inp, None)
      my_list = list(inp)

      for row in inp:
         soc.append(int(row[0]))
         ocv.append(float(row[1]))
         esr.append(float(row[2]))

      for i in range(len(my_list)-1):
         if (float(my_list[i][1])) < float(dut_cutoff_optimized_entry_4.get()):
            soc_state=soc_state+1
         new_bat_cap = float(1-(soc_state/100))*float(battery_capactity_entry_1.get())    
              
   #Update Results Step4 data
   global sl_captured_average_current_3, total_event_duration,battery_life_hours, battery_life_days

   sl_captured_average_current_3 = (sum(si)/(len(si)))- lo_offset.get() #Input bias current and Offset voltage calibration
   
   avg_sleep_event_I.configure(text=str(round(sl_captured_average_current_3*1000,1)))
   avg_sleep_event_I.configure(foreground='green')
   avg_sleep_event_I_units.configure(foreground='green')

   total_event_duration = float(sl_duration_entry_3.get()) + ae_captured_duration_2

   average_current_all_events = (sl_captured_average_current_3 * float(sl_duration_entry_3.get()) + (ae_captured_average_current_2*ae_captured_duration_2))/float(total_event_duration)

   #Complete Step 4 Captured Labels
   sl_captured_current_label_4.configure(text=str(round(float(sl_captured_average_current_3),4)), foreground='black',background='dark gray')
   sl_captured_duration_label_4.configure(text=str(round(float(sl_duration_entry_3.get()),4)), foreground='black',background='dark gray')
   average_current_profile_captured_label_4.configure(text=str(round(average_current_all_events,4)),foreground='blue',background='dark gray')
   batt_cap_captured_label_4.configure(text=str(int(new_bat_cap)), foreground='black',background='dark gray')

   #Copy Step 4 Captured Labels to Optimized Entrys
   sl_optimized_current_entry_4.insert(0,str(round(float(sl_captured_average_current_3),4)))
   sl_optimized_duration_entry_4.insert(0,str(round(float(sl_duration_entry_3.get()),4)))
   average_current_profile_optimized_label_4.configure(text=str(round(average_current_all_events,4)),foreground='blue',background='dark gray')
   batt_cap_optimized_entry_4.insert(0,str(int(new_bat_cap)))

   si.clear()

   #Calculate Captured Battery Life Hours

   battery_life_hours =  float(new_bat_cap)/float(average_current_all_events)                                 
   battery_life_days = float(battery_life_hours/24)
                                       
   captured_battery_life_hours_graph.configure(text=str(round(float(battery_life_hours),2)),foreground='blue',background='dark gray')
   captured_battery_life_days_graph.configure(text=str(round(float(battery_life_days),2)),foreground='blue',background='dark gray')

   optimized_battery_life_hours_graph.configure(text=str(round(float(battery_life_hours),2)),foreground='blue',background='dark gray')
   optimized_battery_life_days_graph.configure(text=str(round(float(battery_life_days),2)),foreground='blue',background='dark gray')                                

   filemenu.entryconfigure(4, state=tk.NORMAL)

   step3_label.configure(foreground='black')
   step4_label.configure(foreground='blue')
   

#################################################################################
###    STEP4 OPTIMIZED RESULTS 
#################################################################################
def optimize_profile():
   global optimized_battery_life_hours, optimized_battery_life_days, optimized_average_current_all_events

   soc_state = 0
   
   if batt_chem.get() == 'AA-Alkaline' or batt_chem.get() == 'AAA-Alkaline':
      soc_file = 'AA_AAA.csv'     
   elif batt_chem.get() == 'LI-Ion' or batt_chem.get()=='LiFepo4':
      soc_file = 'LiIon.csv'
   elif batt_chem.get() == 'NiMH/NiCd':
      soc_file = 'NiMH_AA_AAA.csv'
   elif batt_chem.get() == 'Li-Coin':
      soc_file = 'CoinCell.csv'
   elif batt_chem.get() == 'CR123':
      soc_file = 'CR123.csv'
    
      
   with open(soc_file, 'r')as csvfile:
      inp = csv.reader(csvfile, delimiter = ',')
      headers = next(inp, None)
      headers1= next(inp, None)
      headers2 = next(inp, None)
      my_list = list(inp)

      for row in inp:
         soc.append(int(row[0]))
         ocv.append(float(row[1]))
         esr.append(float(row[2]))

      for i in range(len(my_list)-1):
         if (float(my_list[i][1])) < float(dut_cutoff_optimized_entry_4.get()):
            soc_state=soc_state+1
         new_bat_cap = float(1-(soc_state/100))*float(battery_capactity_entry_1.get())    

   batt_cap_optimized_entry_4.delete(0,END)           
   batt_cap_optimized_entry_4.insert(0,str(int(new_bat_cap)))
   optimized_average_current_all_events = (float(sl_optimized_duration_entry_4.get())* float(sl_optimized_current_entry_4.get()) + (float(ae_optimized_duration_entry_4.get())*float(ae_optimized_current_entry_4.get())))/(float(sl_optimized_duration_entry_4.get()) + float(ae_optimized_duration_entry_4.get()))

   average_current_profile_optimized_label_4.configure(text=str(round(float(optimized_average_current_all_events),4)),foreground='blue',background='dark gray')

   #battery_life_hours = capacity in mAH / mA
   optimized_battery_life_hours =  float(new_bat_cap)/float(optimized_average_current_all_events)
   optimized_battery_life_days = float(optimized_battery_life_hours/24)

   optimized_battery_life_hours_graph.configure(text=str(round(float(optimized_battery_life_hours),2)),foreground='blue',background='dark gray')
   optimized_battery_life_days_graph.configure(text=str(round(float(optimized_battery_life_days),2)),foreground='blue',background='dark gray')

   filemenu.entryconfigure(4, state=tk.NORMAL)
   
 
#################################################################################
###    RESET
#################################################################################

def reset():

    #Turn off low current sense resistor
    cmd = 'l'
    bytes_returned = ser.write(cmd.encode())
         
    optimize_button.configure(state=tk.NORMAL)

    capture_active_event_button.configure(state=tk.NORMAL)
    psu_combo_box.configure(state=tk.NORMAL)
    trigger_box.config(state=tk.NORMAL)
    battery_chemistry_combo_box.configure(state=tk.NORMAL)
    battery_cells_combo_box.configure(state=tk.NORMAL)

    cmd = 'i' #turn voltage off
    bytes_returned = ser.write(cmd.encode())
                                                
    p_rad.configure(value=1,foreground='black',background='dark gray')
    p_rad.deselect()
    p_rad1.configure(value=0,foreground='red',background='dark gray')
    p_rad1.select()

    capture_active_event_button.config(text = 'Capture Active I' )

    #offset = 0
    x[:] = []
    y[:] = []
    si[:] = []

    ax.plot(x, y)
    ax.cla()
   # plt.close()
     
    ae_captured_average_current_2 = 0
    sl_captured_average_current_3 = 0
    ae_captured_duration_2 = 0
    soc_state = 0

    #Clear all of the Labels and Entry Fields
    ae_captured_current_label_4.configure(text='-',background='dark gray')
    ae_captured_duration_label_4.configure(text='-',background='dark gray')
    sl_captured_current_label_4.configure(text='-',background='dark gray')
    sl_captured_duration_label_4.configure(text='-',background='dark gray')
    dut_cutoff_captured_label_4.configure(text='-',background='dark gray')
    batt_cap_captured_label_4.configure(text='-',background='dark gray')
    average_current_profile_captured_label_4.configure(text='-',background='dark gray')
    captured_battery_life_hours_graph.configure(text='-',background='dark gray')
    captured_battery_life_days_graph.configure(text='-',background='dark gray')

    ae_optimized_current_entry_4.delete(0,END)
    ae_optimized_duration_entry_4.delete(0,END)
    dut_cutoff_optimized_entry_4.delete(0,END)
    batt_cap_optimized_entry_4.delete(0,END)
    sl_optimized_current_entry_4.delete(0,END)
    sl_optimized_duration_entry_4.delete(0,END)
    sl_optimized_current_entry_4.delete(0,END)
    sl_optimized_duration_entry_4.delete(0,END)

    average_current_profile_optimized_label_4.configure(text='')

    optimized_battery_life_hours_graph.configure(text='')
    optimized_battery_life_days_graph.configure(text='')

    avg_active_event_I_2.configure(text='0.00', foreground = 'black')
    avg_active_event_I_units.configure(foreground = 'black')
    avg_sleep_event_I.configure(text='0000', foreground = 'black')
    avg_sleep_event_I_units.configure(foreground = 'black')
    
    
#################################################################################
###    RESET GRAPH ONLY
#################################################################################
def reset_graph():
  x[:] = []
  y[:] = []
  si[:] = []
  ax.plot(x, y)
  ax.cla()
  plt.close()

#################################################################################
###    GET CONFIG
#################################################################################
#def get_config():
   #try:
     #  ser = serial.Serial(com_port, baud_rate, timeout=None)
   #except SerialException:
    #    print('Port is busy')
#
  # cmd = 'm'
 #  bytes_returned = ser.write(cmd.encode())
  # data.set(ser.readline(2).hex())
 #  print('MFR CAL ',data.get())
 #  data.set(ser.readline(2).hex())
 #  print('ADC CONFIG ',data.get())
  # ser.close()
   
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
battery_chemistry_combo_box = ttk.Combobox(profile_frame, width=12, textvariable=batt_chem)
battery_chemistry_combo_box['values'] = ('AA-Alkaline', 'AAA-Alkaline', 'LI-Ion','LiFepo4','NiMH/NiCd', 'Li-Coin','CR123') 
battery_chemistry_combo_box.grid(row=5, column=0,padx=(150,4),sticky = 'w')
battery_chemistry_combo_box.current(0)
battery_chemistry_combo_box.bind('<<ComboboxSelected>>', set_voltage)

battery_cells = Label(profile_frame, text='Number of Cells',background='dark gray')
battery_cells.grid(row=6, column=0, padx=10,pady=2,sticky = 'w')
batt_cells = tk.StringVar()
battery_cells_combo_box = ttk.Combobox(profile_frame, width=8, textvariable=batt_cells)
battery_cells_combo_box['values'] = (1, 2, 3) 
battery_cells_combo_box.grid(row=6, column=0,padx=(150,4),sticky = 'w')
battery_cells_combo_box.current(0)
battery_cells_combo_box.bind('<<ComboboxSelected>>', set_voltage)

#Voltage
dut_cuttoff_voltage = Label(profile_frame, text='DUT Cutoff Voltage',background='dark gray')
dut_cuttoff_voltage.grid(row=7, column=0, padx=10,pady=2,sticky = 'w')
dut_cutoff_voltage_entry = Entry(profile_frame, width=8)
dut_cutoff_voltage_entry.grid(row=7, column=0, padx=(150,4), sticky = 'w')
dut_cutoff_voltage_entry.focus_set()
dut_cutoff_voltage_entry.insert(0,0.9)
dut_cuttoff_voltage_label = Label(profile_frame, text='volts',background='dark gray')
dut_cuttoff_voltage_label.grid(row=7, column=0, padx=(210,4),pady=2,sticky = 'w')

volt_lab = Label(profile_frame, text='PSU Voltage Output',background='dark gray')
volt_lab.grid(row=8, column=0, padx=10,pady=2,sticky = 'w')
voltage = tk.StringVar()
psu_combo_box = ttk.Combobox(profile_frame, width=5, textvariable=voltage)
psu_combo_box['values'] = (1.2, 1.5, 2.4, 3.0, 3.6, 3.7, 4.2, 4.5) 
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
rt_c = Label(profile_frame, text='Capture Duration (s)',background='dark gray')
rt_c.grid(row=11, column=0, padx=10,pady=2,sticky = 'w')
rt_dur = Entry(profile_frame, width=6)
rt_dur.grid(row=11, column=0, padx=(130,4), sticky = 'w')
rt_dur.focus_set()
rt_dur.insert(0,1)

choice_lab = Label(profile_frame, text=' -OR- ',background='dark gray')
choice_lab.grid(row=11, column=0, padx=(170,2),pady=2,sticky = 'w')

trig_var = IntVar()
trigger_box = tk.Checkbutton(profile_frame, text='Ext Trig', variable=trig_var,background='dark gray', command=TrigArmed,state=tk.DISABLED)
trigger_box.grid(row=11, column=0, padx=(205,4),pady= 2,sticky='w')

trig_label = ttk.Label(profile_frame, text='', background='dark gray')
trig_label.grid(row=11, column = 0, padx=(200,4),sticky='w')

capture_active_event_button = tk.Button(profile_frame,text='Capture Active I',command=capture_profile,state=tk.DISABLED)
capture_active_event_button.grid(row=12,column=0, padx=(10,4),pady= 2,sticky = 'w')
avg_active_event_I_2 = ttk.Label(profile_frame, text='0.00',font=('Arial Bold',10), foreground = 'black',background='dark gray',state=tk.DISABLED)
avg_active_event_I_2.grid(row=12, column = 0, padx= (120,4),pady= 2, sticky = 'w')
avg_active_event_I_units = ttk.Label(profile_frame, text='mA',font=('Arial Bold',10), foreground = 'black',background='dark gray',state=tk.DISABLED)
avg_active_event_I_units.grid(row=12, column = 0, padx=(170,4),pady= 2, sticky = 'w')

#STEP3 - CAPTURE SLEEP EVENT CURRENT WIDGETS

sl_duration_labe1_3 = Label(profile_frame, text='Enter Sleep Duration',background='dark gray')
sl_duration_labe1_3.grid(row=14, column=0, padx=10,pady=2,sticky = 'w')
sl_duration_entry_3 = Entry(profile_frame, width=10)
sl_duration_entry_3.grid(row=14, column=0,padx=(130,4),sticky = 'w')
sl_duration_entry_3.insert(0,4250)
sl_duration_units_lab_3 = Label(profile_frame, text='S',background='dark gray')
sl_duration_units_lab_3.grid(row=14, column=0, padx=(200,2),pady=4,sticky = 'w')

capture_sleep_btn_3 = tk.Button(profile_frame,text='Capture Sleep I',command=capture_sleep_profile,state=tk.NORMAL)
capture_sleep_btn_3.grid(row=15,column=0, padx=(10,4),pady= 2,sticky = 'w')

avg_sleep_event_I = ttk.Label(profile_frame, text='0000',font=('Arial Bold',10), foreground = 'black',background='dark gray',state=tk.DISABLED)
avg_sleep_event_I.grid(row=15, column = 0, padx= (120,4),pady= 2, sticky = 'w')

avg_sleep_event_I_units = ttk.Label(profile_frame, text='uA',font=('Arial Bold',10), foreground = 'black',background='dark gray')
avg_sleep_event_I_units.grid(row=15, column = 0, padx=(170,4),pady= 2, sticky = 'w')

#STEP4 - RESULTS AND OPTIMIZE  WIDGETS
#Section 4 Fields

#Profile Headers
captured_profile_label = ttk.Label(profile_frame, text='Captured' ,foreground='black',background='dark gray')
captured_profile_label.grid(row=17, column = 0, padx=(150,4),sticky = 'w')

optimized_profile_label = Label(profile_frame, text='Optimized',background='dark gray')
optimized_profile_label.grid(row=17, column=0, padx=(210,1),pady=2,sticky = 'w')

#Active Event Current
ae_current_label_4 = Label(profile_frame, text='Active Event Current',background='dark gray')
ae_current_label_4.grid(row=18, column=0, padx=10,pady=4,sticky = 'w')
ae_captured_current_label_4 = Label(profile_frame, text='-', background='dark gray')
ae_captured_current_label_4.grid(row=18, column=0, padx=(150,4),pady=2,sticky = 'w')
ae_optimized_current_entry_4 = Entry(profile_frame, width=7)
ae_optimized_current_entry_4.grid(row=18, column=0,padx=(210,4),sticky = 'w')
ae_current_units_lab_4 = Label(profile_frame, text='mA',background='dark gray')
ae_current_units_lab_4.grid(row=24, column=0, padx=(260,2),pady=2,sticky = 'w')

#Active Event Duration
ae_duration_label_4 = Label(profile_frame, text='Active Event Duration',background='dark gray')
ae_duration_label_4.grid(row=19, column=0, padx=10,pady=4,sticky = 'w')
ae_captured_duration_label_4 = Label(profile_frame, text='-',background='dark gray')
ae_captured_duration_label_4.grid(row=19, column=0, padx=(150,4),pady=2,sticky = 'w')
ae_optimized_duration_entry_4 = Entry(profile_frame, width=7)
ae_optimized_duration_entry_4.grid(row=19, column=0,padx=(210,4),sticky = 'w')
ae_duration_units_lab_4 = Label(profile_frame, text='S',background='dark gray')
ae_duration_units_lab_4.grid(row=19, column=0, padx=(260,2),pady=2,sticky = 'w')

#Sleep Event Current
sl_current_label_4 = Label(profile_frame, text='Sleep Current',background='dark gray')
sl_current_label_4.grid(row=20, column=0, padx=10,pady=4,sticky = 'w')
sl_captured_current_label_4 = Label(profile_frame, text='-',background='dark gray')
sl_captured_current_label_4.grid(row=20, column=0, padx=(150,4),pady=2,sticky = 'w')
sl_optimized_current_entry_4 = Entry(profile_frame, width=7)
sl_optimized_current_entry_4.grid(row=20, column=0,padx=(210,4),sticky = 'w')
sl_current_units_lab_4 = Label(profile_frame, text='mA',background='dark gray')
sl_current_units_lab_4.grid(row=20, column=0, padx=(260,2),pady=2,sticky = 'w')

#Sleep Event Duration
sl_duration_labe1_4 = Label(profile_frame, text='Sleep Duration',background='dark gray')
sl_duration_labe1_4.grid(row=21, column=0, padx=10,pady=4,sticky = 'w')
sl_captured_duration_label_4 = Label(profile_frame, text='-',background='dark gray')
sl_captured_duration_label_4.grid(row=21, column=0, padx=(150,4),pady=2,sticky = 'w')
sl_optimized_duration_entry_4 = Entry(profile_frame, width=7)
sl_optimized_duration_entry_4.grid(row=21, column=0,padx=(210,4),sticky = 'w')
sl_duration_units_lab_4 = Label(profile_frame, text='S',background='dark gray')
sl_duration_units_lab_4.grid(row=21, column=0, padx=(260,2),pady=2,sticky = 'w')

#DUT Cutoff Voltage
dut_cutoff_label_4 = Label(profile_frame, text='DUT Cutoff Voltage',background='dark gray')
dut_cutoff_label_4.grid(row=22, column=0, padx=10,pady=2,sticky = 'w')
dut_cutoff_captured_label_4 = Label(profile_frame, text='-',background='dark gray')
dut_cutoff_captured_label_4.grid(row=22, column=0, padx=(150,4),pady=2,sticky = 'w')
dut_cutoff_optimized_entry_4 = Entry(profile_frame, width=7)
dut_cutoff_optimized_entry_4.grid(row=22, column=0, padx=(210,4), sticky = 'w')
dut_cutoff_units_lab_4 = Label(profile_frame, text='mAh',background='dark gray')
dut_cutoff_units_lab_4.grid(row=22, column=0, padx=(260,2),pady=2,sticky = 'w')

#Battery Capacity
batt_cap_label_4 = Label(profile_frame, text='Effective Battery Capacity',background='dark gray')
batt_cap_label_4.grid(row=23, column=0, padx=10,pady=2,sticky = 'w')
batt_cap_captured_label_4 = Label(profile_frame, text='-',background='dark gray')
batt_cap_captured_label_4.grid(row=23, column=0, padx=(150,4),pady=2,sticky = 'w')
batt_cap_optimized_entry_4 = Entry(profile_frame, width=7)
batt_cap_optimized_entry_4.grid(row=23, column=0, padx=(210,4), sticky = 'w')
batt_cap_units_lab_4 = Label(profile_frame, text='mAh',background='dark gray')
batt_cap_units_lab_4.grid(row=23, column=0, padx=(260,2),pady=2,sticky = 'w')

#Average Current Profile
average_current_profile_label_4 = Label(profile_frame, text='Average Current Profile',foreground = 'blue',background='dark gray')
average_current_profile_label_4.grid(row=24, column=0, padx=10,pady=2,sticky = 'w')
average_current_profile_captured_label_4 = Label(profile_frame, text='-',background='dark gray')
average_current_profile_captured_label_4.grid(row=24, column=0, padx=(150,4),pady=2,sticky = 'w')
average_current_profile_optimized_label_4 = Label(profile_frame, text='-',background='dark gray')
average_current_profile_optimized_label_4.grid(row=24, column=0, padx=(210,4),pady=4,sticky = 'w')
average_current_profile_units_lab_4 = Label(profile_frame, text='mA',background='dark gray')
average_current_profile_units_lab_4.grid(row=24, column=0, padx=(260,2),pady=2,sticky = 'w')

#Battery Life Hours
batt_life_hours_captured_graph_label = ttk.Label(profile_frame, text='Battery Life (hours) ',foreground = 'blue',background='dark gray')
batt_life_hours_captured_graph_label.grid(row=25, column=0, padx=10, sticky = 'w')
captured_battery_life_hours_graph = ttk.Label(profile_frame, text='-',foreground='blue',background='dark gray')
captured_battery_life_hours_graph.grid(row=25, column = 0,padx=(150,4),sticky = 'w')
optimized_battery_life_hours_graph = ttk.Label(profile_frame, text='-',foreground='blue',background='dark gray')
optimized_battery_life_hours_graph.grid(row=25, column = 0,padx=(210,4),sticky = 'w')

#Battery Life Days
batt_life_days_captured_graph_label = ttk.Label(profile_frame, text='Battery Life (days) ', foreground = 'blue',background='dark gray')
batt_life_days_captured_graph_label.grid(row=26, column = 0,padx=10,sticky = 'w')
captured_battery_life_days_graph = ttk.Label(profile_frame, text='-' ,foreground='blue',background='dark gray')
captured_battery_life_days_graph.grid(row=26, column = 0,padx=(150,4),sticky = 'w')
optimized_battery_life_days_graph = ttk.Label(profile_frame, text='-',foreground='blue',background='dark gray')
optimized_battery_life_days_graph.grid(row=26, column = 0,padx=(210,4),sticky = 'w')

#OPTIMIZE BUTTON
optimize_button = tk.Button(profile_frame,text='Optimize',command=optimize_profile,state=tk.NORMAL)
optimize_button.grid(row=27,column=0, padx=(210,4),pady= 2,sticky = 'w')

##RESET
reset_button = tk.Button(profile_frame,text='Reset All',command=reset,state=tk.NORMAL)
reset_button.grid(row=27,column=0, padx=(150,4),pady= 2,sticky = 'w')

##RESET GRAPH
reset_graph_button = tk.Button(profile_frame,text='Reset Graph',command=reset_graph,state=tk.NORMAL)
reset_graph_button.grid(row=27,column=0, padx=(10,4),pady= 2,sticky = 'w')

#CONFIG BUTTON
#BUTTON = ttk.Button(profile_frame,text='CONFIG',command=get_config,state=tk.NORMAL)
#BUTTON.grid(row=33,column=0, padx=(280,4),pady= 4,sticky = 'w')

#STEP LABELS
step1_label = ttk.Label(profile_frame, text='Step1 - Battery Info and PSU Output',font=('Arial Bold',11), foreground = 'blue',background='dark gray')
step1_label.grid(row=3, column = 0, padx=2,pady=(10,2), sticky = 'w',columnspan=2)

step2_label = ttk.Label(profile_frame, text='Step2 - Active Event',font=('Arial Bold',11), background='dark gray')
step2_label.grid(row=10, column = 0, padx=2,pady=2,sticky = 'w',columnspan=2)

step3_label = ttk.Label(profile_frame, text='Step3 - Sleep Event',font=('Arial Bold',11), background='dark gray')
step3_label.grid(row=13, column = 0, padx=2, pady=2, sticky = 'w')

step4_label = ttk.Label(profile_frame, text='Step4 - Results and Optimization',font=('Arial Bold',11), background='dark gray')
step4_label.grid(row=16, column = 0, padx=2, pady=2, sticky = 'w')

   
root.mainloop()
