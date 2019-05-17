# -*- coding: utf-8 -*-

import socket
import pickle
import argparse
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
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(SERVER_ADDR)

    # Get file name frame
    fname, client_addr = server_socket.recvfrom(BUFF_SIZE)
    print('==== START ====')
    print('File Name: ', pickle.loads(fname).data)
    filename = pickle.loads(fname).data

    # Get file size frame
    fsize, client_addr = server_socket.recvfrom(BUFF_SIZE)
    print('File Size: ', pickle.loads(fsize).data, ' B')
    filesize = pickle.loads(fsize).data

    # Get current time frame
    ftime, client_addr = server_socket.recvfrom(BUFF_SIZE)
    print('Current Time: ', pickle.loads(ftime).data)
    curr_time = pickle.loads(ftime).data

    # Get file
    with open(curr_time + '_' + filename, 'wb') as f:
        while True:
            # All file frames received
            frames = []
            # Receive file frames
            while True:
                frame, client_addr = server_socket.recvfrom(BUFF_SIZE)
                length = pickle.loads(frame).length
                data = pickle.loads(frame).data
                # Check if it's the end frame
                if length is None and data == 'END':
                    break
                # Check the length file frame
                if length != sys.getsizeof(data):
                    # If some data was lost, then resend the file frame
                    server_socket.sendto('resend'.encode(), client_addr)
                    print("continue")
                    continue
                else:
                    server_socket.sendto('ok'.encode(), client_addr)
                    frames.append(frame)
            # When the whole file is sent, check the final status
            # Check the number of frames
            if len(frames) != (filesize // FILE_FRAME_SIZE + 1):
                # If some frames were lost or duplicated, then resend all file frames
                server_socket.sendto('resend-all'.encode(), client_addr)
                continue
            else:
                server_socket.sendto('ok'.encode(), client_addr)
            # Sort the file frames by index
            frames.sort(key = (lambda fra : pickle.loads(fra).index))
            # Write received file frames to server's new file
            for frame in frames:
                f.write(pickle.loads(frame).data)
            print('====  END  ====', '\n')
            break
            
    # Close server socket
    server_socket.close()

if __name__ == '__main__':
    main()
