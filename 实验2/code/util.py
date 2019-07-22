# -*- coding: utf-8 -*-
'''
@author: xinghuazhang
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: xing_hua_zhang@126.com
@software: PyCharm 2017.1.4
@file: util.py
@time: 2018/5/1 14:43
@desc:
'''
# state
# has not been sent 0
# has been sent but not be acked 1
# has been acked 2
NOT_SENT = 0
SENT_NOT_ACKED = 1
ACKED = 2
# packet loss ratio
LOST_PACKET_RATIO = 0.25
# ip
CLIENT_IP = '127.0.0.1'
SERVER_IP = '127.0.0.1'
# port
SERVER_PORT_S = 10240
CLIENT_PORT_S = 10241
SERVER_PORT_R = 10242
CLIENT_PORT_R = 10243

class Data(object):

    def __init__(self, msg, seq=0, state=NOT_SENT, seq_num=10):
        self.msg = msg
        self.state = state
        self.seq = str(seq % seq_num)

    def __str__(self):
        return self.seq + '\tdata:' + self.msg
