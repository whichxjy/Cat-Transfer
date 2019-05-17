# -*- coding: utf-8 -*-

import socket
import pickle
import datetime
import argparse
import struct
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

def recv_all(sock, n):
    """Helper function to recv n bytes or return None if EOF is hit"""
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def recv_msg(sock):
    """Receive message from socket"""
    # Read message length and unpack it into an integer
    raw_msglen = recv_all(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('!I', raw_msglen)[0]
    # Read the message data
    return recv_all(sock, msglen)

def frame2pack(frame):
    """Convert frame to package"""
    dump_frame = pickle.dumps(frame)
    package = struct.pack('!I', len(dump_frame)) + dump_frame
    return package

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
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(SERVER_ADDR)
    
    # Send file name frame
    fname = Frame(None, sys.getsizeof(filename), filename)
    client_socket.sendall(frame2pack(fname))

    # Send file size frame
    file_size = get_file_size(filename)
    fsize = Frame(None, sys.getsizeof(file_size), file_size)
    client_socket.sendall(frame2pack(fsize))

    # Send current time frame
    time_str = str(datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    curr_time = "_".join(time_str.split())
    ftime = Frame(None, sys.getsizeof(curr_time), curr_time)
    client_socket.sendall(frame2pack(ftime))

    # Send file
    with open(filename, 'rb') as f:
        # Index of each frame of file
        index = 0
        data = f.read(FILE_FRAME_SIZE)
        while (data):
            # Create file frame
            frame = Frame(index, sys.getsizeof(data), data)
            # Send file frame to server
            client_socket.sendall(frame2pack(frame))
            # Update data
            data = f.read(FILE_FRAME_SIZE)
        # Send the end frame
        end_frame = Frame(None, None, 'END')
        client_socket.sendall(frame2pack(end_frame))

    # Close client socket
    client_socket.close()

if __name__ == '__main__':
    main()
