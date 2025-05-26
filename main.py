import tkinter as tk
import tkinter.ttk as ttk
import serial.tools.list_ports
import serial

command = []

ports = serial.tools.list_ports.comports()
serialObj = serial.Serial()

def serial_ports():
    return serial.tools.list_ports.comports()

def on_select(event=None):
    serialObj.port = cb.get().split(' ')[0]
    serialObj.baudrate = 9600
    serialObj.open()

root = tk.Tk()
# configure root
root.title("Jfs Besta")
root.geometry('800x500+300+300')
root.columnconfigure(0, weight=1)
root.rowconfigure(1, weight=1)

port = tk.IntVar()

label = ttk.Label(root, text='Port:')
label.grid(row=0, column=0, sticky='e', padx=(10,2), pady=5)
cb = ttk.Combobox(root, values=serial_ports())
cb.grid(row=0, column=1, sticky="w", padx=(2,10), pady=5)
cb.bind('<<ComboboxSelected>>', on_select)

txt = tk.Text(root)
txt.grid(row=1, column=0, columnspan=2, sticky='ewns')
scb = tk.Scrollbar(root)
scb.grid(row=1, column=2, sticky='ns')
scb.config(command=txt.yview)
txt.config(yscrollcommand=scb.set)
txt.tag_configure('small', font=('Verdana', 8), foreground='black')

portlbl = ttk.Label(root, textvariable=port, background='grey', font='none 24 bold')
portlbl.config(anchor=tk.CENTER)
portlbl.grid(row=0, column=2, sticky='nsew')

left = ttk.LabelFrame(root, text='Commands')
left.grid(row=1, column=2, sticky='ne')

class Callback:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def __call__(self):
        self.func(*self.args, **self.kwargs)

def default_callback(i):
    cmd = [0x2A, 0x01, 0x01, 0x00, 0x02]
    cmd[2] = i
    cmd[4] = i + 1
    command.append(cmd)
    command.append([0x2A, 0x01, 90, 0x00, 91])  # get position

for i in range(1, 7):
    btn = ttk.Button(left, text=f'Goto {i}', command=Callback(default_callback, i))
    btn.grid(row=i-1, column=2)

ttk.Button(left, text='up', command=Callback(default_callback, 70)).grid(row=8, column=2)
ttk.Button(left, text='down', command=Callback(default_callback, 71)).grid(row=9, column=2)
ttk.Button(left, text='Position', command=Callback(default_callback, 90)).grid(row=10, column=2)
ttk.Button(left, text='Aus', command=Callback(default_callback, 76)).grid(row=11, column=2)

def checkcommand(x):
    i = x[2]
    if i <= 6:
        return f'Goto Port {i} ->'
    if i == 70:
        return 'up ->'
    if i == 71:
        return 'down ->'
    if i == 90:
        return 'Position :'
    if i == 76:
        return 'Ausschalten '

def checkdone(x):
    i = x[2]
    if i == 255:
        return "."
    if i == 250:
        return "Falscher Befehl\n"
    if i == 245:
        return "Gerät in Störung\n"
    if i <= 6:
        port.set(i)
        return f' {i} \n'

weiter = True

def checkSerialPort():
    global weiter
    if serialObj.isOpen() and serialObj.in_waiting:
        inp = serialObj.read(size=4)
        txt.insert(tk.END, checkdone(inp))
        weiter = True
    if (len(command) > 0) and (weiter == True):
        if serialObj.isOpen():
            x = command.pop(0)
            txt.insert(tk.END, checkcommand(x), 'small')
            serialObj.write(bytes(x))
            weiter = False
        else:
            txt.insert('0.1', 'Kein Port geöffnet !!!\n')
            command.clear()

def periodic_serial_check():
    checkSerialPort()
    root.after(50, periodic_serial_check)  # alle 50 ms prüfen

periodic_serial_check()
root.mainloop()