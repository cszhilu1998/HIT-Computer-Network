# -*- coding: utf-8 -*-
'''
@author: xinghuazhang
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: xing_hua_zhang@126.com
@software: PyCharm 2017.1.4
@file: sr.py
@time: 2018/5/1 16:38
@desc:
'''
import util
import select
from random import random
import time

class SR(object):
    """
    SR protocol, including sender and receiver implementation
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
        #clock = 0
        clock = {}
        seq = 0
        window = []
        # start transport source data to target server
        with open(source_data, 'r') as f:
            while True:
                # timeout, reset all data in window into NOT_SENT
                now_time = time.time()
                #print now_time
                ll=[]
                for k in clock:
                    if now_time - clock[k] > self.delay_time:
                        print '-----------------timeout------------------'
                        for data in window:
                            if data.state == util.SENT_NOT_ACKED:
                                ll.append(str(data.seq))
                                data.state = util.NOT_SENT
                                break  ### difference from GBN ###
                for k in ll:
                    clock.pop(k)
                # if window has space, and then append new data
                while len(window) < self.window_size:
                    line = f.readline().strip()
                    if not line:
                        break
                    data = util.Data(line, seq=seq)
                    window.append(data)
                    seq += 1

                if not window:
                    break
                # intercept all data in window and sent data in NOT_SENT state
                for data in window:
                    if not data.state:
                        # UDP use sendto method
                        self.s.sendto(str(data), (self.host, trgt_port))
                        clock[str(data.seq)] = time.time()
                        data.state = util.SENT_NOT_ACKED

                # use select method to listen socket (non-blocked)
                readable_list, writeable_list, errors = select.select([self.s, ], [], [], 1)
                # if trgt server send data back(such as ack)
                if len(readable_list) > 0:
                    # simulate ack loss
                    if random() < util.LOST_PACKET_RATIO:
                        #clock += 1
                        #print('ack loss')
                        continue
                    # receive ack and reset clock to zero
                    #clock = 0
                    try:
                        ack_message, address = self.s.recvfrom(self.buffer_size)
                        print 'ACK seq:' + ack_message
                        clock.pop(ack_message)
                        # after receiving ack, change into ACKED state
                        for data in window:
                            if ack_message == data.seq:
                                data.state = util.ACKED
                                break
                    except BaseException, e:
                        pass
                else:
                    #clock += 1
                    pass

                # slide window
                while window[0].state == util.ACKED:
                    window.pop(0)
                    if not window:
                        break

        self.s.close()
        if lock:
            lock.release()

    def recv_data(self):
        """
        receiver implementation: receive data and send ack
        :return: None
        """
        # record base seq num in receiver window
        seq = 0
        window = {}
        while True:
            # use select method to listen socket (non-blocked)
            readable_list, writeable_list, errors = select.select([self.s, ], [], [], 1)
            # if source server send data
            if len(readable_list) > 0:
                message, address = self.s.recvfrom(self.buffer_size)
                ack = message.split()[0]
                # simulate data loss
                if random() < util.LOST_PACKET_RATIO:
                    continue
                if ack in self.__sr_valid_acklist(seq):
                    print (message)
                    self.s.sendto(ack, address)
                    window[ack] = message.split()[1]
                    # slide window
                    while str(seq) in window:
                        print(str(seq) + ' ' + window[str(seq)] + '(Delivery to the upper level)')
                        window.pop(str(seq))
                        seq = (seq + 1) % self.seq_num
                elif ack in self.__sr_old_acklist(seq):
                    #print(message)
                    self.s.sendto(ack, address)
                else:
                    pass

        self.s.close()

    def __sr_valid_acklist(self, base):
        """
        receiver window seq from base to base+window_size-1
        :param base: window of receiver left seq
        :return: ret(all window seq num)
        """
        ret = []
        end = base + self.window_size - 1
        while base <= end:
            ret.append(str(base % self.seq_num))
            base += 1
        return ret

    def __sr_old_acklist(self, base):
        """
        receiver window seq from base-window to base-1(avoid ack loss)
        :param base: window of receiver left seq
        :return: ret(old all window seq num)
        """
        ret = []
        begin = base - self.window_size   # unc;
        end = base - 1
        while begin <= end:
            ret.append(str(begin % self.seq_num))
            begin += 1
        return ret
