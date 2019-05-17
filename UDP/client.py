# -*- coding: utf-8 -*-

import socket
import pickle
import argparse
import datetime
import sys

# Size of each file frame
FILE_FRAME_SIZE = 4096

# Buffer size
BUFF_SIZE = 2 * FILE_FRAME_SIZE

class Frame:
    def __init__(self, index, length, data):
        self.index = index
        self.length = length
        self.data = data

def get_file_size(filename):
    import os
    statinfo = os.stat(filename)
    return statinfo.st_size

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, default='127.0.0.1', help='Server\'s IP address')
    parser.add_argument('--port', type=int, help='Port number')
    parser.add_argument('--file', type=str, help='The file to transfer')
    args = parser.parse_args()

    # Intialization
    SERVER_IP = args.ip
    SERVER_PORT = args.port
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)
    filename = args.file

    # Create client socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Send file name frame
    fname = Frame(None, sys.getsizeof(filename), filename)
    client_socket.sendto(pickle.dumps(fname), SERVER_ADDR)

    # Send file size frame
    file_size = get_file_size(filename)
    fsize = Frame(None, sys.getsizeof(file_size), file_size)
    client_socket.sendto(pickle.dumps(fsize), SERVER_ADDR)

    # Send current time frame
    time_str = str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    curr_time = '_'.join(time_str.split())
    ftime = Frame(None, sys.getsizeof(curr_time), curr_time)
    client_socket.sendto(pickle.dumps(ftime), SERVER_ADDR)

    # Send file
    with open(filename, 'rb') as f:
        while True:
            # Index of each frame of file
            index = 0
            data = f.read(FILE_FRAME_SIZE)
            while (data):
                index += 1
                # Create file frame
                frame = Frame(index, sys.getsizeof(data), data)
                # Send file frame to server
                while (client_socket.sendto(pickle.dumps(frame), SERVER_ADDR)):
                    # Check status
                    status, server_addr = client_socket.recvfrom(BUFF_SIZE)
                    status = status.decode()
                    # If it's not ok, resend the file frame
                    if status == 'ok':
                        break
                    elif status == 'resend':
                        continue
                # Update data
                data = f.read(FILE_FRAME_SIZE)
            # Send the end frame
            end_frame = Frame(None, None, 'END')
            client_socket.sendto(pickle.dumps(end_frame), SERVER_ADDR)
            # When the whole file is sent, check the final status
            final_status, server_addr = client_socket.recvfrom(BUFF_SIZE)
            final_status = final_status.decode()
            if final_status == 'ok':
                break
            elif final_status == 'resend-all':
                f.seek(0, 0)
                continue

    # Close client socket
    client_socket.close()

if __name__ == '__main__':
    main()
