# -*- coding: utf-8 -*-

from __future__ import print_function
from conf import *
from handler import *
from handler_t import *
from handler_t1 import *
from handler_t2 import *
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
            self.handler = FH(contr,contracts[contr])
            self.handler_t1 = Handler_T1()
            self.handler_t2 = Handler_T2()
            self.handler_t1.current_side = 'backward'
            self.handler_t2.current_side = 'forward'
            self.handler_a = Handler_A()
            self.handler_w = Handler_W()
            self.current_handler = 't'
            self.handler_t1.get_flag()
            self.handler_t2.get_flag()
            if not (FH.forward_position_size == 0 and FH.backward_position_size == 0):
                if FH.forward_position_size > FH.backward_position_size:
                    self.handler_t1.current_side = 'forward'
                    self.handler_t2.current_side = 'backward'
                    self.handler_t1.adjust_rt(FH.forward_position_size - FH.backward_position_size)
                    self.handler_t1.adjust_guide(FH.forward_position_size)
                    self.handler_t2.adjust_rt(-FH.backward_position_size / (FH.forward_position_size - FH.backward_position_size) * FH.tap)
                    self.handler_t2.adjust_guide(FH.backward_position_size)
                else:
                    self.handler_t1.current_side = 'backward'
                    self.handler_t2.current_side = 'forward'
                    self.handler_t1.adjust_rt(FH.backward_position_size - FH.forward_position_size)
                    self.handler_t1.adjust_guide(FH.backward_position_size)
                    self.handler_t2.adjust_rt(-FH.forward_position_size / (FH.backward_position_size - FH.forward_position_size) * FH.tap)
                    self.handler_t2.adjust_guide(FH.forward_position_size)
                FH.forward_limit = FH.forward_position_size
                FH.backward_limit = FH.backward_position_size
        f_exp.close()

    def get_handler(self):

        if FH.forward_position_size == 0 and FH.backward_position_size == 0:
            if self.current_handler != 't':
                self.handler_t1 = Handler_T1()
                self.handler_t2 = Handler_T2()
                self.handler_t1.current_side = 'backward'
                self.handler_t2.current_side = 'forward'
                self.current_handler = 't'
        elif self.current_handler == 't':
            if FH.forward_position_size == FH.backward_position_size:
                if not (FH.forward_position_size == 0 and FH.backward_position_size == 0):
                    self.handler_w = Handler_W()
                    self.current_handler = 'w'
            elif self.handler_t1.D_std > max(FH.forward_limit,FH.backward_limit) and self.handler_t2.D_std <= 0.0:
                if self.handler_t2.forward_gap_balance or self.handler_t2.backward_gap_balance \
                  or self.handler_t2.forward_catch or self.handler_t2.backward_catch:
                    if FH.stable_spread:
                        self.handler_a = Handler_A()
                        self.handler_a.current_side = self.handler_t2.current_side
                        self.current_handler = 'a'
        elif self.current_handler == 'a':
            if af(self.handler_a.D) == self.handler_a.D_std:
                self.handler_t1 = Handler_T1()
                self.handler_t2 = Handler_T2()
                if FH.forward_position_size > FH.backward_position_size:
                    self.handler_t1.current_side = 'forward'
                    self.handler_t2.current_side = 'backward'
                    self.handler_t1.adjust_rt(FH.forward_position_size - FH.backward_position_size)
                    self.handler_t1.adjust_guide(FH.forward_position_size)
                    self.handler_t2.adjust_rt(-FH.backward_position_size / (FH.forward_position_size - FH.backward_position_size) * FH.tap)
                    self.handler_t2.adjust_guide(FH.backward_position_size)
                else:
                    self.handler_t1.current_side = 'backward'
                    self.handler_t2.current_side = 'forward'
                    self.handler_t1.adjust_rt(FH.backward_position_size - FH.forward_position_size)
                    self.handler_t1.adjust_guide(FH.backward_position_size)
                    self.handler_t2.adjust_rt(-FH.forward_position_size / (FH.backward_position_size - FH.forward_position_size) * FH.tap)
                    self.handler_t2.adjust_guide(FH.forward_position_size)
                FH.forward_limit = FH.forward_position_size
                FH.backward_limit = FH.backward_position_size
                self.current_handler = 't'

    def run(self):
        try:
            if self.current_handler == 't':
                if self.handler_t1.get_flag() and self.handler_t2.get_flag():
                    self.get_handler()
                    if self.current_handler == 't':
                        print('aaaa', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.current_handler)
                        print(FH.balance_overflow, FH.margin, FH.goods_rt)
                        if FH.stable_spread:
                            if self.handler_t1.forward_balance_size >= FH.tap or self.handler_t1.forward_catch_size >= FH.tap \
                            or self.handler_t1.backward_balance_size >= FH.tap or self.handler_t1.backward_catch_size >= FH.tap:
                                self.handler_t1.put_position()
                            else:
                                self.handler_t2.put_position()
                        time.sleep(1)
                else:
                    print ('qqqq',mt5.last_error())
            elif self.current_handler == 'w':
                if self.handler_w.get_flag():
                    self.get_handler()
                    if self.current_handler == 'w':
                        print('aaaa', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.current_handler)
                        print(FH.balance_overflow, FH.margin, FH.goods_rt)
                        if FH.stable_spread:
                            self.handler_w.put_position();
                        time.sleep(1)
                else:
                    print ('qqqq',mt5.last_error())
            elif self.current_handler == 'a':
                if self.handler_a.get_flag():
                    self.get_handler()
                    if self.current_handler == 'a':
                        print('aaaa', time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), self.current_handler)
                        print(FH.balance_overflow, FH.margin, FH.goods_rt)
                        if FH.stable_spread:
                            self.handler_a.put_position();
                        time.sleep(1)
                else:
                    print ('qqqq',mt5.last_error())
        except Exception as e:
            traceback.print_exc()
            send_email(e)
