# -*- coding: utf-8 -*-
'''
@author: xinghuazhang
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: xing_hua_zhang@126.com
@software: PyCharm 2017.1.4
@file: server.py
@time: 2018/5/1 15:47
@desc:
'''
import socket
import thread
import util
from gbn import GBN
from sr import SR
import argparse

def create_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='protocol(GBN or RS)')

    parser.add_argument(
        '--protocol', default=GBN, help='protocol name'
    )
    parser.add_argument(
        '--dual', default=False, help="whether dual transmission"
    )

    return parser

def server_send_data(server_port, client_ip, client_port, source_data, protocol, lock=None):
    # transport layer protocol is UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # set socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind ip address
    s.bind(('', server_port))
    # use protocol
    if protocol == 'GBN':
        p = GBN(s, host=client_ip)
    elif protocol == 'SR':
        p = SR(s, host=client_ip)
    # server as data sender sends data to client
    if lock:
        p.send_data(source_data, client_port, lock)
    else:
        p.send_data(source_data, client_port)
    #p.send_data(source_data, client_port, lock)

def server_receive_data(server_port, protocol):
    # transport layer protocol is UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # set socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind ip address
    s.bind(('', server_port))
    # use protocol
    if protocol == 'GBN':
        p = GBN(s)
    elif protocol == 'SR':
        p = SR(s)
    # server as data receiver receive data from client,
    # and then send ack back to client
    p.recv_data()


if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    if args.dual:
        lock1 = thread.allocate_lock()
        thread.start_new_thread(server_send_data, (util.SERVER_PORT_S, util.CLIENT_IP, \
                                                   util.CLIENT_PORT_R, 'sdata.txt', args.protocol, lock1))
        server_receive_data(util.SERVER_PORT_R, args.protocol)
        while lock1.locked():
            pass
    else:
        server_send_data(util.SERVER_PORT_S, util.CLIENT_IP, \
                                                   util.CLIENT_PORT_R, 'sdata.txt', args.protocol)
