# -*- coding: utf-8 -*-

import socket
import pickle
import struct
import argparse
import threading
import time
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

def handle_connection(conn_socket, addr):
    """Handle connection from client"""

    print('==== START ====')

    # Get file name frame
    msg = recv_msg(conn_socket)
    print('File Name: ', pickle.loads(msg).data)
    filename = pickle.loads(msg).data

    # Get file size frame
    msg = recv_msg(conn_socket)
    print('File Size: ', pickle.loads(msg).data, ' B')
    filesize = pickle.loads(msg).data
    
    # Get current time frame
    msg = recv_msg(conn_socket)
    print('Current Time: ', pickle.loads(msg).data)
    curr_time = pickle.loads(msg).data

    # Get file
    with open(curr_time + '_' + filename, 'wb') as f:
        while True:
            msg = recv_msg(conn_socket)
            if msg == None:
                break
            frame = pickle.loads(msg)
            length = frame.length
            data = frame.data
            if length is None and data == 'END':
                print('====  END  ====', '\n')
                break
            else:
                f.write(data)

    # Close connection socket
    conn_socket.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', type=str, default='127.0.0.1', help='Server\'s IP address')
    parser.add_argument('--port', type=int, help='Port number')
    args = parser.parse_args()

    # Intialization
    SERVER_IP = args.ip
    SERVER_PORT = args.port
    SERVER_ADDR = (SERVER_IP, SERVER_PORT)

    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(SERVER_ADDR)
    server_socket.listen(10)

    # Thread ID
    tid = 0

    try:
        # Server is always running
        while True:
            # Get connection socket
            conn_socket, addr = server_socket.accept()

            # When a new connection comes, create a new thread
            tid += 1
            t = threading.Thread(target = handle_connection,
                                args = (conn_socket, addr),
                                name = ('thread-%d' % tid))
            t.start()
    finally:
        # Close server socket
        server_socket.close()

if __name__ == '__main__':
    main()
