# -*- coding: utf-8 -*-
'''
@author: xinghuazhang
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: xing_hua_zhang@126.com
@software: PyCharm 2017.1.4
@file: gbn.py
@time: 2018/5/1 1:34
@desc:
'''
import util
import select
from random import random


class GBN(object):
    """
    GBN protocol, including sender and receiver implementation
    """
    def __init__(self, s, host='127.0.0.1', buffer_size=1024, window_size=4, \
                 seq_num=10, delay_time=3):
        """
        :param s: source socket
        :param host: target host
        :param buffer_size: buffer size
        :param window_size: sliding window size
        :param seq_num: maximum seq_num
        :param delay_time: allowed maximum delayed time
        """
        self.s = s
        self.host = host
        self.buffer_size = buffer_size
        self.window_size = window_size
        self.seq_num = seq_num
        self.delay_time = delay_time

    def send_data(self, source_data, trgt_port, lock=None):
        """
        sender implementation: send data and receive ack
        :param source_data: data
        :param trgt_port: target port and default host is '127.0.0.1'
        :return: None
        """
        if lock:
            lock.acquire()
        # inital clock, seq and window
        clock = 0
        seq = 0
        window = []
        # start transport source data to target server
        with open(source_data, 'r') as f:
            while True:
                # timeout, reset all data in window into NOT_SENT
                if clock > self.delay_time:
                    print '---------------timeout-----------------'
                    clock = 0
                    for data in window:
                        data.state = util.NOT_SENT

                # if window has space, and then append new data
                while len(window) < self.window_size:
                    line = f.readline().strip()
                    if not line:
                        break
                    # construct data frame
                    data = util.Data(line, seq=seq)
                    window.append(data)
                    #print(seq)
                    seq += 1


                if not window:
                    break
                # intercept all data in window and sent data in NOT_SENT state
                for data in window:
                    if data.state == util.NOT_SENT:
                        # UDP use sendto method
                        self.s.sendto(str(data), (self.host, trgt_port))
                        data.state = util.SENT_NOT_ACKED

                # use select method to listen socket (non-blocked)
                readable_list, writeable_list, errors = select.select([self.s, ], [], [], 1)
                # if trgt server send data back(such as ack)
                if len(readable_list) > 0:
                    # simulate ack loss
                    #print('wait')
                    if random() < util.LOST_PACKET_RATIO:
                        #print('ack loss')
                        continue
                    # receive ack and reset clock to zero
                    #clock = 0
                    try:
                        # UDP use recvfrom method to receive data
                        ack_message, address = self.s.recvfrom(self.buffer_size)
                        print 'ACK seq:' + ack_message
                        # receive ack and then change window(slide window)
                        for i in range(len(window)):
                            # seq <= ack we think has in ACKED state
                            if ack_message == window[i].seq:
                                clock = 0
                                window = window[i + 1:]
                                break
                    except BaseException,e:
                        #print('error')
                        pass
                else:
                    clock += 1

        self.s.close()
        if lock:
            lock.release()

    def recv_data(self):
        """
        receiver implementation: receive data and send ack
        :return: None
        """
        # record last ack
        last_ack = self.seq_num - 1
        window = []

        while True:
            # use select method to listen socket (non-blocked)
            readable_list, writeable_list, errors = select.select([self.s, ], [], [], 1)
            # if source server send data
            if len(readable_list) > 0:
                message, address = self.s.recvfrom(self.buffer_size)
                # data format seq \t data
                ackseq = int(message.split()[0])
                # no packet loss
                if last_ack == (ackseq - 1) % self.seq_num:
                    # stimulate packet loss
                    if random() < util.LOST_PACKET_RATIO:
                        continue
                    # send ack
                    self.s.sendto(str(ackseq), address)
                    last_ack = ackseq

                    # if has been received the data(not necessary)
                    if ackseq not in window:
                        window.append(ackseq)
                        print message
                    while len(window) > self.window_size:
                        window.pop(0)
                else:
                    self.s.sendto(str(last_ack), address)

        self.s.close()
