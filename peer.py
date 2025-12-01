import xmlrpc.client
import socket

hostname = socket.gethostname()
my_ip = socket.gethostbyname(hostname)

print(f"My IP is: {my_ip}")

server = xmlrpc.client.ServerProxy("http://localhost:8089") #we need to change this to our new IP address

print("Welcome to the P2P File Sharing Network")
print("Please offer the main server what files you can share:")
file_input = input("Enter filenames separated by commas: ")

file_list = [filename.strip() for filename in file_input.split(',')]
print(f"You are sharing the following files: {file_list}")
server.P2P.register_files(my_ip, file_list)  


while True: 
    command = input("Please enter a command (1=Search, 2=Listen): ")

    if command == '1' :
        filename = input("Enter the filename you want to search for: ")
        peers = server.P2P.search_file(filename)
        
        if peers:
            print(f"Peers with the file '{filename}': {peers}")
        else:
            print(f"No peers found with the file '{filename}'.")
    
    elif command == '2' :
        print("Listening quietly for incoming requests...")
        # server code here later 
    else:
        print("Command not implemented. Exiting...")
        break