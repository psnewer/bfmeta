# -*- coding: utf-8 -*-

from __future__ import print_function
from conf import *
from handler import *
from handler_t import *
from handler_1t import *
from handler_w import *
from handler_f import *
import sys
import json
import codecs
import requests
import time

class Future_Manager(object):
    def __init__(self):
        f_exp = codecs.open('./bucket/experiment_EURUSD.conf', 'r', encoding='utf-8')
        data_algs = json.load(f_exp)
        contracts = data_algs['contract']
        for contr in contracts:
            self.handler = FH(contr,contracts[contr])
            self.handler_t = Handler_T()
            self.handler_1t = Handler_1T()
            self.handler_w = Handler_W()
            self.handler_f = Handler_F()
            if contracts[contr]['first_handler'] == 't':
                self.current_handler = self.handler_t
            elif contracts[contr]['first_handler'] == 'w':
                self.current_handler = self.handler_w
            elif contracts[contr]['first_handler'] == 'f':
                self.current_handler = self.handler_f
            self.current_handler.get_flag()
        f_exp.close()

    def get_handler(self):
        print ('aaaa',time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),self.current_handler.tip)
        print (FH.goods,FH.balance_overflow,FH.forward_goods+FH.backward_goods+FH.balance_overflow,FH.endure_goods,FH.goods_rt)
        if FH.forward_position_size == 0 and FH.backward_position_size == 0:
            FH.catch = False
            FH.balance = False
            self.current_handler = self.handler_f
        elif FH.forward_goods + FH.backward_goods + FH.balance_overflow > FH.endure_goods:
            FH.catch = False
            FH.balance = False
            self.current_handler = self.handler_w
        elif self.current_handler.tip == 'w':
            if FH.forward_goods + FH.backward_goods + FH.balance_overflow < 0.0:
                FH.catch = False
                FH.balance = False
                self.current_handler = self.handler_t
        elif  self.current_handler.tip == 'f':
            if FH.forward_position_size >= FH.limit_size and FH.backward_position_size >= FH.limit_size:
                FH.catch = False
                FH.balance = False
                self.current_handler = self.handler_t

    def run(self):
        self.get_handler()
        try:
            self.current_handler.get_flag();
            self.current_handler.put_position();
            time.sleep(1)
        except Exception as e:
            print("Exception when calling FuturesApi: %s\n" % e)
            send_email(e)
#            dic_clear = True
#
#            try:
#                body_dic = json.loads(e.body)
#            except Exception:
#                send_email(e)
#                dic_clear = False
#
#            if dic_clear:
#                e_sig = True
#                if 'label' in body_dic:
#                    if body_dic['label'] in ['ORDER_POC_IMMEDIATE','ORDER_NOT_FOUND','INCREASE_POSITION','INSUFFICIENT_AVAILABLE']:
#                        e_sig = False
#                    else:
#                        e_sig = True
#                if e_sig and 'detail' in body_dic:
#                    if body_dic['detail'] == 'invalid argument: #3':
#                        e_sig = False
#                    else:
#                        e_sig = True
#                if e_sig:
#                    print ('e_sig')
#                    send_email(e)