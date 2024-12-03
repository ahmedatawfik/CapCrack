# CapCrack: Automated WPA2-PSK Key Cracking Tool 🚀

CapCrack is a Python-based tool designed to expose vulnerabilities in WPA2-PSK WiFi encryption. It automates handshake capture and brute force cracking using GPU acceleration. The tool features a user-friendly GUI, supports passive monitoring, and enables active deauthentication attacks for handshake acquisition.

---

## 🌟 Features
- **Graphical User Interface (GUI)**: Intuitive PyQt5-based interface for seamless operation.
- **Passive and Active Attacks**:
  - Monitor for natural WPA handshakes (Passive Mode).
  - Force client reconnections with deauthentication packets (Active Mode).
- **Mask-Based Brute Force Cracking**:
  - GPU-accelerated brute force using Hashcat.
  - User-defined masks for targeted cracking.
- **Real-Time Progress Indicators**: Track attack and cracking processes in real-time.
- **Error Handling and Logging**: Robust backend to handle handshake parsing and API communication errors.

---

## 🛠️ Requirements

### Hardware
- A WiFi card capable of monitor mode (e.g., TP-LINK TL-2N722N).
- NVIDIA GPU with CUDA support for GPU-accelerated cracking (e.g., RTX 4070).

### Software
- **OS**: Ubuntu 22.04 or Kali Linux 2024.3 VM recommended.
- **Python 3.9** or above.
- **Required Python Packages**: `PyQt5`, `Flask`, `requests`.
- **System Tools**:
  - Aircrack-ng suite: `airodump-ng`, `aireplay-ng`.
  - Hashcat for GPU acceleration.
  - hcxpcapngtool for handshake processing.

### Install Python Packages:
```bash
pip install PyQt5 flask requests
```
### Setup
```bash
# Clone this repository
git clone https://github.com/yourusername/CapCrack.git
cd CapCrack

# Launch the Flask backend
python3 hashcracker.py

# Launch the GUI tool
python3 gui.py
```
---

# 🚀 How to Use

## Step 1: Refresh Networks
* Click the **Refresh Networks** button in the GUI
* The tool scans for nearby WiFi networks and displays them in a table with:
 * **SSID**: The name of the network
 * **BSSID**: The MAC address of the access point 
 * **Channel**: The frequency channel

🎉 **Result**: A list of available networks is displayed

## Step 2: Monitor for Handshake (Passive Attack) 
* Select a target network from the table
* Click **Monitor for Handshake**
* The tool listens for EAPOL handshake packets from the selected network
* Once the handshake is captured:
 * A confirmation dialog appears
 * You'll be prompted to enter a mask for cracking (e.g., `?d?d?d?d` for numeric passwords)

🎉 **Result**: A handshake file is saved and sent to the cracking backend along with the mask.

## Step 3: Run Deauth Attack (Active Attack)
* Select a target network from the table
* Click **Run Deauth Attack**
* The tool:
 * Sends deauthentication packets to disconnect clients from the network
 * Captures the handshake when clients reconnect

🎉 **Result**: The captured handshake is processed and sent to the cracking backend along with the mask.

## Step 4: Crack the Password
* After capturing the handshake, the tool prompts you to enter a mask for cracking
* Enter the desired mask (e.g., `?d?d?d?d` for numeric passwords of length 4)
* The GUI communicates with the backend (`hashcracker.py`) to run Hashcat
* The cracked password is displayed in a dialog box

🎉 **Result**: The cracked WiFi password is revealed
## 🎥 Watch Demo
Demo available at: [YouTube Link](<https://youtu.be/N35GK8Nmgh8?si=adj23uu5K-eQe1zy>)

# ⚠️ Legal Disclaimer
<p align="center">
  <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHhxdDFydXd3Z25xaHJ5NXgza2RwY2ExcGx1ZHd0ZDdvYmxjbG92eiZlcD12MV9pbnRlcm5hbF9naWZzX2dpZklkJmN0PWc/ko7twHhomhk8E/giphy.gif" alt="Binary Code Security GIF" width="400"/>
</p>

**IMPORTANT**: CapCrack is for educational purposes only. Unauthorized use of this tool on networks you do not own or have explicit permission to test is illegal.
