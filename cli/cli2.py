import socket
import time
import collections
import threading
import os
import sys

class Request:
    def __init__(self, name, priority, size, progress):
        self.name = name
        self.priority = priority
        self.size = size
        self.progress = progress #tiến độ tải file


class menu:
    def __init__(self, name, size):
        self.name = name
        self.size = size

preRequest = []
NumberOfFile_Menu = 0

def get_local_ip(s:socket.socket):

    s.settimeout(0)
    try:
        s.connect(('10.254.254.254', 1))

        local_ip = s.getsockname()[0] 
    except Exception:
        local_ip = '127.0.0.1'
    finally:
        s.close()
    return local_ip


def checkPrevious(preRequest, request):
    for i in range(0, len(preRequest)):
        if preRequest[i].name == request:
            return True
    return False


def readInputFile(s, Menu):
    try:
        while True:
            f = open("input2.txt", "r")
            lines = f.readlines()

            for line in lines:
                line = line.strip().split() 
                if len(line) == 2 and not checkPrevious(preRequest, line[0]) and line[1] in {"HIGH", "CRITICAL", "NORMAL"}:
                    check = True    
                    for i in range(0, len(Menu)):
                        if Menu[i].name == line[0]: 
                            preRequest.append(Request(line[0], line[1], Menu[i].size, 0)) 
                            check = False
                            break
                    if check == True: preRequest.append(Request(line[0], line[1], 0, 0))
            f.close()
            time.sleep(2) 
    except KeyboardInterrupt:
        return
    finally:
        return
    
def PrintStatus(preRequest,n):
    for i in range(0, n):
        if preRequest[i].size == 0:
            print(preRequest[i].name + " "+ " " + "File not found")
        elif preRequest[i].progress == 1:
            print(preRequest[i].name + " "+ " " + "Downloaded Successfully")
        else:
            print(preRequest[i].name + " "+ " " + str(int(preRequest[i].progress * 100)) + "%")

    sys.stdout.write("\033[" + str(n) + "A")
    sys.stdout.flush()  
    

def mainProcess(s):
    time.sleep(0.5) 
    try:
        while True:
            n = len(preRequest)
            for i in range(0, n):
                if preRequest[i].size == 0 or preRequest[i].progress == 1: 
                    PrintStatus(preRequest,n) 
                    continue
                RealName = "output2/" + preRequest[i].name
                f = open(RealName, "ab") 
                cur_size = f.tell()
                if cur_size >= preRequest[i].size:
                    preRequest[i].progress = 1
                    PrintStatus(preRequest, n)
                    continue
                name_bytes = preRequest[i].name.encode('utf-8')
                s.sendall(len(name_bytes).to_bytes(4, byteorder = 'big'))
                s.sendall(name_bytes)
                priority_bytes = preRequest[i].priority.encode('utf-8')
                s.sendall(len(priority_bytes).to_bytes(4, byteorder = 'big'))
                s.sendall(priority_bytes)
                s.sendall(cur_size.to_bytes(4, byteorder = 'big'))

                data = s.recv(1024 * 10000)
                if not data:
                    break

                f.write(data)
                cur_size = f.tell()
                preRequest[i].progress = cur_size / preRequest[i].size
                f.close()

                PrintStatus(preRequest,n)

                if preRequest[i].progress < 1: 
                    all_done = False
                
            if all_done:

                done_msg = "DONE".encode('utf-8')
                s.sendall(len(done_msg).to_bytes(4, byteorder= 'big'))
                s.sendall(done_msg)
                break

    except KeyboardInterrupt: 
        return
    finally: 
        return
    

def main():
    server_ip = input("Enter the server IP address: ")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (server_ip, 3000)
    print('Connecting to port ' + str(server_address))


    Menu = []
    
    try: 
        s.connect(server_address)
        print ("SERVER CONNECTED\n")
        NumberOfFile_Menu = int.from_bytes(s.recv(4), byteorder = 'big')
        print('NUMBER OF FILES: ' + str(NumberOfFile_Menu) + '\n')
        
        for i in range(NumberOfFile_Menu):
            name_length = int.from_bytes(s.recv(4), byteorder = 'big')
            name = s.recv(name_length).decode('utf-8')
            size = int.from_bytes(s.recv(4), byteorder = 'big')
            Menu.append(menu(name, size))
        print("AVAILABLE FILES:")

        for i in range(0,NumberOfFile_Menu):
            print(Menu[i].name + " " + str(Menu[i].size))


        read_input = threading.Thread(target=readInputFile, args=(s, Menu ),daemon=True).start()
        main_process = threading.Thread(target=mainProcess, args=(s, ),daemon=True).start()

        
        while True:
            pass
    except KeyboardInterrupt or ConnectionResetError:
        print("\nCtrl+C pressed.")
    finally:
        print('Closing socket !')
        s.close()

main()
