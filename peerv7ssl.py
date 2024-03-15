import socket
import os
import threading
import ssl

def send_to_tracker(ip_address, files, request_type):
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.load_verify_locations("server.crt")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip = ''# ENTER IP ADDRESS OF TRACKER
    start_port = 6969
    for i in range(5):
        server_address = (server_ip, start_port + i)
        try:
            sock.connect(server_address)
            break
        except socket.error as e:
            if i == 4:
                print("Tracker is busy")
                return
            continue
    
    with context.wrap_socket(sock) as secure_sock:
        try:
            if request_type == 'REGISTER':
                message = 'REGISTER:'+ip_address+':'+','.join(files)
                secure_sock.sendall(message.encode('utf-8'))
                full_data = b''
                while True:
                    data = secure_sock.recv(1024)
                    if not data:
                        break
                    full_data += data
                data_str = full_data.decode('utf-8')
                if data_str.startswith("FILES_LIST:"):
                    file_list = data_str[len("FILES_LIST:"):].split(',')
                    print("Files from P2P network:")
                    for file_name in file_list:
                        print(file_name)            
                else:
                    print(data_str)
            elif request_type == 'DOWNLOAD_REQUEST':
                secure_sock.sendall('DOWNLOAD_REQUEST'.encode('utf-8'))
                data = secure_sock.recv(1024)
                file_list = data.decode('utf-8')[len("FILES_LIST:"):].split(',')
                print("Files Available For Download:")
                for file_name in file_list:
                    print(file_name)
                file_to_download = input("Enter the name of the file to download : ")
                secure_sock.sendall(('DOWNLOAD:'+file_to_download).encode('utf-8'))
                ip_peer = secure_sock.recv(1024).decode('utf-8')
                print("\nIP_PEER\n", ip_peer, "\nDONE\n")
                if ip_peer == "FILE NOT FOUND":
                    print("File not found")
                else:
                    download_from_peer(ip_peer, file_to_download,directory_path)
        except Exception as e:
            print("Error:", e)
        finally:
            secure_sock.close()

def download_from_peer(peer_ip, file_name, directory_path):
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    context.check_hostname = False
    context.load_verify_locations("server.crt")

    download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_address = (peer_ip, 9696)
    
    with context.wrap_socket(download_socket) as secure_download_socket:
        print("\nPEER_ADDRESS\n", peer_address, "\nDONE\n")
        secure_download_socket.connect(peer_address)
        secure_download_socket.sendall(('DOWNLOAD:' + file_name).encode('utf-8'))
        file_path = os.path.join(directory_path, file_name)
        with open(file_path, 'wb') as file:
            while True:
                file_data = secure_download_socket.recv(1024)
                if not file_data:
                    break
                file.write(file_data)
        print('File downloaded and saved:', file_path)

def get_files_in_directory(directory_path):
    files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
    return files

def handle_download_requests(ip_address, port, directory_path):
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.check_hostname = False
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    download_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    download_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = (ip_address, port)
    
    with context.wrap_socket(download_socket, server_side=True) as secure_download_socket:
        secure_download_socket.bind(server_address)
        secure_download_socket.listen(5)
        
        while True:
            print('PLEASE SELECT AN OPTION:')
            connection, client_address = secure_download_socket.accept()
            with connection:
                print('Connection from', client_address)
                data = connection.recv(1024).decode('utf-8')
                print('Received {!r}'.format(data))
                parts = data.split(':')
                if parts[0] == 'DOWNLOAD':
                    file_name = parts[1]
                    file_path = os.path.join(directory_path, file_name)
                    if os.path.isfile(file_path):
                        with open(file_path, 'rb') as file:
                            file_data = file.read()
                            connection.sendall(file_data)
                            print('File sent : ', file_name)
                    else:
                        message = "FILE NOT FOUND"
                        connection.sendall(message.encode('utf-8'))

directory_path = 'C:/Users/Harsha Kolipakula/Documents/CN/VIDEOS'
if not os.path.exists(directory_path):
    os.makedirs(directory_path)

files = get_files_in_directory(directory_path)
localhost_ip = socket.gethostbyname(socket.gethostname())
localhost_ip_str = str(localhost_ip)
ip_address = localhost_ip_str

send_to_tracker(ip_address, files, 'REGISTER')
download_port = 9696
handle_download_thread = threading.Thread(target=handle_download_requests, args=(ip_address, download_port, directory_path))
handle_download_thread.daemon = True
handle_download_thread.start()

while True:
    print("\nFunctions List:\n1:DOWNLOAD_REQUEST\n0:Exit\n")
    action = input("Enter choice : ")
    print("\n")
    if action == '1':
        send_to_tracker(ip_address, files, 'DOWNLOAD_REQUEST')
    elif action == '0':
        print("Terminating Program\n")
        break
    else:
        print("Invalid Input\n")

