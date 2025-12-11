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
        if os.path.exists(filename):
            return send_from_directory(FILE_DIRECTORY, filename, as_attachment=True)
        else:
            return "File not found", 404
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
    # If run by automation script, read from pipe
    file_input = sys.stdin.readline().strip()

file_list = [f.strip() for f in file_input.split(',')]
safe_register(MY_PEER_ID, file_list)

while True: 
    # If automated, sleep forever
    if not sys.stdin.isatty():
        time.sleep(99999)

    print("\n--- MENU ---")
    print("1. SEARCH")
    print("2. DOWNLOAD")
    print("3. EXIT")
    command = input("Selection: ")

    if command == '1':
        filename = input("Enter filename: ")
        peers = safe_search(filename)
        if peers: print(f"Found: {peers}")
        else: print("Not found.")

    elif command == '2':
        filename = input("Enter Filename: ")
        potential_peers = safe_search(filename)
        if not potential_peers:
            print("Not found.")
            continue
            
        for i, p in enumerate(potential_peers):
            print(f"[{i}] {p}")
            
        try:
            selection = int(input("Select peer index: "))
            target_peer_id = potential_peers[selection]
            target_ip, target_port = target_peer_id.split(':')
        except:
            continue
            
        url = f"http://{target_ip}:{target_port}/download/{filename}"
        print(f"Downloading from {url}...")
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(filename, 'wb') as f: f.write(r.content)
                print("SUCCESS!")
                safe_register(MY_PEER_ID, [filename])
                if input("Report malicious? (y/n): ") == 'y': safe_report(target_peer_id)
            else:
                print(f"Failed: {r.status_code}")
        except Exception as e:
            print(f"Error: {e}")

    elif command == '3':
        break