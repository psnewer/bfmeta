# -*- coding: utf-8 -*-

from __future__ import print_function
from conf import *
from handler import *
from handler_t import *
from handler_1t import *
from handler_0t import *
from handler_w import *
from handler_a import *
import sys
import traceback
import json
import codecs
import requests
import time

class Future_Manager(object):
    def __init__(self):
        f_exp = codecs.open('./bucket/experiment_ES.conf', 'r', encoding='utf-8')
        data_algs = json.load(f_exp)
        contracts = data_algs['contract']
        for contr in contracts:
            self.current_handler = FH(contr,contracts[contr])
            self.handler_t = Handler_T()
            if contracts[contr]['first_handler'] == 't':
                self.current_handler = self.handler_t
            elif contracts[contr]['first_handler'] == 'w':
                self.current_handler = Handler_W()
        f_exp.close()

    def get_handler(self):

        if self.current_handler.tip == 'w':
            if FH.forward_position_size == 0 and FH.backward_position_size == 0:
                self.handler_t = Handler_T()
                self.current_handler = self.handler_t
                self.current_handler.get_flag()
        elif self.current_handler.tip == 't':
            if self.current_handler.current_side == 'biside':
                if not (FH.forward_position_size == 0 and FH.backward_position_size == 0) or self.current_handler.rt_adjust:
                    self.current_handler = Handler_W()
                    self.current_handler.get_flag()
            elif af(self.current_handler.D_std) >= self.current_handler.top:
                if self.current_handler.forward_gap_balance or self.current_handler.backward_gap_balance \
                  or self.current_handler.forward_catch or self.current_handler.backward_catch:
                    if FH.stable_spread:
                        self.current_handler = Handler_A()
                        self.current_handler.get_flag()
        elif self.current_handler.tip == 'a':
            if af(self.current_handler.D) == self.current_handler.D_std:
                self.current_handler = self.handler_t
                self.current_handler.get_flag()
                self.current_handler.adjust_rt(af(self.current_handler.D))
                self.current_handler.get_flag()

    def run(self):
        if self.current_handler.get_flag():
            self.get_handler()
            print('aaaa', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.current_handler.tip)
            print(FH.balance_overflow, FH.margin, FH.goods_rt)
            #try:
            if FH.stable_spread:
                self.current_handler.put_position();
            time.sleep(1)
        else:
            print ('qqqq')
            #except Exception as e:
            #    traceback.print_exc()
            #    send_email(e)
