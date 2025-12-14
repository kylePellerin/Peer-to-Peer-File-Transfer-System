import xmlrpc.client
import socket
import threading
import time
import requests
import os
import sys
from flask import Flask, send_from_directory

# --- AWS CONFIGURATION ---
PRIMARY_IP = "54.205.35.150" 
BACKUP_IP  = "54.226.158.73" 
PRIMARY_URL = f"http://{PRIMARY_IP}:8641"
BACKUP_URL  = f"http://{BACKUP_IP}:8642"

SERVER_PORT = 8643 
primary_server = xmlrpc.client.ServerProxy(PRIMARY_URL)
backup_server  = xmlrpc.client.ServerProxy(BACKUP_URL)

def get_public_ip():
    """ ASK AMAZON FOR MY REAL PUBLIC IP """
    try:
        return requests.get('https://checkip.amazonaws.com', timeout=5).text.strip()
    except Exception:
        return socket.gethostbyname(socket.gethostname())

def safe_register(peer_id, file_list):
    try:
        print(f"Registering {peer_id} with Primary...")
        primary_server.P2P.register_files(peer_id, file_list)
        print("Success: Connected to Primary.")
    except Exception as e:
        print(f"Primary failed. Switching to BACKUP...")
        try:
            backup_server.P2P.register_files(peer_id, file_list)
            print("Success: Connected to Backup.")
        except Exception:
            print("CRITICAL: Both servers are down.")

def build_chunks(file_name): # to register chunked files, keeping old to ensure not to break anything
    chunks = []
    with open(file_name, 'rb') as f:
        i = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            chunk_filename = f"{file_name}.part{i}"
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk)
            chunks.append(chunk_filename)
            i += 1
    return chunks

def reassemble_file(filename, chunk_count):
    with open(filename, 'wb') as out:
        for i in range(chunk_count):
            part = f"{filename}.part{i}"
            with open(part, 'rb') as p:
                out.write(p.read())

def safe_search(filename):
    try:
        return primary_server.P2P.search_file(filename)
    except Exception:
        print("Primary unreachable. Searching on Backup...")
        try:
            return backup_server.P2P.search_file(filename)
        except Exception:
            print("Both servers down.")
            return []

def safe_report(bad_peer_id):
    try:
        primary_server.P2P.report_user(bad_peer_id)
        print("Reported to Primary.")
    except Exception:
        try:
            backup_server.P2P.report_user(bad_peer_id)
            print("Reported to Backup.")
        except Exception:
            pass

app = Flask(__name__)
FILE_DIRECTORY = "." 

@app.route('/download/<filename>')
def download_file(filename):
    try:
        # conditional=True allows Flask to handle Range headers automatically
        return send_from_directory(FILE_DIRECTORY, filename, as_attachment=True, conditional=True)
    except Exception as e:
        return str(e), 404
    except Exception as e:
        return str(e), 500

def start_flask_server():
    # Listen on 0.0.0.0 so the outside world can connect
    try:
        app.run(host='0.0.0.0', port=SERVER_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"ERROR starting file server: {e}")

hostname = socket.gethostname()
my_public_ip = get_public_ip()

server_thread = threading.Thread(target=start_flask_server)
server_thread.daemon = True 
server_thread.start()
time.sleep(1)

print(f"\n--- P2P NODE STARTED ---")
MY_PEER_ID = f"{my_public_ip}:{SERVER_PORT}"
print(f"My Public ID: {MY_PEER_ID}")

print("\nStep 1: Share Files")
if sys.stdin.isatty():
    file_input = input("Enter filenames (comma separated): ")
else:
    file_input = sys.stdin.readline().strip()

files_to_register = []
for file in file_input.split(','):
    file = file.strip()
    if os.path.exists(file):
        # CORRECT LOGIC: Register the whole file, do not split it.
        files_to_register.append(file)
        print(f"Prepared {file} for sharing.")
    else:
        print(f"Warning: File '{file}' does not exist and will be skipped.")

# Send the list of strings (whole filenames) to the server
safe_register(MY_PEER_ID, files_to_register)

while True: 
    if not sys.stdin.isatty():
        time.sleep(99999)

    print("\n--- MENU ---")
    print("1. SEARCH")
    print("2. DOWNLOAD")
    print("3. EXIT")
    command = input("Selection: ")

    if command == '1':
        filename = input("Enter filename (or chunk name): ")
        peers = safe_search(filename)
        if peers: print(f"Found: {peers}")
        else: print("Not found.")

    elif command == '2':
        filename = input("Enter Filename: ")
        peers = safe_search(filename)
        
        if not peers:
            print("File not found on any peer.")
            continue

        print(f"Found {len(peers)} peers with this file: {peers}")

        #Get File Size from the first available peer
        file_size = 0
        try:
            first_peer = peers[0]
            first_peer_ip, first_peer_port = first_peer.split(':')
            head_url = f"http://{first_peer_ip}:{first_peer_port}/download/{filename}"
            response = requests.head(head_url, timeout=5)
            if response.status_code == 200:
                file_size = int(response.headers.get('Content-Length', 0))
                print(f"File size: {file_size} bytes")
            else:
                print("Error: Could not determine file size.")
                continue
        except Exception as e:
            print(f"Error connecting to peer for metadata: {e}")
            continue

        if file_size == 0:
            print("File is empty or size unknown.")
            continue

        #Chunk Size
        CHUNK_SIZE = 1024 * 1024 
        num_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
        
        if os.path.exists(filename): #if file exists, ask to overwrite
            if input("File exists. Overwrite? (1=Yes, 0=No): ") != "1":
                continue

        #Create a file of the correct size to write into
        with open(filename, "wb") as f:
            f.seek(file_size - 1)
            f.write(b"\0")

        print(f"Starting download of {num_chunks} chunks from {len(peers)} peers...")

        for i in range(num_chunks):
            start_byte = i * CHUNK_SIZE
            end_byte = min((i + 1) * CHUNK_SIZE - 1, file_size - 1)
            
            # Round Robin: Pick peer based on chunk index
            peer_index = i % len(peers)
            current_peer = peers[peer_index]
            
            ip, port = current_peer.split(':')
            download_url = f"http://{ip}:{port}/download/{filename}"
            
            headers = {"Range": f"bytes={start_byte}-{end_byte}"}
            
            print(f"Downloading chunk {i+1}/{num_chunks} ({start_byte}-{end_byte}) from {current_peer}...")
            
            try:
                r = requests.get(download_url, headers=headers, timeout=10)
                
                if r.status_code == 206 or r.status_code == 200:
                    with open(filename, "r+b") as f: # Open in Read+Binary mode to seek
                        f.seek(start_byte)
                        f.write(r.content)
                else:
                    print(f"Failed to get chunk {i} from {current_peer}. Status: {r.status_code}")
            except Exception as e:
                print(f"Exception downloading chunk {i}: {e}")

        print("Download complete.")
        
        # Register that we now have the file so we can serve it to others
        safe_register(MY_PEER_ID, [filename])

    elif command == '3':
        break