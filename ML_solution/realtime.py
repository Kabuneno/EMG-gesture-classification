import time
import threading
import os
import csv
import ast
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple
import serial
from serial.tools import list_ports
import tkinter as tk
import umyo_parser
import display_stuff
import numpy as np
import joblib


RECORD_DURATION = 1.0
EMG_CH = 8
SP_CH  = 16
ACC_CH = 3
Q_CH   = 4



port = list(list_ports.comports())
print("available ports:")
for p in port:
    print(p.device)
    if p.device == 'COM5':
        device = p.device
print("===")

# read

ser = serial.Serial(port=device, # serial.Serial() настраивает соединение с устройством
                    baudrate=921600, # 921600 bit per second 
                    parity=serial.PARITY_NONE,# described in copybook
                    stopbits=1,# described in copybook
                    bytesize=8,# described in copybook
                    timeout=0 # described in copybook
                    )

print("conn: " + ser.portstr) # this function  makes a print of the text tyhat you write

display_stuff.plot_init()


is_recording = False
recorded_data_left:  List[dict] = []
recorded_data_right: List[dict] = []
start_time = None

root = None
status_label = None
pred_label = None
start_btn = None

def load_artifacts(model_dir="."):
    clf = joblib.load(os.path.join(model_dir, "model.pkl"))
    le  = joblib.load(os.path.join(model_dir, "label_encoder.pkl"))
    feat_names = json.loads(Path(os.path.join(model_dir, "feature_order.json")).read_text(encoding="utf-8"))
    return clf, le, feat_names

try:
    clf, label_encoder, feature_order = load_artifacts(".")
    # print("[ok] Loaded model artifacts.")
except AttributeError:
    print("NO")

def _clip_or_pad_time_series(X: np.ndarray, T: int) -> np.ndarray:
    #function of cliping I mean reducing 
    if X.shape[0] > T:
        return X[-T:, :]
    if X.shape[0] < T:
        pad = np.zeros((T - X.shape[0], X.shape[1]), dtype=float)
        return np.vstack([X, pad])
    return X

def _recorded_list_to_mats(rec_list: List[dict]) -> Dict[str, np.ndarray]:
    t = len(rec_list)
    emg  = np.zeros((t, EMG_CH), dtype=float)
    sp   = np.zeros((t, SP_CH),  dtype=float)
    acc  = np.zeros((t, ACC_CH), dtype=float)
    quat = np.zeros((t, Q_CH),   dtype=float)
    for i, dp in enumerate(rec_list):
        # emg
        emg[i, :] = np.array(dp.get("emg", [0]*EMG_CH), dtype=float)[:EMG_CH]
        # spectr
        sp[i,  :] = np.array(dp.get("spectr", [0]*SP_CH), dtype=float)[:SP_CH]
        # accel
        acc[i, 0] = float(dp.get("ax", 0))
        acc[i, 1] = float(dp.get("ay", 0))
        acc[i, 2] = float(dp.get("az", 0))
        quat[i, :] = np.array(dp.get("qsg", [0]*Q_CH), dtype=float)[:Q_CH]

    emg = _clip_or_pad_time_series(emg,250)
    sp = _clip_or_pad_time_series(sp,250)
    acc = _clip_or_pad_time_series(acc,250)
    quat = _clip_or_pad_time_series(quat,250)
    return {"emg": emg, "spectr": sp, "accel": acc, "quat": quat}

def features_emg(emg: np.ndarray, zero_thr: float = 10.0) -> Dict[str, float]:
    emg = emg - np.median(emg, axis=0, keepdims=True)
    out = {}
    _, C = emg.shape
    for c in range(C):
        x = emg[:, c]
        dx = np.diff(x)
        out[f"emg_{c}_mav"] = float(np.mean(np.abs(x)))
        out[f"emg_{c}_rms"] = float(np.sqrt(np.mean(x**2)))
        out[f"emg_{c}_var"] = float(np.var(x))
        out[f"emg_{c}_wl"]  = float(np.sum(np.abs(dx)))
        zc = np.sum(((x[:-1] * x[1:]) < 0) & (np.abs(dx) > zero_thr))
        out[f"emg_{c}_zc"] = float(zc)
        d2 = np.diff(np.sign(dx))
        ssc = np.sum((np.abs(dx[:-1]) > zero_thr) & (np.abs(dx[1:]) > zero_thr) & (d2 != 0))
        out[f"emg_{c}_ssc"] = float(ssc)

    out["emg_mean_abs_all"] = float(np.mean(np.abs(emg)))
    out["emg_rms_all"] = float(np.sqrt(np.mean(emg**2)))
    out["emg_var_all"] = float(np.var(emg))
    out["emg_wl_all"] = float(np.sum(np.abs(np.diff(emg, axis=0))))
    return out

def features_spectr(sp: np.ndarray, take_bins: int = 4) -> Dict[str, float]:
    F = min(take_bins, sp.shape[1])
    S = sp[:, :F]
    S = np.log1p(np.clip(S, 0, None))
    w = np.ones(F)
    if F == 4:
        w[-1] = 0.3
    Sw = S * w

    out = {
        "sp_mean": float(np.mean(Sw)),
        "sp_max": float(np.max(Sw)),
        "sp_med": float(np.median(Sw)),
        "sp_energy": float(np.sum(Sw**2)),
    }
    for f in range(F):
        col = Sw[:, f]
        out[f"sp{f}_mean"] = float(np.mean(col))
        out[f"sp{f}_max"]  = float(np.max(col))
        out[f"sp{f}_std"]  = float(np.std(col))
    return out

def features_accel(acc: np.ndarray) -> Dict[str, float]:
    acc = acc / 8129.0
    out = {}
    for i, axis in enumerate("xyz"):
        col = acc[:, i]
        out[f"acc_{axis}_mean"]   = float(np.mean(col))
        out[f"acc_{axis}_std"]    = float(np.std(col))
        out[f"acc_{axis}_rng"]    = float(np.max(col) - np.min(col))
        out[f"acc_{axis}_energy"] = float(np.sum(col**2))
    mag = np.linalg.norm(acc, axis=1)
    out["acc_mag_mean"]   = float(np.mean(mag))
    out["acc_mag_std"]    = float(np.std(mag))
    out["acc_mag_energy"] = float(np.sum(mag**2))

    dacc = np.diff(acc, axis=0)
    dmag = np.linalg.norm(dacc, axis=1)
    out["dacc_mag_mean"] = float(np.mean(dmag))
    out["dacc_mag_std"]  = float(np.std(dmag))
    out["dacc_mag_max"]  = float(np.max(dmag))
    return out

def quat_delta_norms(quat: np.ndarray) -> np.ndarray:
    dq = np.diff(quat, axis=0)
    return np.linalg.norm(dq, axis=1)

def features_quat(quat: np.ndarray) -> Dict[str, float]:
    norms = np.linalg.norm(quat, axis=1, keepdims=True) + 1e-8
    q = quat / norms
    out = {}
    for i, comp in enumerate("wxyz"):
        col = q[:, i]
        out[f"quat_{comp}_mean"] = float(np.mean(col))
        out[f"quat_{comp}_std"]  = float(np.std(col))
        out[f"quat_{comp}_rng"]  = float(np.max(col) - np.min(col))
    dn = quat_delta_norms(q)
    out["quat_dnorm_mean"] = float(np.mean(dn))
    out["quat_dnorm_std"]  = float(np.std(dn))
    out["quat_dnorm_max"]  = float(np.max(dn))
    return out

def extract_features_device(emg, sp, acc, quat, tag: str) -> Dict[str, float]:
    f = {}
    f.update({f"{tag}_{k}": v for k, v in features_emg(emg).items()})
    f.update({f"{tag}_{k}": v for k, v in features_spectr(sp).items()})
    f.update({f"{tag}_{k}": v for k, v in features_accel(acc).items()})
    f.update({f"{tag}_{k}": v for k, v in features_quat(quat).items()})
    return f

def features_from_windows(win1: dict, win2: dict) -> Dict[str, float]:
    emg1, sp1, acc1, q1 = win1["emg"], win1["spectr"], win1["accel"], win1["quat"]
    emg2, sp2, acc2, q2 = win2["emg"], win2["spectr"], win2["accel"], win2["quat"]
    #windows

    f1 = extract_features_device(emg1, sp1, acc1, q1, "d1")
    f2 = extract_features_device(emg2, sp2, acc2, q2, "d2")

    e1 = float(np.sum((emg1 - np.median(emg1, axis=0))**2))
    e2 = float(np.sum((emg2 - np.median(emg2, axis=0))**2))
    f_cross = {
        "emg_energy_d1": e1,
        "emg_energy_d2": e2,
        "emg_energy_diff": e1 - e2
    }
    return {**f1, **f2, **f_cross}

def predict_from_recorded(rec_left: List[dict], rec_right: List[dict]) -> Tuple[str, float, np.ndarray]:
    win1 = _recorded_list_to_mats(rec_left)
    win2 = _recorded_list_to_mats(rec_right)
    feats = features_from_windows(win1, win2)
    x = np.array([feats.get(k, 0.0) for k in feature_order], dtype=float).reshape(1, -1)

    y_proba = clf.predict_proba(x)[0]
    y_idx   = int(np.argmax(y_proba))
    y_lbl   = label_encoder.inverse_transform([y_idx])[0]
    conf    = float(y_proba[y_idx])
    return y_lbl, conf, y_proba

def record_once():
    global is_recording, recorded_data_left, recorded_data_right, start_time

    is_recording = True
    recorded_data_left  = []
    recorded_data_right = []
    # recorded_data=[]
    start_time = time.time()

    last_data_upd = 0
    parse_unproc_cnt = 0

    while is_recording and (time.time() - start_time) < RECORD_DURATION:
        cnt = ser.in_waiting
        if cnt > 0:
            data = ser.read(cnt)
            parse_unproc_cnt = umyo_parser.umyo_parse_preprocessor(data)
            devices = umyo_parser.umyo_get_list()
            if devices:
                dat_id = display_stuff.plot_prepare(devices)

                d_diff = 0
                if dat_id is not None:
                    d_diff = dat_id - last_data_upd
                if d_diff > 2 + parse_unproc_cnt / 200:
                    display_stuff.plot_cycle_tester()
                    last_data_upd = dat_id

                for dev in devices[:2]:
                    if dev.unit_id == 1286463055:
                        recorded_data_left.append({
                            "timestamp": time.time() - start_time,
                            "emg": list(dev.data_array[:dev.data_count]),
                            "spectr": list(dev.device_spectr),
                            "ax": dev.ax, "ay": dev.ay, "az": dev.az,
                            "qsg": list(dev.Qsg)
                        })
                    elif dev.unit_id == 2060315505:
                        recorded_data_right.append({
                            "timestamp": time.time() - start_time,
                            "emg": list(dev.data_array[:dev.data_count]),
                            "spectr": list(dev.device_spectr),
                            # "ax": {dev.ax, "ay": dev.ay, "az": dev.az},
                            "ax": dev.ax, "ay": dev.ay, "az": dev.az,
                            "qsg": list(dev.Qsg)
                        })
                    else:
                        print('something really bad')
        time.sleep(0.001)

    is_recording = False
    return recorded_data_left, recorded_data_right


# print(' EVERYTHING IS WORKINNNNNNNNNNG')
def on_start_click():
    start_btn.config(state="disabled")
    status_label.config(text="Recording 1.0s ...")
    pred_label.config(text="")

    def worker():
        try:
            rec_l, rec_r = record_once()
            if len(rec_l) == 0:
                rec_l = [{"emg":[0]*EMG_CH,"spectr":[0]*SP_CH,"ax":0,"ay":0,"az":0,"qsg":[0]*Q_CH} for _ in range(250)]
            if len(rec_r) == 0:
                rec_r = [{"emg":[0]*EMG_CH,"spectr":[0]*SP_CH,"ax":0,"ay":0,"az":0,"qsg":[0]*Q_CH} for _ in range(250)]

            label, conf, proba = predict_from_recorded(rec_l, rec_r)
            txt = f"PREDICTION: {label} "
            print(txt)
            root.after(0, lambda: pred_label.config(text=txt))
        except Exception as e:
            # print("[ERR] Prediction failed:", e)
            # root.after(0, lambda: pred_label.config(text=f"Error: {e}"))
            print("HRLD")
        finally:
            root.after(0, lambda: status_label.config(text="Ready"))

            root.after(0, lambda: start_btn.config(state="normal"))

    th = threading.Thread(target=worker, daemon=True)
    th.start()

def build_gui():
    global root, status_label, pred_label, start_btn
    root = tk.Tk()
    root.title("uMyo — Realtime Gesture Classifier")
    root.geometry("520x240")

    title = tk.Label(root, text="Realtime EMG/IMU Gesture (1s window)", font=("Arial", 14))
    title.pack(pady=10)

    status_label = tk.Label(root, text="Ready", font=("Arial", 12))
    status_label.pack()

    pred_label = tk.Label(root, text="", font=("Arial", 12), fg="blue")
    pred_label.pack(pady=10)

    start_btn = tk.Button(root, text="Start / Continue", width=20, command=on_start_click)
    start_btn.pack(pady=10)

    info = tk.Label(root, text="Do a gesture after pressing Start.\nThe system records ~1s, then predicts and stops.", font=("Arial", 10))
    info.pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    build_gui()
