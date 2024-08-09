import socket
import threading
import os
import queue
import sys

file_queue = queue.Queue()
terminate_thread = queue.Queue()

def read_files_config():
    file_list = []
    with open('filename2.txt', 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) == 2:
                name, size = parts
                file_list.append({"name": name, "size": size})
    return file_list

def monitor_for_new_file(client):
    while file_queue.empty():
        try:
            data_chunk = client.recv(13)
            while len(data_chunk) < 13:
                additional_chunk = client.recv(13 - len(data_chunk))
                data_chunk += additional_chunk
            if data_chunk == b"NewFileDetect":
                file_queue.put(1)
        except:
            continue

def process_client(client_socket, client_address):
    try:
        files = read_files_config()
        
        file_list = "\n".join([f'{item["name"]} {item["size"]}' for item in files])
        client_socket.sendall(file_list.encode('utf-8'))
        
        while True:
            incoming_data = client_socket.recv(1024).decode('utf-8')
            if not incoming_data:
                print(f"Client {client_address} has disconnected.")
                break
            
            if incoming_data.startswith("NewFileDetect"):
                continue

            file_names = []
            priorities = []
            opened_files = []

            lines = incoming_data.split("\n")
            for line in lines:
                if not line:
                    break
                name, priority = line.split(" ")
                file_names.append(name)
                priorities.append(priority)
                print(f"Received from {client_address}: {name}, {priority}")

            for name in file_names:
                opened_files.append(open(name, "rb"))

            for file in opened_files:
                file_size = os.path.getsize(file.name)
                client_socket.sendall(str(file_size).encode('utf-8'))
                client_socket.recv(3)  # Waiting for acknowledgment

            new_file_thread = threading.Thread(target=monitor_for_new_file, args=(client_socket,))
            new_file_thread.start()
            
            while opened_files:
                file_name = ""
                for file, priority in zip(opened_files, priorities):
                    if not file_queue.empty():
                        file_name = client_socket.recv(1024).decode('utf-8')
                        padding = b"NewFileIsComing" + b'\0' * (1024 - len(b"NewFileIsComing"))
                        client_socket.sendall(padding)
                        new_files = file_name.split("\n")
                        for new_file in new_files:
                            if not new_file:
                                break
                            new_name, new_priority = new_file.split(" ")
                            priorities.append(new_priority)
                            opened_files.append(open(new_name, "rb"))
                            new_file_size = os.path.getsize(new_name)
                            client_socket.sendall(str(new_file_size).encode('utf-8'))
                            client_socket.recv(3)  # Waiting for acknowledgment
                            print(f"Successfully added new file {client_address}: {new_name}, {new_priority}")
                        file_queue.get()
                    
                    if priority == "CRITICAL":
                        delay = 11
                    elif priority == "HIGH":
                        delay = 5
                    else:
                        delay = 2
                    
                    while delay > 0:
                        chunk = file.read(1024)
                        if not chunk:
                            end_marker = b"end_of_this_file" + b'\0' * (1024 - len(b"end_of_this_file"))
                            client_socket.sendall(end_marker)
                            file.close()
                            opened_files.remove(file)
                            priorities.remove(priority)
                            break
                        if len(chunk) < 1024:
                            chunk += b'\0' * (1024 - len(chunk))
                        client_socket.sendall(chunk)
                        delay -= 1

            print(f"File transfer complete for {client_address}.")
            terminate_thread.put(1)
            new_file_thread.join()
            terminate_thread.get()
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        client_socket.close()

def server_main():
    host_ip = '127.0.0.1'
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host_ip, 3000))
    server_socket.listen(5)
    print(f"Server is running on {host_ip}:3000")

    try:
        while True:
            client_conn, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")
            client_thread = threading.Thread(target=process_client, args=(client_conn, client_address))
            client_thread.start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server_socket.close()

if __name__ == "__main__":
    server_main()
