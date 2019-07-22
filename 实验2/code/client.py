# -*- coding: utf-8 -*-
'''
@author: xinghuazhang
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: xing_hua_zhang@126.com
@software: PyCharm 2017.1.4
@file: client.py
@time: 2018/5/1 16:15
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

def client_send_data(client_port, server_ip, server_port, source_data, protocol, lock=None):
    # transport layer protocol is UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # set socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind ip address
    s.bind(('', client_port))
    # use protocol
    if protocol == 'GBN':
        p = GBN(s, host=server_ip)
    elif protocol == 'SR':
        p = SR(s, host=server_ip)
    #p = protocol(s, host=server_ip)
    # client as data sender sends data to server
    if lock:
        p.send_data(source_data, server_port, lock)
    else:
        p.send_data(source_data, server_port)

def client_receive_data(client_port, protocol):
    # transport layer protocol is UDP
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # set socket
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind ip address
    s.bind(('', client_port))
    # use protocol
    if protocol == 'GBN':
        p = GBN(s)
        #p = protocol(s)
    elif protocol == 'SR':
        p = SR(s)
    # client as data receiver receive data from server,
    # and then send ack back to server
    p.recv_data()

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    if args.dual:
        lock1 = thread.allocate_lock()
        print
        thread.start_new_thread(client_send_data, (util.CLIENT_PORT_S, util.SERVER_IP, \
                                              util.SERVER_PORT_R, 'cdata.txt', args.protocol, lock1))
        client_receive_data(util.CLIENT_PORT_R, args.protocol)
        while lock1.locked():
            pass
    else:
        client_receive_data(util.CLIENT_PORT_R, args.protocol)
