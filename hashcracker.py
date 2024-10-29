from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/crack_wifi', methods=['POST'])
def crack_wifi():
    # Receive WiFi handshake in text format
    handshake = request.form.get('handshake')
    mask = request.form.get('mask')

    # Validate input
    if not handshake or not mask:
        return jsonify({"error": "Invalid input, handshake and mask are required"}), 400

    # Write handshake to Tocrack.pcap file
    handshake_file_path = 'Tocrack.pcap'
    try:
        with open(handshake_file_path, 'w') as handshake_file:
            handshake_file.write(handshake)
    except IOError as e:
        return jsonify({"error": "Unable to write handshake to file: " + str(e)}), 500

    # Run hashcat command
    hashcat_command = [
        'hashcat.bin',
        '-m', '22000',
        '-a3', handshake_file_path,
        mask,
        '-w', '3'
    ]

    try:
        result = subprocess.run(hashcat_command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Error running hashcat: " + e.stderr}), 500

    # Parse hashcat output to find cracked password (assuming it's in stdout)
    output = result.stdout
    cracked_password = None
    for line in output.splitlines():
        if "Cracked" in line:  # Assuming "Cracked" indicates the password line
            cracked_password = line.split(': ')[-1]

    # Return the cracked password
    if cracked_password:
        return jsonify({"cracked_password": cracked_password}), 200
    else:
        return jsonify({"error": "Password not found."}), 404

if __name__ == '__main__':
    # Run the Flask application on localhost, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)