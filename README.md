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
# CapCrack API Documentation
 
## Overview
This API is used to crack a WiFi password using a provided handshake and mask. It utilizes the Flask framework for the server and `hashcat` for password cracking. This document provides details about the API endpoint, expected request parameters, and sample responses.
 
## Endpoint
### `POST /crack_wifi`
 
### Description
Attempts to crack a WiFi password using a given handshake and a mask. The handshake is provided in text format, and a mask is used to guide the cracking process.
 
### Request Parameters
- **Content-Type**: `multipart/form-data`
- **handshake** (string, required): The WiFi handshake in text format. This should be provided as form-data.
- **mask** (string, required): The mask used by `hashcat` to crack the password. This should also be provided as form-data.
 
### Response Codes
- **200 OK**: Password successfully cracked.
  ```json
  {
    "cracked_password": "password123"
  }
  ```
- **400 Bad Request**: Missing or invalid input parameters.
  ```json
  {
    "error": "Invalid input, handshake and mask are required"
  }
  ```
- **500 Internal Server Error**: Error writing handshake to file or running `hashcat`.
  ```json
  {
    "error": "Unable to write handshake to file: [error details]"
  }
  ```
- **404 Not Found**: Password could not be cracked or output file was not produced.
  ```json
  {
    "error": "Password not found."
  }
  ```
 
### Example cURL Request
```sh
curl -X POST http://localhost:5000/crack_wifi \
  -F "handshake=WPA*02*ab922a72ebffedac4efecc2728c354fe*b20821f62c1b*febd4519990e*4b394d*5dcaa827b4596e97763ff658bc6be85f4af9a7f3e1122ee3f2534f120e6f3df8*0103007502010a000000000000000000019a1fbae1c887a2d52755464df650c87941b6dc8a81f8f56f1f036a64773de523000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001630140100000fac040100000fac040100000fac020000*02" \
  -F "mask=604?d?d?d?d?d?d?d"
```
 
### Example Postman Request
1. Open Postman and create a new `POST` request.
2. Set the request URL to `http://localhost:5000/crack_wifi`.
3. Under the `Body` tab, select `form-data`.
4. Add the following key-value pairs:
   - **Key**: `handshake` (Type: Text)
     **Value**: `WPA*02*ab922a72ebffedac4efecc2728c354fe*b20821f62c1b*febd4519990e*4b394d*5dcaa827b4596e97763ff658bc6be85f4af9a7f3e1122ee3f2534f120e6f3df8*0103007502010a000000000000000000019a1fbae1c887a2d52755464df650c87941b6dc8a81f8f56f1f036a64773de523000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001630140100000fac040100000fac040100000fac020000*02`
   - **Key**: `mask` (Type: Text)
     **Value**: `604?d?d?d?d?d?d?d`
5. Click `Send` to make the request.
6. You should receive a response similar to the example response below:
```json
{
  "cracked_password": "6049790899"
}
```
 
### Notes
- The handshake should be provided in a format that is understandable by `hashcat`.
- The mask should be a valid input for `hashcat`'s mask attack (`-a 3`).
- Ensure that `hashcat` is installed and available in the system's PATH for the API to work properly.
- The `hashcat` command uses the following options:
  - `-m 22000`: Specifies the hash type for WPA-PBKDF2-PMKID+EAPOL.
  - `-a3`: Specifies the brute-force attack mode.
  - `--potfile-disable`: Disables the potfile, which stores previously cracked passwords.
 
### Error Handling
- The API will return appropriate error messages if the handshake or mask parameters are missing or if `hashcat` encounters an error during execution.
 
## Cleanup
- Temporary files, including `Tocrack.pcap` and `cracked.txt`, are deleted after a successful response to keep the environment clean.
 
## Requirements
- Python 3.11+
- CUDA Toolkit (Optional)
- Flask
- `hashcat` must be installed and accessible via command line. `hashcat-bin` must be included in the `PATH` environment variable.
- Dependencies can be installed via:
  ```sh
  pip install flask
  ```
 
## Running the Server
To run the Flask server on localhost (port 5000):
```sh
python hashcracker.py
```

## 🎥 Watch Demo
Demo available at: [YouTube Link](<https://youtu.be/N35GK8Nmgh8?si=adj23uu5K-eQe1zy>)

# ⚠️ Legal Disclaimer
<p align="center">
  <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExaHhxdDFydXd3Z25xaHJ5NXgza2RwY2ExcGx1ZHd0ZDdvYmxjbG92eiZlcD12MV9pbnRlcm5hbF9naWZzX2dpZklkJmN0PWc/ko7twHhomhk8E/giphy.gif" alt="Binary Code Security GIF" width="400"/>
</p>

**IMPORTANT**: CapCrack is for educational purposes only. Unauthorized use of this tool on networks you do not own or have explicit permission to test is illegal.
