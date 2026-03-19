# 🧠 EMG Gesture Classification Project

## 📌 1. Birth of the Idea

<p align="left">
  <img src="/images/05_whatcomesnext.png" width="220" align="left" style="margin-right:15px;"/>
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
  <img src="/images/image.png" width="300"/>
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
  <img src="/images/umyo_wearable_emg_sensor_components_2.png" width="300"/>
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
  <video src="YOUR_VIDEO_LINK" width="300" controls></video>
</p>

Additionally, a USB receiver base was used to transmit EMG data to a computer.

<p align="center">
  <img src="/images/uMyo_ultimate_base_for_PC_connection.png" width="150"/>
</p>

---

### 🧱 Enclosure Design

The initial setup was fragile and exposed. To improve durability and usability, I designed custom enclosures for:
- EMG sensors
- Battery module
- Wrist mounting system

#### 💻 3D Modeling Process

<p align="center">
  <img src="/images/photo_9_2026-03-18_21-46-55.jpg" width="22%"/>
  <img src="/images/photo_8_2026-03-18_21-46-55.jpg" width="22%"/>
  <img src="/images/photo_7_2026-03-18_21-46-55.jpg" width="22%"/>
  <img src="/images/photo_6_2026-03-18_21-46-55.jpg" width="22%"/>
</p>

After completing the designs in Blender, I 3D printed all components.

<p align="center">
  <img src="images/photo_3_2026-03-18_21-46-55.jpg" width="300"/>
</p>

---

### 🔧 Final Assembly

After assembling all components, the final device looked like this:

<p align="center">
  <video src="YOUR_FINAL_VIDEO" width="350" controls></video>
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

The dataset creation process is fully implemented in:

```bash
dataset_creation.py
```

To record the data, I developed a **GUI-based recording tool**, which allowed me to:

* Press keyboard buttons to label gestures
* Perform gestures simultaneously
* Automatically store synchronized EMG and IMU data

### ✋ Gesture Set

All gestures were performed after forming a fist (activating muscle groups consistently):

* `swipe up` — thumb sliding upward along the index finger
* `swipe down` — thumb sliding downward
* `swipe left` — horizontal movement to the left
* `swipe right` — horizontal movement to the right
* `left mbutton` — single tap with thumb
* `left mbutton twice` — double tap
* `right mbutton` — tap on the opposite side of the index finger
* `scroll mode` — triple tap across different areas
* `scroll mode off` — reverse gesture of scroll mode

Each gesture:

* Lasted **1 second**
* Produced **~250 samples per recording**

### 📦 Dataset Scale

* ⏱️ ~8 hours of recording
* 🔢 ~2000 gesture samples
* 📡 High-frequency EMG + IMU data

The dataset was uploaded to **Hugging Face** (private repository).

---

## 🧠 ML Solution

### 🔍 Feature Engineering

Instead of feeding raw signals directly into a model, I designed a **feature extraction pipeline** to convert time-series sensor data into meaningful numerical representations.

For each EMG channel, the following features were extracted:

* **MAV (Mean Absolute Value)** — signal intensity
* **RMS (Root Mean Square)** — energy estimation
* **Variance** — signal dispersion
* **Waveform Length (WL)** — signal complexity
* **Zero Crossings (ZC)** — frequency characteristics
* **Slope Sign Changes (SSC)** — dynamic behavior

Additionally:

* Global EMG statistics across all channels were computed
* Spectral features were extracted and log-scaled
* Accelerometer features included:

  * Mean, standard deviation, range, energy
  * Magnitude-based features
* Quaternion features captured:

  * Orientation stability
  * Motion dynamics via delta norms

To improve robustness, I also introduced **cross-device features**, such as:

* Energy difference between two sensors

---

### 🌲 Model Selection

For gesture classification, I used a:

```text
Random Forest Classifier
```

#### Why Random Forest?

* Handles **high-dimensional feature spaces** well
* Robust to noise (important for EMG signals)
* Does not require heavy preprocessing or scaling
* Works effectively with **tabular engineered features**
* Provides strong baseline performance without overfitting

The model configuration:

* `n_estimators = 800`
* `max_features = sqrt`
* `class_weight = balanced_subsample`
* Parallelized training (`n_jobs = -1`)

---

### 🏋️ Training Process

The dataset was processed as follows:

1. Feature extraction from raw signals

2. Label encoding of gesture classes

3. Train-test split:

   * 80% training
   * 20% testing
   * Stratified sampling

4. Model training on extracted features

5. Evaluation using:

   * Accuracy score
   * Classification report
   * Confusion matrix

Additionally, **Stratified K-Fold cross-validation** was applied to ensure model stability.

---

### ⚡ Real-Time Gesture Prediction

To enable real-time usage, I implemented a prediction pipeline:

1. Incoming EMG + IMU data is collected in time windows
2. The same feature extraction pipeline is applied
3. Features are aligned using saved feature order
4. The trained model predicts the gesture

```python
predict_from_windows(win1, win2)
```

This allows the system to:

* Process live sensor data
* Classify gestures instantly
* Be integrated into interactive applications

---

### 💾 Model Persistence

To ensure reproducibility and deployment:

* Trained model is saved as:

  ```bash
  model.pkl
  ```
* Label encoder:

  ```bash
  label_encoder.pkl
  ```
* Feature order:

  ```bash
  feature_order.json
  ```

This guarantees consistent predictions between training and real-time inference.

---


