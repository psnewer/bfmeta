# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import numpy as np
from conf import *
from handler import *
from handler_t import *

class Handler_0T(FH):
    tap = 0.04

    def __init__(self):
        self.tip = '0t'
        self.tap = 0.04
        self.margin = 0.0
        self.T_guide_up = 0.0
        self.T_guide_dn = 0.0
        self.T_rt_up = FH.tick_price / (FH.h1_oc * FH.T_level)
        self.T_rt_dn = FH.tick_price / (FH.h1_oc * FH.T_level)

    def get_flag(self):

        self.get_std_flag()

        FH.forward_limit = FH.limit_size
        FH.backward_limit = FH.limit_size
        if FH.forward_goods > FH.backward_goods:
            FH.current_side = 'forward'
            self.margin = FH.forward_goods + FH.balance_overflow
            self.D = FH.forward_position_size - FH.backward_position_size
        elif FH.forward_goods < FH.backward_goods:
            FH.current_side = 'backward'
            self.margin = FH.backward_goods + FH.balance_overflow
            self.D = FH.backward_position_size - FH.forward_position_size
        else:
            FH.current_side = 'biside'
            self.margin = 0.0
            self.D = 0.0

        self.get_side()

        self.goods_rt = self.margin / FH.unit_value * FH.T_level
        self.D_up = self.T_guide_up + self.T_rt_up * self.goods_rt
        self.D_dn = self.T_guide_dn + self.T_rt_dn * self.goods_rt

        if self.D_up >= af(-FH.D_01 + FH.N0 * Handler_0T.tap):
            self.adjust_guide(-FH.D_01 + Handler_0T.tap)

        self.bot = -FH.D_01 + self.tap
        if cutoff(self.tap, -FH.D_01 + self.tap, self.D, self.D_up, der='inc', bot=self.bot) >= self.tap:
            self.T_guide_dn += self.D_up - self.D_dn
        elif cutoff(self.tap, -FH.D_01 + self.tap, self.D, self.D_dn, der='red', bot=self.bot) >= af(self.D + (FH.D_01 - self.tap)):
            self.T_guide_up += self.D_dn - self.D_up

        if self.D_up >= self.D:
            self.D_std = self.D_up
            self.put_tap = self.tap
        else:
            self.D_std = self.D_dn
            self.put_tap = af(self.D + (FH.D_01 - self.tap)) if af(self.D + (FH.D_01 - self.tap)) > 0.0 else self.tap

        print (FH.current_side,self.T_guide_up,self.T_guide_dn,FH.balance_overflow,self.margin,self.goods_rt)
        print (self.D,self.D_up,self.D_dn,FH.forward_stable_price,FH.backward_stable_price)

        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if True:
            if len(FH.orders) == 0:
                if FH.current_side == 'backward':
                        if FH.backward_stable_price and self.D > self.D_std:
                            self.backward_gap_balance = True
                        if FH.stable_spread and self.D < self.D_std:
                            self.forward_gap_balance = True
                elif FH.current_side == 'forward':
                        if FH.forward_stable_price and self.D > self.D_std:
                            self.forward_gap_balance = True
                        if FH.stable_spread and self.D < self.D_std:
                            self.backward_gap_balance = True

        if self.forward_gap_balance:
            if FH.forward_position_size > 0.0:
                if FH.current_side == 'forward':
                    self.forward_balance_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='red',bot=self.bot), FH.forward_positions.iloc[0]['volume']))
                    self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                    print('d1', self.D-self.D_std, FH.forward_positions.iloc[0]['volume'])
                else:
                    if FH.forward_positions.iloc[0]['profit'] < 0:
                        self.forward_balance_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), af(FH.forward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[0]['profit'])))))
                        self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                        print ('d2', self.D_std-self.D, FH.forward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[0]['profit'])))
                    else:
                        self.forward_balance_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), FH.forward_positions.iloc[0]['volume']))
                        self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                        print('d2',self.D_std-self.D, FH.forward_positions.iloc[0]['volume'])
        if self.backward_gap_balance:
            if FH.backward_position_size > 0.0:
                if FH.current_side == 'backward':
                    self.backward_balance_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='red',bot=self.bot), FH.backward_positions.iloc[0]['volume']))
                    self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                    print ('d3', self.D-self.D_std, FH.backward_positions.iloc[0]['volume'])
                else:
                    if FH.backward_positions.iloc[0]['profit'] < 0:
                        self.backward_balance_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), af(FH.backward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[0]['profit'])))))
                        self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                        print ('d4', self.D_std-self.D, FH.backward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[0]['profit'])))
                    else:
                        self.backward_balance_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), FH.backward_positions.iloc[0]['volume']))
                        self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                        print ('d4',self.D_std-self.D, FH.backward_positions.iloc[0]['volume'])

        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        if True:
            if len(FH.orders) == 0:
                if FH.current_side == 'backward':
                    #if  (FH.catch and FH.tick_price <= FH.S_up) or (FH.balance and FH.tick_price <= FH.t_up):
                        if FH.stable_spread and self.D < self.D_std:
                            #if FH.t_b >= 0.0:
                                self.backward_catch = True
                                self.backward_catch_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), FH.backward_limit-FH.backward_position_size))
                                print ('b1',self.D_std-self.D, FH.backward_limit-FH.backward_position_size)
                    #elif (FH.catch and FH.tick_price >= FH.S_dn) or (FH.balance and FH.tick_price >= FH.t_dn):
                        if FH.stable_spread and self.D > self.D_std:
                            self.forward_catch = True
                            self.forward_catch_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='red',bot=self.bot), FH.forward_limit-FH.forward_position_size))
                            print ('b2',self.D-self.D_std, FH.forward_limit-FH.forward_position_size)
                elif FH.current_side == 'forward':
                    #if (FH.catch and FH.tick_price >= FH.S_up) or (FH.balance and FH.tick_price >= FH.t_up):
                        if FH.stable_spread and self.D < self.D_std:
                            #if FH.t_f >= 0.0:
                                self.forward_catch = True
                                self.forward_catch_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='inc',bot=self.bot), FH.forward_limit-FH.forward_position_size))
                                print ('b3',self.D_std-self.D, FH.forward_limit-FH.forward_position_size)
                    #elif (FH.catch and FH.tick_price <= FH.S_dn) or (FH.balance and FH.tick_price <= FH.t_dn):
                        if FH.stable_spread and self.D > self.D_std:
                            self.backward_catch = True
                            self.backward_catch_size = af(min(cutoff(self.put_tap,-FH.D_01 + self.tap,self.D,self.D_std,der='red',bot=self.bot), FH.backward_limit-FH.backward_position_size))
                            print ('b4',self.D-self.D_std, FH.backward_limit-FH.backward_position_size)

        if FH.current_side == 'forward' and self.backward_catch_size > 0.0:
            self.backward_catch = False
        elif FH.current_side == 'backward' and self.forward_catch_size > 0.0:
            self.forward_catch = False
        if FH.current_side == 'forward' and self.backward_balance_size > 0.0:
            self.backward_gap_balance = False
        elif FH.current_side == 'backward' and self.forward_balance_size > 0.0:
            self.forward_gap_balance = False

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
        self.T_guide_up += D_std - (self.T_guide_up + self.T_rt_up * self.goods_rt)
        self.T_guide_dn += D_std - (self.T_guide_dn + self.T_rt_dn * self.goods_rt)
        self.D_std = D_std

