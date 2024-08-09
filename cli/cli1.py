import socket
import signal
import sys
import os

# Hàm xử lý tín hiệu để thoát chương trình
def signal_handler(signum, frame):
    print('\nĐang thoát chương trình...')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Cấu hình máy chủ và kết nối
server_address = "127.0.0.1"
server_port = 3000
text_encoding = "utf-8"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((server_address, server_port))

print("Kết nối thành công")

# Tạo thư mục lưu trữ dữ liệu nếu chưa có
output_directory = "output1"
os.makedirs(output_directory, exist_ok=True)

# Nhận thông báo từ máy chủ
server_message = client_socket.recv(1024).decode(text_encoding, errors='ignore')
print(f"{server_message} \n")

# Đọc dữ liệu từ file input.txt và xử lý
while True:
    with open("input.txt", "r") as input_file:
        lines = input_file.readlines()

    for line in lines:
        filename = line.strip()
        if not filename:
            continue
        
        output_file_path = os.path.join(output_directory, filename)
        if not os.path.exists(output_file_path):
            client_socket.sendall(filename.encode(text_encoding))
            
            # Nhận kích thước tệp tin từ máy chủ
            try:
                response = client_socket.recv(1024).decode(text_encoding, errors='ignore')
                if response[:11] == "<EndOfFile>":
                    print(f"{filename} không tồn tại trên máy chủ.")
                    continue
                
                file_size = int(response)
            except ValueError:
                print(f"Lỗi nhận kích thước tệp: {response}")
                continue
            
            with open(output_file_path, "wb") as output_file:
                received_size = 0
                while received_size < file_size:
                    chunk = client_socket.recv(min(file_size - received_size, 1024))
                    if chunk[:11] == b"<EndOfFile>":
                        break
                    output_file.write(chunk)
                    received_size += len(chunk)
                    
                    # Tính toán và in phần trăm tải xuống
                    percent_complete = (received_size / file_size) * 100
                    print(f"\rĐang tải {filename}: {percent_complete:.2f}% hoàn thành", end='')
                
                print("\nHoàn tất tải xuống " + filename)
