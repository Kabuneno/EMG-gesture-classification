
# 🧠 EMG Gesture Classification Project

---

## 📌 1. Birth of the Idea

<p align="left">
  <img src="/images/05_whatcomesnext.png" width="200" align="left"/>
</p>

Everything started when I discovered *Orion*, an experimental project by Meta. I was deeply impressed by the level of technology involved — a system combining smart glasses, a neural interface wristband, and compact computing.

This project inspired me to attempt building a similar system on my own.

However, after analyzing its components, I realized that the glasses themselves required advanced expertise in optics and hardware engineering. Instead of tackling the most complex part first, I decided to focus on a more achievable and equally exciting component — the **EMG-based wristband**.

<br clear="left"/>

---

## ⚡ 2. EMG Technology

Electromyography (EMG) is a technique used to measure the electrical activity produced by muscles.

When the brain sends signals to muscles, it does so through electrical impulses. These impulses cause muscles to contract and produce movement. EMG sensors are capable of detecting these signals from the surface of the skin.

Different hand gestures involve different muscle groups. As a result, each gesture produces a unique electrical signal pattern.

<p align="center">
  <img src="/images/image.png" width="260"/>
</p>

This makes it possible to:

- Capture EMG signals  
- Process and extract meaningful features  
- Train machine learning models to classify gestures  

Such systems can be applied in:

- Human-computer interaction  
- Gesture-based control systems  
- Assistive technologies  

---

## 🔌 3. Hardware: uMyo Sensors

<p align="center">
  <img src="/images/umyo_wearable_emg_sensor_components_2.png" width="260"/>
</p>

To avoid building EMG hardware from scratch, I explored existing solutions and discovered **uMyo EMG sensors** developed by *uDevices*.

I acquired two uMyo sensors, which provided a reliable and open-source platform for working with EMG signals.

---

## 🛠️ 4. Working with the EMG Environment

### 🔋 Hardware Setup

The system was powered using:

- 1000 mAh Li-Po battery  
- USB-C Li-Po charger (uDevices)  
- JST PH2.0 connectors for wiring  

<p align="center">
  <!-- Replace with YouTube or link -->
  <b>📹 Hardware setup video</b><br>
  YOUR_VIDEO_LINK
</p>

Additionally, a USB receiver base was used to transmit EMG data to a computer.

<p align="center">
  <img src="/images/uMyo_ultimate_base_for_PC_connection.png" width="140"/>
</p>

---

### 🧱 Enclosure Design

The initial setup was fragile and exposed. To improve durability and usability, I designed custom enclosures for:

- EMG sensors  
- Battery module  
- Wrist mounting system  

#### 💻 3D Modeling Process

<p align="center">
  <img src="/images/photo_9_2026-03-18_21-46-55.jpg" width="23%"/>
  <img src="/images/photo_8_2026-03-18_21-46-55.jpg" width="23%"/>
  <img src="/images/photo_7_2026-03-18_21-46-55.jpg" width="23%"/>
  <img src="/images/photo_6_2026-03-18_21-46-55.jpg" width="23%"/>
</p>

After completing the designs in Blender, I 3D printed all components.

<p align="center">
  <img src="/images/photo_3_2026-03-18_21-46-55.jpg" width="260"/>
</p>

---

### 🔧 Final Assembly

After assembling all components, the final device looked like this:

<p align="center">
  <b>📹 Final device demo</b><br>
  YOUR_FINAL_VIDEO
</p>

---

### 💻 Software & Signal Processing

The uMyo sensors come with open-source Python code that enables:

- Raw EMG signal acquisition  
- Signal processing  
- Feature extraction  
- Real-time data visualization  

The main entry point is:

```bash
umyo_testing.py
```
---

# 🤖 5. Machine Learning Pipeline

## 📊 Data Structure Understanding

Before developing any machine learning solution, it was essential to deeply understand the structure of the data produced by the EMG sensors.

As described in `testing_functionality.pdf`, each incoming data packet contains:

* Device metadata (RSSI, packet ID, length, unit identifiers)
* Battery information (pb1, pb2, pb3)
* Raw EMG signal data (constructed from high/low byte pairs across 30+ channels)
* IMU data:

  * Quaternion components (`qw, qx, qy, qz`)
  * Acceleration (`ax, ay, az`)
  * Orientation (`yaw, pitch, roll`)
* Magnetic sensor data

The data is transmitted at a high rate of **921600 bits per second**, enabling real-time signal processing and large-scale dataset creation.

---

## 🧪 Dataset Creation

```bash
dataset_creation.py
```

To record the data, I developed a **GUI-based recording tool**, which allowed me to:

* Label gestures via keyboard
* Perform gestures in real-time
* Store synchronized EMG and IMU data

### ✋ Gesture Set

(All gestures performed after forming a fist)

* `swipe up`
* `swipe down`
* `swipe left`
* `swipe right`
* `left mbutton`
* `left mbutton twice`
* `right mbutton`
* `scroll mode`
* `scroll mode off`

Each gesture:

* Duration: **1 second**
* Samples: **~250 per recording**

### 📦 Dataset Scale

* ⏱️ ~8 hours recording
* 🔢 ~2000 samples
* 📡 High-frequency EMG + IMU

Stored on **Hugging Face (private)**

---

## 🧠 ML Solution

### 🔍 Feature Engineering

* MAV, RMS, Variance
* Waveform Length
* Zero Crossings, SSC
* Spectral features (log-scaled)
* Accelerometer + Quaternion features
* Cross-device energy features

---

### 🌲 Model Selection

```text
Random Forest Classifier
```

**Why:**

* Robust to noisy EMG signals
* Handles high-dimensional features
* No heavy preprocessing required
* Fast and reliable baseline

---

### 🏋️ Training Process

1. Feature extraction
2. Label encoding
3. Train/test split (80/20, stratified)
4. Model training
5. Evaluation:

   * Accuracy
   * Classification report
   * Confusion matrix

---

## ⚡ Real-Time Gesture Prediction

To enable real-time interaction, I implemented `realtime.py`.

### 🔄 Pipeline

1. Stream EMG + IMU data (serial, 921600 baud)
2. Record 1-second window (~250 samples)
3. Preprocess (clip/pad)
4. Extract features (same as training)
5. Predict using trained model

---

### 🖥️ User Interface

<p align="center">
  <img src="YOUR_GUI_SCREENSHOT" width="320"/>
</p>

Workflow:

1. Press **Start**
2. Perform gesture
3. Wait ~1 second
4. Receive prediction

---

### ⚙️ Key Design Decisions

* Shared feature pipeline (train = inference)
* Fixed window size
* Lightweight model (CPU-friendly)
* Threading for smooth GUI

---



