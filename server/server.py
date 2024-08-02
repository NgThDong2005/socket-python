# server/server.py
import os
import socket
import threading
from tkinter import filedialog, simpledialog, ttk
from datetime import datetime


UPLOAD_FOLDER = 'Server_data'
HOST = 'localhost'
PORT = 3000
CHUNK = 1024
socket_lock = threading.Lock()
FILE_LIST_PATH = 'text.txt' 


def read_file_list(file_path):
    file_list = []
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) == 2:
                file_name, file_size = parts
                file_list.append((file_name, file_size))
    return file_list

def receive_request_type_and_file_info(conn):
    data = conn.recv(1024).decode().strip()
    conn.sendall("OK".encode())
    if data.startswith('upload:'):
        return 'upload', data[len('upload:'):]
    elif data.startswith('download:'):
        return 'download', data[len('download:'):]
    else:
        return None, None
    
def split(filePath, chunkSize):
    chunks = []
    with open(filePath, 'rb') as file:
            while True:
                chunk = file.read(chunkSize)
                if not chunk:
                    break
                chunkFile = f"{filePath}_part_{len(chunks)}"
                with open(chunkFile, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunks.append(chunkFile)
    return chunks

def send_chunk(conn, chunk_index, chunk_path, num_chunks):
    try:
        with socket_lock:
            chunk_size = os.path.getsize(chunk_path)
            conn.sendall(f"{chunk_index}:{chunk_size}\n".encode())
            ack = conn.recv(10).decode().strip()
            if ack != 'OK':
                raise Exception("Failed to receive acknowledgment from client.")

            with open(chunk_path, 'rb') as chunk_file:
                chunk_data = chunk_file.read()
                conn.sendall(chunk_data)

            ack = conn.recv(10).decode().strip()
            if ack != 'OK':
                raise Exception("Failed to receive acknowledgment from client.")
            else:
                print(f"sent chunk_{chunk_index} size: {os.path.getsize(chunk_path)} ({chunk_index + 1}/{num_chunks})")
    except Exception as e:
        print(f"Error sending chunk {chunk_index}: {e}")
                


def handle_download(conn, file_name):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_name} not found.")

        chunks = split(file_path, CHUNK)
        num_chunks = len(chunks)
        conn.sendall(f"{num_chunks}".encode())        
        threads = []
        for index, chunk_path in enumerate(chunks):
            thread = threading.Thread(target=send_chunk, args=(conn, index, chunk_path, num_chunks))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        ack = conn.recv(10).decode().strip()
        if ack != 'OK':
            raise Exception("Failed to receive acknowledgment from client.")
        else:
            print(f"File {file_name} downloaded successfully.")
    except Exception as e:
        print(f"Error handling download: {e}")
    finally:
        for chunk in chunks:
            os.remove(chunk)
        

def handle_client(conn, addr):
    print(f"Connected by {addr}")
    try:
        # Send file list to client
        file_list = read_file_list(FILE_LIST_PATH)
        file_list_str = '\n'.join([f"{name} {size}" for name, size in file_list])
        conn.sendall(file_list_str.encode())
        
        request_type, file_info = receive_request_type_and_file_info(conn)
        if not request_type or not file_info:
            raise ValueError("Invalid request type or file info")
        print(f"Request: {request_type}")
        print(f"File info: {file_info}")
        file_name = file_info.strip()
        print(f"FileDownloadname: {file_name}")
        handle_download(conn, file_name)
    
    except socket.error as E:
        print(f"Socket error: {E}")
    except OSError as E:
        print(f"Error writing to file: {E}")
    except ValueError as E:
        print(f"Error parsing file info: {E}")
    except Exception as E:
        print(f"Error: {E}")
    finally:
        conn.close()

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST,PORT))
        server_socket.listen()
        print(f"Server is listening on {HOST} - {PORT}")
        
        while True:
            conn, addr = server_socket.accept()
            print(f"Connected with client on {addr[0]} - {addr[1]}")
            client_thread = threading.Thread(target = handle_client, args = (conn, addr))
            client_thread.start()
    
def main():
    try:
        start_server()
    except KeyboardInterrupt:
        print(f"Server stopped.")
    except Exception as E:
        print(f"Error: {E}")
    
if __name__ == "__main__":
    main()