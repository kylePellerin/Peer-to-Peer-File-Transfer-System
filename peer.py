import xmlrpc.client
import socket
import threading
import time
import requests
import os
from flask import Flask, send_from_directory

app = Flask(__name__)

# we serve files from the current folder
FILE_DIRECTORY = "." 

@app.route('/download/<filename>')
def download_file(filename):
    try:
        # Check if file exists before trying to send
        if os.path.exists(filename):
            print(f"\n[!] Incoming request: Sending '{filename}' to a peer...")
            return send_from_directory(FILE_DIRECTORY, filename, as_attachment=True)
        else:
            return "File not found", 404
    except Exception as e:
        return str(e), 500

def start_flask_server(port):
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False) # 0.0.0.0 for listen to anyone

hostname = socket.gethostname()
my_ip = socket.gethostbyname(hostname)
print(f"My IP is: {my_ip}")

my_port = int(input("Enter the PORT you want to listen on: ")) #hardcose for 8089 with one
server_thread = threading.Thread(target=start_flask_server, args=(my_port,))
server_thread.daemon = True # ensures thread dies when program closed
server_thread.start()

time.sleep(1) #needed this delay to start flask without issues

server = xmlrpc.client.ServerProxy("http://localhost:8089") #we need to change this to our new IP address eventually

print("Welcome to the P2P File Sharing Network")
print("Please offer the main server what files you can share:")
file_input = input("Enter filenames separated by commas: ")

file_list = [filename.strip() for filename in file_input.split(',')]
print(f"You are sharing the following files: {file_list}")
try:
    server.P2P.register_files(my_ip, file_list)
    print("Files registered successfully with the main server.")
except Exception as e:
    print(f"Error registering files: {e}")


while True: 
    print("\n--- MENU ---")
    print("1. SEARCH for a file")
    print("2. DOWNLOAD a file")
    print("3. Listen quietly (Log Mode)")
    print("4. Exit")
    
    command = input("Selection: ")

    if command == '1':
        filename = input("Enter filename to search: ")
        try:
            peers = server.P2P.search_file(filename)
            if peers:
                print(f"Peers with '{filename}': {peers}")
            else:
                print(f"No peers found for '{filename}'.")
        except Exception as e:
            print(f"Search failed: {e}")

    elif command == '2':
        # This is the new logic to actually fetch the file
        target_ip = input("Enter Peer IP: ")
        target_port = input("Enter Peer Port (e.g. 8001): ")
        filename = input("Enter Filename: ")

        # Construct the URL based on our Flask route
        url = f"http://{target_ip}:{target_port}/download/{filename}"
        
        print(f"Downloading from {url}...")
        try:
            # Send HTTP GET request to the peer
            response = requests.get(url)
            
            if response.status_code == 200:
                # Save the file content
                save_name = "downloaded_" + filename
                with open(save_name, 'wb') as f:
                    f.write(response.content)
                print(f"SUCCESS! Saved as '{save_name}'")
            else:
                print(f"Failed. Peer sent status code: {response.status_code}")
        except Exception as e:
            print(f"Download error: {e}")

    elif command == '3':
        print(f"Listening on port {my_port}... (Press Ctrl+C to stop)")
        # Just sleep forever to keep the Flask thread alive
        while True:
            time.sleep(1)
            
    elif command == '4':
        print("Exiting...")
        break
    else:
        print("Invalid command.")