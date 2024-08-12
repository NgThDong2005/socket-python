import socket
import signal
import sys
import os
from time import sleep

def signal_handler(sig, frame):
    print('\nExiting program...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
host = "127.0.0.1"
port = 3000
encoding = "utf-8"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect((host, port))

print("Connected successfully")

output_dir = "output1"
os.makedirs(output_dir, exist_ok=True)

message = client.recv(1024).decode(encoding)
print(f"{message} \n")

def print_process(current, total):
    percent = float(current) / total * 100
    print(f"\rDownloading... {percent:.2f}%", end='', flush=True)

while True:
    with open("input1.txt", "r") as file:
        lines = file.readlines()
        
    for line in lines:
        data = line.strip()
        if not data:
            continue
    
        message = data      
        if not os.path.exists(f"{output_dir}/{message}"):
            client.sendall(str(message).encode(encoding))
            
            response = client.recv(1024).decode(encoding)
            size = int(response)    
            file_name = f"{output_dir}/{message}"
            with open(file_name, "wb") as file:
                current = 0
                while True:
                    chunk = client.recv(1024)
                    while len(chunk) != 1024:
                        data = client.recv(1024 - len(chunk))
                        chunk = chunk + data
                    if chunk[:11] == b"<EndOfFile>":
                        break
                    if current + 1024 > size:
                        file.write(chunk[0:(size - current)])
                        current = current + (size - current)
                    else:    
                        file.write(chunk)
                        current += len(chunk)
                    print_process(current, size)
            print("\n")
