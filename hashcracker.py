from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/crack_wifi', methods=['POST'])
def crack_wifi():
    """
    Endpoint to crack a WiFi password using a provided handshake and mask.

    Request Parameters:
    - handshake (str): The WiFi handshake in text format.
    - mask (str): The mask used by hashcat to crack the password.

    Returns:
    - 200: Cracked password in JSON format if successful.
        Example: {"cracked_password": "password123"}
    - 400: Error message if input validation fails.
        Example: {"error": "Invalid input, handshake and mask are required"}
    - 500: Error message if there is an issue writing the handshake file or running hashcat.
        Example: {"error": "Unable to write handshake to file: [error details]"}
    - 404: Error message if password could not be found.
        Example: {"error": "Password not found."}

    Example cURL Call:
    curl -X POST http://localhost:5000/crack_wifi -F "handshake=WPA*02*ab922a72ebffedac4efecc2728c354fe*b20821f62c1b*febd4519990e*4b394d*5dcaa827b4596e97763ff658bc6be85f4af9a7f3e1122ee3f2534f120e6f3df8*0103007502010a000000000000000000019a1fbae1c887a2d52755464df650c87941b6dc8a81f8f56f1f036a64773de523000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001630140100000fac040100000fac040100000fac020000*02" -F "mask=604?d?d?d?d?d?d?d"

    Sample Response:
    {
      "cracked_password": "6049790899"
    }
    """
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

    hashcat_command = [
        'hashcat.bin',          # The hashcat executable
        '-m', '22000',          # Hash type (22000 is for WPA-PBKDF2-PMKID+EAPOL)
        '-a3',                  # Attack mode (3 is for brute-force attack)
        handshake_file_path,    # Path to the file containing the handshake
        mask,                   # Mask for the brute-force attack (e.g. ?a?a?a?a)
        '-w', '3',              # Workload profile (3 is for high performance)
        '-o', 'cracked.txt',    # Output file for cracked passwords
        '--potfile-disable'     # Disable the potfile (which stores previously cracked passwords)
    ]

    try:
        result = subprocess.run(hashcat_command, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        cleanup_files([handshake_file_path, 'cracked.txt'])
        return jsonify({"error": "Error running hashcat: " + e.stderr}), 500

    # Read the contents of cracked.txt to get the cracked password
    try:
        with open('cracked.txt', 'r') as cracked_file:
            cracked_password = cracked_file.read().strip()
            cracked_password = cracked_password.split(':')[-1].strip()
    except IOError as e:
        cleanup_files([handshake_file_path, 'cracked.txt'])
        return jsonify({"error": "Unable to read cracked password file: " + str(e)}), 500

    # Cleanup temporary files
    cleanup_files([handshake_file_path, 'cracked.txt'])

    # Return the cracked password
    if cracked_password:
        return jsonify({"cracked_password": cracked_password}), 200
    else:
        return jsonify({"error": "Password not found."}), 404

def cleanup_files(file_paths):
    """
    Helper function to remove temporary files.

    Parameters:
    - file_paths (list): List of file paths to be removed.
    """
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            print(f"Error removing file {file_path}: {e}")

if __name__ == '__main__':
    # Run the Flask application on localhost, port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
