# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import numpy as np
from conf import *
from handler import *
from handler_0t import *

class Handler_T(FH):
    tap = 0.01

    def __init__(self):
        self.tip = 't'
        self.tap = Handler_T.tap
        self.T_rt = FH.tick_price / (FH.m5_hl * FH.T_level)
        Handler_T.T_rt = self.T_rt
        self.T_guide = 0.0

    def get_flag(self):

        self.get_std_flag()

        FH.forward_limit = FH.D_01
        FH.backward_limit = FH.D_01
        if FH.backward_position_size > FH.forward_position_size:
            FH.current_side = 'forward'
            self.D = FH.backward_position_size - FH.forward_position_size
        elif FH.forward_position_size > FH.backward_position_size:
            FH.current_side = 'backward'
            self.D = FH.forward_position_size - FH.backward_position_size
        else:
            FH.current_side = 'biside'
            self.D = 0.0

        self.get_side()

        self.D_std = self.T_guide - FH.goods_rt * self.T_rt

        if self.T_rt != Handler_T.T_rt:
            self.top = FH.D_01 - Handler_0T.tap
        else:
            self.top = FH.D_01

        print (FH.current_side,self.T_guide,self.T_rt)
        print(self.D, self.D_std, FH.forward_stable_price, FH.backward_stable_price)

        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if FH.balance:
            if len(FH.orders) == 0:
                if FH.current_side == 'backward':
                    if FH.tick_price > FH.t_dn:
                        if FH.forward_stable_price and self.D > self.D_std:
                            self.forward_gap_balance = True
                    elif FH.tick_price <= FH.t_up:
                        #if FH.t_b >= 0.0:
                        if FH.backward_stable_price and self.D < self.D_std:
                            self.backward_gap_balance = True
                elif FH.current_side == 'forward':
                    if FH.tick_price < FH.t_dn:
                        if FH.backward_stable_price and self.D > self.D_std:
                            self.backward_gap_balance = True
                    elif FH.tick_price >= FH.t_up:
                        #if FH.t_f >= 0.0:
                        if FH.forward_stable_price and self.D < self.D_std:
                            self.forward_gap_balance = True
                elif FH.current_side == 'biside':
                    self.adjust_guide(self.tap)
                    if  FH.tick_price >= FH.t_up:
                        if FH.forward_stable_price and self.D < self.D_std:
                            #if FH.t_f >= 0.0:
                            self.forward_gap_balance = True
                    elif FH.tick_price <= FH.t_dn:
                        if FH.backward_stable_price and self.D < self.D_std:
                            #if FH.t_b >= 0.0:
                            self.backward_gap_balance = True

        if self.forward_gap_balance:
            if FH.forward_position_size > 0.0:
                if FH.current_side == 'forward' or FH.current_side == 'biside':
                    self.forward_balance_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.forward_positions.iloc[0]['volume']))
                    self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                    print('d1', self.D_std-self.D, FH.forward_positions.iloc[0]['volume'])
                else:
                    #if FH.forward_positions.iloc[0]['profit'] < 0:
                    if False:
                        self.forward_balance_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='red',top=self.top), af(FH.forward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[0]['profit'])))))
                        self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                        print ('d2', self.D-self.D_std, FH.forward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[0]['profit'])))
                    else:
                        self.forward_balance_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='red',top=self.top), FH.forward_positions.iloc[0]['volume']))
                        self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
        if self.backward_gap_balance:
            if FH.backward_position_size > 0.0:
                if FH.current_side == 'backward' or FH.current_side == 'biside':
                    self.backward_balance_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.backward_positions.iloc[0]['volume']))
                    self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                    print ('d3', self.D_std-self.D, FH.backward_positions.iloc[0]['volume'])
                else:
                    #if FH.backward_positions.iloc[0]['profit'] < 0:
                    if False:
                        self.backward_balance_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='red',top=self.top), af(FH.backward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[0]['profit'])))))
                        self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                        print ('d4', self.D-self.D_std, FH.backward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[0]['profit'])))
                    else:
                        self.backward_balance_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='red',top=self.top), FH.backward_positions.iloc[0]['volume']))
                        self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])

        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        if FH.catch:
            if len(FH.orders) == 0:
                if FH.current_side == 'backward':
                    if  FH.tick_price <= FH.S_up:
                        if FH.backward_stable_price and self.D < self.D_std:
                            #if FH.t_b >= 0.0:
                                self.forward_catch = True
                                self.forward_catch_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.forward_limit-FH.forward_position_size))
                                print ('b1',self.D_std-self.D, FH.forward_limit-FH.forward_position_size)
                    elif FH.tick_price >= FH.S_dn:
                        if FH.forward_stable_price and self.D > self.D_std:
                            self.backward_catch = True
                            self.backward_catch_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='red',top=self.top), FH.forward_position_size-FH.backward_position_size))
                            print ('b2',self.D-self.D_std, FH.backward_limit-FH.backward_position_size)
                elif FH.current_side == 'forward':
                    if FH.tick_price >= FH.S_up:
                        if FH.forward_stable_price and self.D < self.D_std:
                            #if FH.t_f >= 0.0:
                                self.backward_catch = True
                                self.backward_catch_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.backward_limit-FH.backward_position_size))
                                print ('b3',self.D_std-self.D, FH.backward_limit-FH.backward_position_size)
                    elif FH.tick_price <= FH.S_dn:
                        if FH.backward_stable_price and self.D > self.D_std:
                            self.forward_catch = True
                            self.forward_catch_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='red',top=self.top), FH.backward_position_size-FH.forward_position_size))
                            print ('b4',self.D-self.D_std, FH.forward_limit-FH.forward_position_size)
                elif FH.current_side == 'biside':
                    self.adjust_guide(self.tap)
                    if  FH.tick_price <= FH.S_dn:
                        if FH.backward_stable_price and self.D < self.D_std:
                            #if FH.t_b >= 0.0:
                            self.forward_catch = True
                            self.forward_catch_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.forward_limit-FH.forward_position_size))
                    elif FH.tick_price >= FH.S_up:
                        if FH.forward_stable_price and self.D < self.D_std:
                            #if FH.t_f >= 0.0:
                            self.backward_catch = True
                            self.backward_catch_size = af(min(cutoff(self.tap,0,self.D,self.D_std,der='inc',top=self.top), FH.backward_limit-FH.backward_position_size))

    def put_position(self):

        self.forward_increase_clear = False
        self.forward_reduce_clear = False
        self.backward_increase_clear = False
        self.backward_reduce_clear = False
        for order in FH.orders:
            order_price = float(order.price_open)
            order_type = order.type
            order_id = order.ticket
            order_magic = order.magic
            if order_magic == 0:
                if order_type is mt5.ORDER_TYPE_BUY:
                    self.forward_increase_clear = True
                elif order_type is mt5.ORDER_TYPE_SELL:
                    self.backward_increase_clear = True
            elif order_magic == 1000:
                if order_type is mt5.ORDER_TYPE_BUY:
                    self.backward_reduce_clear = True
                elif order_type is mt5.ORDER_TYPE_SELL:
                    self.forward_reduce_clear = True
            elif order_magic == 1001:
                self.forward_reduce_clear = True
                self.backward_reduce_clear = True
            if order_type is mt5.ORDER_TYPE_BUY and order_magic == 0:
                if self.forward_catch:
                    if FH.ask_1 > order_price:
                        mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                else:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
            elif order_type is mt5.ORDER_TYPE_SELL and order_magic == 1000:
                if self.forward_gap_balance:
                    if order_price > FH.bid_1:
                        mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                else:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})

            if order_type is mt5.ORDER_TYPE_SELL and order_magic == 0:
                if self.backward_catch:
                    if FH.bid < order_price:
                        mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                else:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
            elif order_type is mt5.ORDER_TYPE_SELL and order_magic == 1000:
                if self.backward_gap_balance:
                    if order_price < FH.ask_1:
                        mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                else:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})

        if len(FH.orders) == 0:
                if not self.forward_increase_clear:
                    if FH.forward_position_size < FH.limit_size:
                        if self.forward_catch and self.forward_catch_size > 0:
                            mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
                                            "type": mt5.ORDER_TYPE_BUY, "volume": self.forward_catch_size,
                                            "price": FH.ask_1, "deviation": 10, "magic": 0})
                if not self.forward_reduce_clear and self.forward_gap_balance:
                    if FH.forward_position_size > 0:
                        if self.forward_balance_size > 0:
                            mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
                                            "type": mt5.ORDER_TYPE_SELL, "position": self.forward_balance_ticket,
                                            "volume": self.forward_balance_size, "price": FH.bid_1,
                                            "deviation": 10, "magic": 1000})

                if not self.backward_increase_clear:
                    if FH.backward_position_size < FH.limit_size:
                        if self.backward_catch and self.backward_catch_size > 0:
                            mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
                                            "type": mt5.ORDER_TYPE_SELL, "volume": self.backward_catch_size,
                                            "price": FH.bid_1, "deviation": 10, "magic": 0})
                if not self.backward_reduce_clear and self.backward_gap_balance:
                    if FH.backward_position_size > 0:
                        if self.backward_balance_size > 0:
                            mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
                                            "type": mt5.ORDER_TYPE_BUY, "position": self.backward_balance_ticket,
                                            "volume": self.backward_balance_size, "price": FH.ask_1,
                                            "deviation": 10, "magic": 1000})

    def adjust_guide(self,D_std):
        self.T_guide += D_std - (self.T_guide - FH.goods_rt / self.T_rt)
        self.D_std = D_std

    def adjust_rt(self,D_std):
        self.T_rt = (self.T_guide - D_std) / FH.goods_rt
        self.D_std = D_std


