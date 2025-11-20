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
    
    elif command == '2' :
    
    elif command == '3' :
    
    elif command == '4' :
    
    else:
        print("Command not implemented. Exiting...")
        break