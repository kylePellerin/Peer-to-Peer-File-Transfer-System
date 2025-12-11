import xmlrpc.client
import socket
import threading
import time
import requests
import os
from flask import Flask, send_from_directory
PRIMARY_IP = "54.205.35.150" 
BACKUP_IP  = "54.226.158.73" 
PRIMARY_URL = f"http://{PRIMARY_IP}:8641"
BACKUP_URL  = f"http://{BACKUP_IP}:8642"

SERVER_PORT = 8643  #all peers on this random value

# Create connections
primary_server = xmlrpc.client.ServerProxy(PRIMARY_URL)
backup_server  = xmlrpc.client.ServerProxy(BACKUP_URL)

def safe_register(ip, file_list):
    try:
        print(f"Registering with Primary ({PRIMARY_IP})...")
        primary_server.P2P.register_files(ip, file_list)
        print("Success: Connected to Primary.")
    except Exception as e:
        print(f"Primary failed. Switching to BACKUP ({BACKUP_IP})...")
        try:
            backup_server.P2P.register_files(ip, file_list)
            print("Success: Connected to Backup.")
        except Exception:
            print("CRITICAL: Both servers are down.")

def safe_search(filename):
    #Tries Primary If fail, tries Backup.
    try:
        return primary_server.P2P.search_file(filename)
    except Exception:
        print("Primary unreachable. Searching on Backup...")
        try:
            return backup_server.P2P.search_file(filename)
        except Exception:
            print("Both servers down.")
            return []
app = Flask(__name__)
FILE_DIRECTORY = "." 

@app.route('/download/<filename>')
def download_file(filename):
    try:
        if os.path.exists(filename):
            print(f"\n[!] Peer requested '{filename}'. Sending...")
            return send_from_directory(FILE_DIRECTORY, filename, as_attachment=True)
        else:
            return "File not found", 404
    except Exception as e:
        return str(e), 500

def start_flask_server():
    # We listen on 0.0.0.0 to allow connections from other AWS machines
    try:
        app.run(host='0.0.0.0', port=SERVER_PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"ERROR starting file server: {e}")

def safe_report(peer_ip):
    # Report a malicious file transfer to the network
    try:
        primary_server.P2P.report_user(peer_ip)
        print("Reported to Primary.")
    except Exception:
        print("Primary unreachable. Reporting on Backup...")
        try:
            backup_server.P2P.report_user(peer_ip)
            print("Reported to Backup.")
        except Exception:
            print("Both servers down. Report failed.")

hostname = socket.gethostname()
my_ip = socket.gethostbyname(hostname)

# start the File Server background thread
server_thread = threading.Thread(target=start_flask_server)
server_thread.daemon = True 
server_thread.start()
time.sleep(1) # give flask a second to start

print(f"\n--- P2P NODE STARTED ---")
print(f"My IP: {my_ip}")
print(f"Listening on Port: {SERVER_PORT}")

print("\nStep 1: Share Files")
file_input = input("Enter filenames (comma separated): ")
file_list = [f.strip() for f in file_input.split(',')]

safe_register(my_ip, file_list)

while True: 
    print("\n--- MENU ---")
    print("1. SEARCH for a file")
    print("2. DOWNLOAD a file")
    print("3. LISTEN for incoming requests")
    print("4. EXIT")
    
    command = input("Selection: ")

    if command == '1':
        filename = input("Enter filename to search: ")
        peers = safe_search(filename)
        if peers:
            print(f"Peers with '{filename}': {peers}")
        else:
            print(f"No peers found.")

    elif command == '2':
        filename = input("Enter Filename to download: ")
    
        print(f"Locating '{filename}'...")
        potential_peers = safe_search(filename) #call our mainserver method
        
        if not potential_peers:
            print("File not found on network.")
            continue
        print(f"\nFound {len(potential_peers)} source(s):")
        for i, peer_ip in enumerate(potential_peers):
            print(f"[{i}] {peer_ip}")
        try:
            selection = int(input("\nEnter index of peer: "))
            target_ip = potential_peers[selection]
        except (ValueError, IndexError):
            print("Invalid selection.")
            continue
            
        url = f"http://{target_ip}:{SERVER_PORT}/download/{filename}"
        print(f"Downloading from {target_ip}...")
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                if filename in file_list:
                    overwrite = int(input("File already exists locally, you will overwrite is this okay? (1=Yes, 0=No): ")) #add overwrite prompt later
                    if not overwrite:
                        print("Download cancelled.")
                        continue

                save_name = filename
                with open(save_name, 'wb') as f:
                    f.write(response.content)
                print(f"SUCCESS! Saved as '{save_name}'")
                safe_register(my_ip, [save_name.strip()]) #register new file with server
                file_list.append(save_name.strip())
                report = int(input("Report this as a malicious file transfer to the network? (1=Yes, 0=No): ")) #architecture for reporting
                if report == 1:
                    print("Reporting... Peers") #architecture for reporting
                    safe_report(target_ip)
            else:
                print(f"Failed. Status: {response.status_code}")
        except Exception as e:
            print(f"Download Error: {e}")
    elif command == '3':
        print(f"Listening... (Press Ctrl+C to stop)")
        while True:
            time.sleep(1)
    elif command == '4':
        break