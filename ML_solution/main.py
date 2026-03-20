import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from datasets import load_dataset
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import LabelEncoder
import joblib







def parse_cell(cell, expected_len: int) -> np.ndarray:
    if isinstance(cell, (list, tuple, np.ndarray)):
        arr = np.array(cell, dtype=float).flatten()
    elif isinstance(cell, (int, float)):
        if cell == 0:
            arr = np.zeros(0, dtype=float)
        else:
            arr = np.array([cell], dtype=float)
    elif isinstance(cell, str):
        s = cell.strip()
        if s == "" or s == "0":
            arr = np.zeros(0, dtype=float)
        else:
            try:
                val = ast.literal_eval(s)
                if isinstance(val, (list, tuple)):
                    arr = np.array(val, dtype=float).flatten()
                else:
                    arr = np.zeros(0, dtype=float)
            except Exception:
                arr = np.zeros(0, dtype=float)
    else:
        arr = np.zeros(0, dtype=float)

    out = np.zeros(expected_len, dtype=float)
    n = min(expected_len, arr.size)
    if n > 0:
        out[:n] = arr[:n]
    return out

def assemble_series(sample: dict, prefix: str, vec_len: int) -> np.ndarray:
    mats = []
    for t in range(250):
        mats.append(parse_cell(sample.get(f"{prefix}{t}", "0"), vec_len))
    return np.vstack(mats)  # (T, vec_len)

def features_emg(emg: np.ndarray, zero_thr: float = 10.0) -> Dict[str, float]:
    emg = emg - np.median(emg, axis=0, keepdims=True)  # baseline
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



def extract_features_sample(sample: dict) -> Dict[str, float]:
    emg1  = assemble_series(sample, 'emg1_', 8)
    sp1   = assemble_series(sample, "spectr1_",  16)
    acc1  = assemble_series(sample, 'accel_1_', 3)
    q1    = assemble_series(sample, "quat_1_",   4)

    emg2  = assemble_series(sample, "emg2_", 8)
    sp2   = assemble_series(sample, 'spectr2_', 16)
    acc2  = assemble_series(sample, "accel_2_", 3)
    q2    = assemble_series(sample, "quat_2_", 4)

    f1 = extract_features_device(emg1, sp1, acc1, q1, "d1")
    f2 = extract_features_device(emg2, sp2, acc2, q2, "d2")

    e1 = float(np.sum((emg1 - np.median(emg1, axis=0))**2))
    e2 = float(np.sum((emg2 - np.median(emg2, axis=0))**2))
    f_cross = {
        "emg_energy_d1": e1,
        "emg_energy_d2": e2,
        "emg_energy_diff":e1-e2,
    }

    feats= {**f1, **f2,**f_cross}
    feats["label"] = sample["label"]
    return feats

def load_hf_dataset(name: str = "Kabuneno/EMG_spectr_geture09"):
    ds = load_dataset(name)
    return ds["train"]

def build_feature_table(hf_split, num_proc: int = 1):
    feats = hf_split.map(
        extract_features_sample,
        remove_columns=hf_split.column_names,
        desc="Feature extraction",
        num_proc=num_proc
    )
    feature_names = [c for c in feats.column_names if c != "label"]
    X = np.column_stack([feats[c] for c in feature_names]).astype(float)
    y = np.array(feats["label"], dtype=object)
    return X, y, feature_names

def train_and_eval(X, y, feature_names, save_dir: str = "."):
    le = LabelEncoder()
    y_enc = le.fit_transform(y)

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc
    )

    clf = RandomForestClassifier(
        n_estimators=800,
        max_depth=None,
        max_features="sqrt",
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=42
    )
    clf.fit(X_tr, y_tr)
    y_pred = clf.predict(X_te)

    acc = accuracy_score(y_te, y_pred)
    print(f"\nHoldout accuracy: {acc:.3f} ({acc*100:.1f}%)")
    print("\nClassification report:")
    print(classification_report(y_te, y_pred, target_names=le.classes_))
    print("Confusion matrix:")
    print(confusion_matrix(y_te, y_pred))

    n_splits = min(5, len(np.unique(y_enc)))
    if n_splits >= 2:
        skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
        accs = []

        for tr, te in skf.split(X, y_enc):
            clf.fit(X[tr], y_enc[tr])
            accs.append(accuracy_score(y_enc[te], clf.predict(X[te])))

        # print(f"\nStratified {n_splits}-fold acc: mean={np.mean(accs):.3f}, std={np.std(accs):.3f}")

    Path(save_dir).mkdir(parents=True, exist_ok=True)


    joblib.dump(clf,  os.path.join(save_dir, "model.pkl"))
    joblib.dump(le,   os.path.join(save_dir, "label_encoder.pkl"))


    Path(os.path.join(save_dir, "feature_order.json")).write_text(
        json.dumps(feature_names, ensure_ascii=False, indent=2), encoding="utf-8"
    )

def load_artifacts(model_dir: str = "."):
    clf = joblib.load(os.path.join(model_dir, "model.pkl"))
    le  = joblib.load(os.path.join(model_dir, "label_encoder.pkl"))

    feat_names = json.loads(Path(os.path.join(model_dir, "feature_order.json")).read_text(encoding="utf-8"))
    return clf, le, feat_names

def features_from_windows(win1: dict, win2: dict) -> Dict[str, float]:
    
    emg1, sp1, acc1, q1 = win1["emg"], win1["spectr"], win1["accel"], win1["quat"]
    emg2, sp2, acc2, q2 = win2["emg"], win2["spectr"], win2["accel"], win2["quat"]

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

def predict_from_windows(win1: dict, win2: dict, model_dir: str = ".") -> str:
    clf, le, feat_names = load_artifacts(model_dir)
    feats = features_from_windows(win1, win2)
    x = np.array([feats.get(k, 0) for k in feat_names], dtype=float).reshape(1, -1)
    y = clf.predict(x)[0]
    return le.inverse_transform([y])[0]


def sample_to_windows(sample: dict) -> Tuple[dict, dict]:
    emg1  = assemble_series(sample, 'emg1_', 8)
    sp1   = assemble_series(sample, 'spectr1_', 16)
    acc1  = assemble_series(sample, "accel_1_", 3)
    q1    = assemble_series(sample, "quat_1_", 4)

    emg2  = assemble_series(sample, "emg2_", 8)
    sp2   = assemble_series(sample, "spectr2_", 16)
    acc2  = assemble_series(sample, "accel_2_", 3)
    q2    = assemble_series(sample, "quat_2_", 4)

    win1 = {"emg": emg1, "spectr": sp1, "accel": acc1, "quat": q1}
    win2 = {"emg": emg2, "spectr": sp2, "accel": acc2, "quat": q2}
    return win1, win2

hf_train = load_hf_dataset("Kabuneno/EMG_spectr_geture09")
X, y, feature_names = build_feature_table(hf_train, num_proc=1)
# print(f"X shape: {X.shape}, #classes: {len(set(y.tolist()))}")
train_and_eval(X, y, feature_names, save_dir=".")


# one predict
try:
    idx = 740
    sample = hf_train[idx]
    win1, win2 = sample_to_windows(sample)
    pred = predict_from_windows(win1, win2, model_dir=".")
except Exception as e:
    print("wrong")


# """
#     winX: {
#       "emg": (T,8),
#       "spectr": (T,16),
#       "accel": (T,3),
#       "quat": (T,4)
#     }
# """  features from windows