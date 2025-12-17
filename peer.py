import xmlrpc.client
import socket
import threading
import time
import requests
import os
import sys
import concurrent.futures
from flask import Flask, send_from_directory

# --- AWS CONFIGURATION ---
PRIMARY_IP = "54.205.35.150" 
BACKUP_IP  = "54.226.158.73" 
PRIMARY_URL = f"http://{PRIMARY_IP}:8641"
BACKUP_URL  = f"http://{BACKUP_IP}:8642"

if len(sys.argv) > 1:
    SERVER_PORT = int(sys.argv[1])
else:
    SERVER_PORT = 8643
CHUNK_SIZE = 1024 * 1024 #just 1mb 
primary_server = xmlrpc.client.ServerProxy(PRIMARY_URL)
backup_server  = xmlrpc.client.ServerProxy(BACKUP_URL)

def get_public_ip():
    """ ASK AMAZON FOR MY REAL PUBLIC IP """
    try:
        return requests.get('https://checkip.amazonaws.com', timeout=5).text.strip()
    except Exception:
        return socket.gethostbyname(socket.gethostname())

#First trying to connect to main server, if fails, try backup.
def safe_register(peer_id, file_list): 
    try:
        print(f"Registering {peer_id} with Primary...")
        primary_server.P2P.register_files(peer_id, file_list)
        print("Success: Connected to Primary.")
    except Exception as e: #attempting backup
        print(f"Primary failed. Switching to BACKUP...")
        try:
            backup_server.P2P.register_files(peer_id, file_list)
            print("Success: Connected to Backup.")
        except Exception:
            print("CRITICAL: Both servers are down.")

#unregister from both servers safely.
def safe_unregister(peer_id):
    try:
        primary_server.P2P.unregister_client(peer_id)
    except Exception:
        try:
            backup_server.P2P.unregister_client(peer_id)
        except Exception:
            pass

#Search for filename on primary server, if fails we will try on the backuo.
def safe_search(filename):
    try:
        return primary_server.P2P.search_file(filename)
    except Exception:
        print("Primary unreachable. Searching on Backup...")
        try:
            return backup_server.P2P.search_file(filename)
        except Exception: #should both be down unable to search.
            print("Both servers down.")
            return []

#reporting a malicious peer to the server attempting to contact each server.
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

#calculate latency to each peer and rank them. choosing the best half of the list of peers
def rank_peers_by_latency(peers, filename):
    print(f"   [Speed Test] Benchmarking {len(peers)} peers...")
    ranked_results = []

    def check_speed(peer):
        ip, port = peer.split(':')
        url = f"http://{ip}:{port}/download/{filename}"
        try:
            start = time.time()
            # just get headers
            requests.head(url, timeout=2) 
            latency = time.time() - start
            return (latency, peer)
        except:
            return (999, peer) # If it fails, treat as super slow
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = list(executor.map(check_speed, peers))

    # sort by latency (lowest first)
    results.sort(key=lambda x: x[0])
    # extract just the peer strings
    sorted_peers = [r[1] for r in results if r[0] < 999]
    print(f"   [Speed Test] Top 3 Fastest Peers:")
    for i in range(min(3, len(sorted_peers))):
        print(f" #{i+1}: {sorted_peers[i]} ({results[i][0]:.3f}s)")
         
    return sorted_peers

@app.route('/download/<filename>')
def download_file(filename):
    try:
        # conditional=True allows Flask to handle Range headers automatically
        return send_from_directory(FILE_DIRECTORY, filename, as_attachment=True, conditional=True)
    except Exception as e:
        return str(e), 404
    except Exception as e:
        return str(e), 500

#starting of the peer server, prompting for files to share and then communicating with both servers
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

#our main loop logic for commands from the user 
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

        print(f"Found {len(peers)} peers. Ranking by speed...")
        #Use latency sort for best peers
        peers = rank_peers_by_latency(peers, filename)
        
        if not peers:
            print("All peers unreachable.")
            continue

        if len(peers) > 5:
            # Keep only the Top 10 (or Top 50%) prefomring peers 
            cutoff = max(10, int(len(peers) * 0.5))
            print(f"Optimization: Dropping {len(peers) - cutoff} slow peers. Keeping Top {cutoff}.")
            peers = peers[:cutoff]
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

        num_chunks = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE
        
        if os.path.exists(filename): #if file exists, ask to overwrite
            if input("File exists. Overwrite? (1=Yes, 0=No): ") != "1":
                continue

        #Create a file of the correct size to write into
        with open(filename, "wb") as f:
            f.seek(file_size - 1)
            f.write(b"\0")

        # DYNAMIC THREAD COUNT: 
        # Use 1 thread per peer, up to a max of 10 (to prevent crashing the OS)
        num_threads = min(len(peers), 10)
        
        print(f"Starting PARALLEL download of {num_chunks} chunks from {len(peers)} peers using {num_threads} threads...")

        def download_chunk(i):
            start_byte = i * CHUNK_SIZE
            end_byte = min((i + 1) * CHUNK_SIZE - 1, file_size - 1)
            peer_index = i % len(peers)
            current_peer = peers[peer_index]
            
            ip, port = current_peer.split(':')
            download_url = f"http://{ip}:{port}/download/{filename}"
            headers = {"Range": f"bytes={start_byte}-{end_byte}"}

            # print(f"Downloading chunk {i+1} from {current_peer}...") # Optional: Comment out to reduce spam
            
            try:
                r = requests.get(download_url, headers=headers, timeout=10)
                if r.status_code == 206 or r.status_code == 200:
                    with open(filename, "r+b") as f:
                        f.seek(start_byte)
                        f.write(r.content)
                    return True
                else:
                    print(f"Failed chunk {i} from {current_peer}: {r.status_code}")
                    return False
            except Exception as e:
                print(f"Error chunk {i}: {e}")
                return False

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(download_chunk, i) for i in range(num_chunks)]
            concurrent.futures.wait(futures)

        print("Download complete.")
        if input("Do you want to report this file transfer? (1=Yes, 0=No): ") == "1":
            for peer in peers:
                if peer == MY_PEER_ID: #don't report yourself
                    continue
                print("Reporting bad peer:", peer)
                safe_report(peer)
        # Register that we now have the file so we can serve it to others
        safe_register(MY_PEER_ID, [filename])

    elif command == '3':
        print("Exiting...")
        safe_unregister(MY_PEER_ID)
        break