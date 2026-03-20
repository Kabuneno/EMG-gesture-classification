import umyo_parser
import display_stuff
import serial
from serial.tools import list_ports
import tkinter as tk

port = list(list_ports.comports())
print("available ports:")


print("available ports:")
for p in port:
    print(p.device)
    if p.device == 'COM5':
        device = p.device
print("===")



ser = serial.Serial(port=device, # serial.Serial() sets th connection with devices
                    baudrate=921600, # 921600 bit per second 
                    parity=serial.PARITY_NONE,# described in copybook
                    stopbits=1,# described in copybook
                    bytesize=8,# described in copybook
                    timeout=0 # described in copybook
                    )

print("conn: " + ser.portstr) # this function  makes a print of the text tyhat you write
last_data_upd = 0

# plot_emg = [0] * 2000
# plot_spg = [0] * 200 * 4
# plot_ax = [0] * 200
# plot_ay = [0] * 200
# plot_az = [0] * 200
# plot_Q = [0] * 200 * 4 
display_stuff.plot_init()







#===========GPT CODE for keys thorugh gui

key_to_gesture = {
    'a': 'swipe up',
    's': 'swipe down',
    'z': 'swipe left',
    'x': 'swipe right',
    'c': 'left mbutton',
    'v': 'left mbutton twice',
    'b': 'right mbutton',
    'n': 'scroll mode',
    'm': 'scroll mode off'
}

def create_gui_k():
    global root, status_label
    
    root = tk.Tk()
    root.geometry("500x400")
    root.title("Gesture Recorder - Keyboard Controls")
    
    instruction_frame = tk.Frame(root)
    instruction_frame.pack(pady=10)
    
    instructions = tk.Label(instruction_frame, text="Keyboard Controls:\na: swipe up\ns: swipe down\nz: swipe left\nx: swipe right\nc: left mbutton\nv: left mbutton twice\nb: right mbutton\nn: scroll mode\nm: scroll mode off", 
                           justify=tk.LEFT, font=("Arial", 12))
    instructions.pack()
    
    status_label = tk.Label(root, text="Ready to record", font=("Arial", 14))
    status_label.pack(pady=20)
    
    for key in key_to_gesture:
        root.bind(f'<KeyPress-{key}>', lambda event, g=key_to_gesture[key]: start_recording(g))
    
    exit_btn = tk.Button(root, text="Exit", command=root.quit, width=15)
    exit_btn.pack(pady=10)

    root.focus_set()
    
    root.mainloop()


# def create_gui():
#     global root, status_label
    
#     root = tk.Tk()
#     root.geometry("400x300")
    
#     button_frame = tk.Frame(root)
#     button_frame.pack(pady=20)
    
#     gestures = [
        # 'swipe up',
        # 'swipe down',
        # 'swipe left',
        # 'swipe right',
        # 'left mbutton',
        # 'left mbutton twice',
        # 'right mbutton',
        # 'scroll mode',
        # 'scroll mode off'
#     ]
    
#     for i, gesture in enumerate(gestures):
#         btn = tk.Button(button_frame, text=gesture, width=15,
#                        command=lambda g=gesture: start_recording(g))
#         btn.grid(row=i//2, column=i%2, padx=5, pady=5)

#     status_label = tk.Label(root, text="ready rec", font=("Arial", 14))
#     status_label.pack(pady=20)
    
#     exit_btn = tk.Button(root, text="exit", command=root.quit, width=15)
#     exit_btn.pack(pady=10)
    
#     root.mainloop()



























import time
import threading

is_recording = False
recorded_data = []
recorded_data_2=[]
current_gesture = None
start_time = None

def start_recording(gesture_name):
    global is_recording, recorded_data, current_gesture, start_time
    
    if is_recording:
        return
    
    current_gesture = gesture_name
    is_recording = True
    recorded_data = []
    start_time = time.time()
    
    status_label.config(text=f"recording {gesture_name}")
    
    record_thread = threading.Thread(target=record_data_1)
    record_thread.daemon = True
    record_thread.start()


def record_data_1():
    global is_recording, recorded_data, start_time , recorded_data_2
    
    last_data_upd = 0
    parse_unproc_cnt = 0
    
    while is_recording and (time.time() - start_time) < 1:
        cnt = ser.in_waiting
        if cnt > 0:
            data = ser.read(cnt)
            parse_unproc_cnt = umyo_parser.umyo_parse_preprocessor(data)

            devices = umyo_parser.umyo_get_list()
            if devices:
                # print(len(devices))
                dat_id = display_stuff.plot_prepare(devices)
                
                d_diff = 0
                if not (dat_id is None):
                    d_diff = dat_id - last_data_upd
                if d_diff > 2 + parse_unproc_cnt / 200:
                    display_stuff.plot_cycle_tester()
                    last_data_upd = dat_id
                

                # LEFT DATA GETTING
                
                if devices[0].unit_id == 1286463055:
                    # print("DATA FOR 1286463055 LEFT")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             
                    # print("left is in 0")
                    # device_data = devices[1]
                    device_data = devices[0]
                    # print(device_data.device_spectr, 'LEFT')
                    recorded_data.append({
                        'timestamp': time.time() - start_time,
                        'emg': list(device_data.data_array[:device_data.data_count]),
                        'spectr': list(device_data.device_spectr),
                        'ax': device_data.ax,
                        'ay': device_data.ay,
                        'az': device_data.az,
                        'qsg': list(device_data.Qsg)
                    })
                if devices[1].unit_id == 1286463055:
                    # print("DATA FOR 1286463055 LEFT")
                    # print("left is in 1")
                    # device_data = devices[2]
                    device_data = devices[1]
                    # print(device_data.Qsg)
                    # print(device_data.device_spectr, 'LEFT')
                    recorded_data.append({
                        'timestamp': time.time() - start_time,
                        'emg': list(device_data.data_array[:device_data.data_count]),
                        'spectr': list(device_data.device_spectr),
                        'ax': device_data.ax,
                        'ay': device_data.ay,
                        'az': device_data.az,
                        'qsg': list(device_data.Qsg)
                    })
                



                               



                # RIGHT DATA GETTING
                                                                                                                                                                                                                                                                                                                                                                     
                if devices[0].unit_id == 2060315505:
                    # print('DATA FOR 2060315505 RIGHT')
                    # print("right is in 0")
                    device_data_2 = devices[0]
                    # print(device_data_2.device_spectr, 'RIGHT')
                    recorded_data_2.append({
                        'timestamp': time.time() - start_time,
                        'emg': list(device_data_2.data_array[:device_data_2.data_count]),
                        'spectr': list(device_data_2.device_spectr),
                        'ax': device_data_2.ax,
                        'ay': device_data_2.ay,
                        'az': device_data_2.az,
                        'qsg': list(device_data_2.Qsg)
                    })
                if devices[1].unit_id == 2060315505:
                    # print('DATA FOR 2060315505 RIGHT')
                    # print("right is in 1")
                    device_data_2 = devices[1]
                    # print(device_data_2.Qsg)
                    # print(device_data_2.device_spectr, 'RIGHT')
                    
                    recorded_data_2.append({
                        'timestamp': time.time() - start_time,
                        'emg': list(device_data_2.data_array[:device_data_2.data_count]),
                        'spectr': list(device_data_2.device_spectr),
                        'ax': device_data_2.ax,
                        'ay': device_data_2.ay,
                        'az': device_data_2.az,
                        'qsg': list(device_data_2.Qsg)
                    })

        time.sleep(0.001) 

    is_recording = False
    save_data()
    
    root.after(0, lambda: status_label.config(text="ready rec"))

import csv 
num_of_samples = 250 

def save_data():
    if not recorded_data or not current_gesture:
        return
    
    all_emg = []
    all_spectr=[]
    all_accel=[]
    all_quat =[]

    some_emg_count = 0 
    for data_point in recorded_data:
        some_emg_count +=len(data_point['emg'])
        all_emg.append(data_point['emg'])
        # print(data_point['emg'])


        all_spectr.append(data_point['spectr'])
        all_accel.append([data_point['ax'], data_point['ay'], data_point['az']])
        # print(len(data_point['ax']),'AX LEN' )


        all_quat.append(data_point['qsg'])
        # print(data_point['qsg'])
    # print(some_emg_count,'EMG')
    
    if len(all_emg) > num_of_samples:
        all_emg = all_emg[:num_of_samples]
    elif len(all_emg) < num_of_samples:
        all_emg.extend([0] * (num_of_samples - len(all_emg)))
    if len(all_spectr) > num_of_samples:
        all_spectr = all_spectr[:num_of_samples]
    elif len(all_spectr) < num_of_samples:
        all_spectr.extend([0] * (num_of_samples - len(all_spectr)))

    if len(all_accel) > num_of_samples:
        all_accel = all_accel[:num_of_samples]
    elif len(all_accel) < num_of_samples:
        all_accel.extend([0] * (num_of_samples - len(all_accel)))

    if len(all_quat) > num_of_samples:
        all_quat = all_quat[:num_of_samples]
    elif len(all_quat) < num_of_samples:
        all_quat.extend([0] * (num_of_samples - len(all_quat)))
    

    row = [f'{current_gesture}']
    # print('LEFT')
    # for i in range(250):
    #     print(all_quat[i])

    row.extend(list(all_emg))
    # print(len(list(all_emg)), "EMG")
    row.extend(list(all_spectr))
    # print(len(list(all_spectr)), "SPECTR")
    row.extend(list(all_accel))
    # print(len(list(all_accel)), "ACCEL")
    row.extend(list(all_quat))
    # print(len(list(all_quat)), "QUAT")


    all_emg = []
    all_spectr = []
    all_accel = []
    all_quat = []
    some_emg_count = 0 
    for data_point in recorded_data_2:
        some_emg_count +=len(data_point['emg'])
        all_emg.append(data_point['emg'])

        all_spectr.append(data_point['spectr'])
        all_accel.append([data_point['ax'], data_point['ay'], data_point['az']])
        all_quat.append(data_point['qsg'])
    # print(some_emg_count,'EMG')
    if len(all_emg) > num_of_samples:
        all_emg = all_emg[:num_of_samples]
    elif len(all_emg) < num_of_samples:
        all_emg.extend([0] * (num_of_samples - len(all_emg)))
    
    if len(all_spectr) > 250:
        all_spectr = all_spectr[:num_of_samples]
    elif len(all_spectr) < num_of_samples:
        all_spectr.extend([0] * (num_of_samples - len(all_spectr)))

    if len(all_accel) > num_of_samples:
        all_accel = all_accel[:num_of_samples]
    elif len(all_accel) < num_of_samples:
        all_accel.extend([0] * (num_of_samples - len(all_accel)))

    if len(all_quat) > num_of_samples:
        all_quat = all_quat[:num_of_samples]
    elif len(all_quat) < num_of_samples:
        all_quat.extend([0] * (num_of_samples - len(all_quat)))
    
    # print('RIGHT')
    # for i in range(250):
    #     print(all_quat[i])

    row.extend(list(all_emg))
    # print(len(list(all_emg)), "EMG")
    row.extend(list(all_spectr))
    # print(len(list(all_spectr)), "SPECTR")
    row.extend(list(all_accel))
    # print(len(list(all_accel)), "ACCEL")
    row.extend(list(all_quat))
    # print(len(list(all_quat)), "QUAT")


    with open('dataset_gsns_4.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(row)
    
    print(f"saved: {current_gesture}")



import os

if __name__ == "__main__":
    fn = 'dataset_gsns_4.csv'
    file_exists = os.path.isfile(fn)
    if not file_exists:
        header = ['label']
        header.extend([f'emg1_{i}' for i in range(num_of_samples)])
        header.extend([f'spectr1_{i}' for i in range(num_of_samples)])
        header.extend([f'accel_1_{i}' for i in range(num_of_samples)])
        header.extend([f'quat_1_{i}' for i in range(num_of_samples)])

        header.extend([f'emg2_{i}' for i in range(num_of_samples)])
        header.extend([f'spectr2_{i}' for i in range(num_of_samples)])
        header.extend([f'accel_2_{i}' for i in range(num_of_samples)])
        header.extend([f'quat_2_{i}' for i in range(num_of_samples)])

        with open(fn, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)
    
    create_gui_k()

# print(len(plot_emg))