import xmlrpc.client

server = xmlrpc.client.Server("http://172.31.37.44:8089") //testing on VM servers

print("Welcome to the P2P File Sharing Network")
print("Please offer the main server what files you can share:")
file_list = input("Enter filenames separated by commas: ").split(',')
file_list = [filename.strip() for filename in file_list]
server.register_files(file_list) # need to implement this function on server side

while True: 
    command = input("Please enter a command (Either querry for a filename, or listen quietly): ")

    if command == '1' :
        filename = input("Enter the filename you want to search for: ")
        peers = server.search_file(filename) # need to implement this function on server side
        if peers:
            print(f"Peers with the file '{filename}': {peers}")
        else:
            print(f"No peers found with the file '{filename}'.")
    
    elif command == '2' :
        print("Listening quietly for incoming requests...")
        # Implement listening logic here if needed
    
    else:
        print("Command not implemented. Exiting...")
        break