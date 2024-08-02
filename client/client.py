# client/client.py
import os
import socket
import threading
import tkinter as tk
from tkinter import *
from tkinter import filedialog, simpledialog, ttk
import time

#DOWNLOAD_FOLDER = 'Client_data'
HOST = 'localhost'
PORT = 3000
CHUNK = 1024
socket_lock = threading.Lock()
INPUT_FILE = 'input.txt'
OUTPUT_DIR = 'output'


def select_file_to_download():
    file_name = simpledialog.askstring("Download", "Enter the filename to download:")
    if file_name:
        download_file(file_name)
        print(f"File selected: {file_name}")
    else:
        print("No file selected to download.")  

# HELPER FUNCTIONS
def split_file(file_path, chunk_size):
    # intialize a list to stores chunks
    chunks = []
    # open the file in read-binary mode
    with open(file_path, 'rb') as file:
        # read the file chunks-by-chunks
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                chunk_filename = f"{file_path}_part_{len(chunks)}"
                # open file in write-binary mode and write each chunks to new file
                with open(chunk_filename, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunks.append(chunk_filename)
    # return list of chunk_path
    return chunks

def merge_chunks(chunks, output_file):
    # Open the output file in write-binary mode ('wb')
    with open(output_file, 'wb') as out_file:
        # Iterate over the list of chunk files
        for chunk_file in chunks:
            # Open the current chunk file in read-binary mode ('rb')
            with open(chunk_file, 'rb') as chunk:
                # Read the contents of the chunk file and write it to the output file
                out_file.write(chunk.read())
            # Remove the chunk file after it has been written to the output file
            os.remove(chunk_file)

def download_chunk(file_name, client_socket, chunk_paths, num_chunks, download_folder_path):
    try:
        with socket_lock:
            chunk_info = client_socket.recv(1024).decode().strip()
            chunk_index, chunk_size = map(int, chunk_info.split(':'))
            client_socket.send('OK'.encode())

            chunk_data = b''
            while len(chunk_data) < chunk_size:
                chunk_data += client_socket.recv(min(1024, chunk_size - len(chunk_data)))

            chunk_path = os.path.join(download_folder_path, f"{file_name}_chunk_{chunk_index}")
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)

            client_socket.send('OK'.encode())
            print(f"Received chunk_{chunk_index} size: {chunk_size} ({chunk_index + 1}/{num_chunks})")
            chunk_paths.append(chunk_path)

    except Exception as e:
        print(f"Error downloading file {file_name}: {e}")

def download_file(file_name):
    try:
        #create socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            # connect to server
            client_socket.connect((HOST, PORT))
            client_socket.settimeout(10)
            print(f"Host: {HOST}, Port: {PORT}")
            
            # Send the request type
            client_socket.sendall("download".encode())
            print(f"Send request to server: {"download".encode()}")
            
            # Send the file name
            client_socket.sendall(file_name.encode())
            print(f"Send filename to server: {file_name.encode()}")
            ack = client_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Failed to receive acknowledgment from server.")
            # Receive the number of chunks
            num_chunks = int(client_socket.recv(1024).decode())
            print(f"Num of chunks: {num_chunks}")
            # Mở hộp thoại lưu file
            download_folder_path = filedialog.askdirectory()
            # Send acknowledgment
            chunk_paths = []

            threads = []
            for _ in range(num_chunks):
                thread = threading.Thread(target=download_chunk, args=(file_name, client_socket, chunk_paths, num_chunks, download_folder_path))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
            
            if None not in chunk_paths:
                output_file = os.path.join(download_folder_path, file_name)
                merge_chunks(chunk_paths, output_file)
                client_socket.send('OK'.encode())
                print(f"File {file_name} downloaded successfully.")

    except socket.timeout:
        print("Connection timed out. Please try again.")
    except socket.error as E:
        print(f"Socket error: {E}")
    except Exception as E:
        print(f"Error: {E}")

def start_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))

        file_list = client_socket.recv(1024).decode()
        print("Danh sách các file từ server:")
        print(file_list)

        file_name = simpledialog.askstring("Download", "Enter the filename to download:")
        if file_name:
            download_file(file_name)
        else:
            print("No file selected to download.")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    start_client()