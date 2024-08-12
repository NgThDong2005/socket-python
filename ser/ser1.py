import os
import socket

host_address = "127.0.0.1"
port_number = 3000
text_encoding = "utf-8"
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((host_address, port_number))

print(f"Máy chủ đang chạy trên {host_address}:{port_number}")

while True:
    server_socket.listen()
    print("Đang chờ kết nối từ khách hàng...")
    client_socket, client_address = server_socket.accept()
    print(f"Đã kết nối với {client_address}")
    try:
        with open("filename1.txt", "r") as file:
            file_content = file.read()
            client_socket.sendall(file_content.encode(text_encoding))

        while True:
            client_message = client_socket.recv(1024).decode(text_encoding)
            
            if client_message == '':
                print(f"{client_address} đã ngắt kết nối")
                break
            
            print(f"Nhận từ khách hàng: {client_message}")
            requested_file = f"{client_message}"
            
            if os.path.exists(requested_file):
                file_size = os.path.getsize(requested_file)
                client_socket.sendall(str(file_size).encode(text_encoding))
                
                with open(requested_file, "rb") as file:
                    while (chunk := file.read(1024)):
                        if len(chunk) < 1024:
                            chunk += b'\0' * (1024 - len(chunk))
                        client_socket.sendall(chunk)
                
                end_marker = b"<EndOfFile>"
                end_marker = end_marker.ljust(1024, b'\0')
                client_socket.sendall(end_marker)
                print(f"Đã gửi xong {requested_file}")
            else:
                print(f"Tệp tin {requested_file} không tồn tại")
                client_socket.sendall(b"File not found")

    except Exception as e:
        print(f"Đã xảy ra lỗi: {e}")
    finally:
        client_socket.close()
