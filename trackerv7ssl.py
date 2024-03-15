import socket
import threading
import os
import time
import subprocess
import ssl

def ping_ips(ip_files_dict):
    while True:
        for ip in list(ip_files_dict.keys()):
            try:
                response = subprocess.check_output(
                    ['ping', '-n', '1', '-w', '1000', ip],
                    stderr=subprocess.STDOUT,
                    universal_newlines=True 
                )
                if 'unreachable' in response:
                    print(f"IP address {ip} is not active. Removing from dictionary.")
                    del ip_files_dict[ip]
            except subprocess.CalledProcessError:
                del ip_files_dict[ip]
        time.sleep(30)

def tracker(port, ip_files_dict):   
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.check_hostname = False
    context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    host_name = socket.gethostname()
    host_ip = socket.gethostbyname(host_name)
    server_address = (host_ip, port)

    with context.wrap_socket(sock, server_side=True) as secure_sock:
        secure_sock.bind(server_address)
        secure_sock.listen(0)
        
        while True:
            print(f'\nWaiting for a connection at {host_ip}:{port}')
            connection, client_address = secure_sock.accept()
            with connection:
                print('Connection from', client_address)
                data = connection.recv(1024).decode('utf-8')
                print('received {!r}'.format(data))
                parts = data.split(':')
                if parts[0] == 'REGISTER':
                    ip_address = parts[1]
                    files = parts[2].split(',')
                    if ip_address in ip_files_dict:
                        print("CONNECTION REJECTED AS REPEATED REGISTRATION ATTEMPTED")
                        message = "ALREADY REGISTERED"
                        connection.sendall(message.encode('utf-8'))
                    else:
                        ip_files_dict[ip_address] = files
                        all_files = [file for files_list in ip_files_dict.values() for file in files_list]
                        file_list_message = 'FILES_LIST:' + ','.join(all_files)
                        connection.sendall(file_list_message.encode('utf-8'))
                elif parts[0] == 'DOWNLOAD_REQUEST':
                    all_files = [file for files_list in ip_files_dict.values() for file in files_list]
                    file_list_message = 'FILES_LIST:' + ','.join(all_files)
                    connection.sendall(file_list_message.encode('utf-8'))
                    file_name = ((connection.recv(1024).decode('utf-8')).split(':'))[1]
                    for ip, files in ip_files_dict.items():
                        if file_name in files:
                            print(ip)
                            connection.sendall(ip.encode('utf-8'))
                            break
                    else:
                        message = "FILE NOT FOUND"
                        connection.sendall(message.encode('utf-8'))
                print(ip_files_dict)

if __name__ == '__main__':
    ip_files_dict = {}
    start_port = 6969
    for i in range(5):
        port = start_port + i
        tracker_thread = threading.Thread(target=tracker, args=(port, ip_files_dict))
        tracker_thread.start()
    ping_thread = threading.Thread(target=ping_ips, args=(ip_files_dict,))
    ping_thread.daemon = True
    ping_thread.start()


