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