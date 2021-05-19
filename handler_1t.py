# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import numpy as np
from conf import *
from handler import *

class Handler_1T(FH):
    def __init__(self):
        self.tip = '1t'
        self.current_side = 'biside'
        self.pre_side = 'biside'
        self.T_rt_up = 5
        self.T_rt_dn = 10
        self.T_guide_up = 0.0
        self.T_guide_dn = 0.0

    def get_flag(self):

        self.get_std_flag()

        if FH.backward_position_size < FH.forward_position_size:
            self.current_side = 'forward'
            self.D = FH.forward_position_size - FH.backward_position_size
        elif FH.forward_position_size < FH.backward_position_size:
            self.current_side = 'backward'
            FH.step_soft = -FH.step_soft
            self.D = FH.backward_position_size - FH.forward_position_size
        else:
            self.current_side = 'biside'
            self.D = 0.0

        if self.current_side != self.pre_side:
            self.pre_side = self.current_side
            if self.current_side == 'biside':
                FH.catch = False
                FH.balance = False

        FH.goods_rt = FH.margin / FH.limit_value * 400
        self.T_std_up = self.T_guide_up + self.T_rt_up * FH.goods_rt
        self.T_std_dn = self.T_guide_dn + self.T_rt_dn * FH.goods_rt
        self.D_up = FH.limit_size * self.T_std_up
        self.D_dn = FH.limit_size * self.T_std_dn
        if self.D_up >= self.D + FH.tap:
            self.T_guide_dn += self.T_std_up - self.T_std_dn
            self.D_std = self.D_up
        elif self.D_dn <= self.D - FH.tap:
            self.T_guide_up += self.T_std_dn - self.T_std_up
            self.D_std = self.D_dn
        else:
            self.D_std = self.D

        #if self.D == 0.0:
        #    FH.pre_D_std = 0.0
        #    self.T_rt_dn = 1
        #    self.T_guide_dn += FH.T_std - (self.T_guide_dn + self.T_rt_dn * FH.goods_rt)
        #if self.D_std > FH.pre_D_std:
        #    FH.pre_D_std = self.D_std
        #    self.T_rt_dn = 1 + FH.pre_D_std / FH.limit_size * 5
        #    self.T_guide_dn += FH.T_std - (self.T_guide_dn + self.T_rt_dn * FH.goods_rt)
        #if FH.T_std < 0.0:
        #    FH.T_guide += 0.0 - FH.T_std
        #    FH.T_std = 0.0
        if self.T_std_up > 1.0:
            self.T_guide_up += 1.0 - self.T_std_up
            self.T_guide_dn += 1.0 - self.T_std_dn
            self.T_std_up = 1.0
            self.T_std_dn = 1.0


        print (self.current_side,self.T_guide_up,self.T_guide_dn,self.T_rt_up,self.T_rt_dn)
        print (self.T_std_up,self.T_std_dn,self.D,self.D_up,self.D_dn,FH.stable_spread)

        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if FH.balance:
            if len(FH.orders) == 0:
                if self.current_side == 'backward':
                    #if FH.tick_price >= FH.t_dn:
                    if FH.stable_spread and self.D > self.D_std:
                        self.backward_gap_balance = True
                    #elif FH.tick_price <= FH.t_up:
                        #if FH.t_b >= 0.0:
                    if FH.stable_spread and self.D < self.D_std:
                        self.forward_gap_balance = True
                elif self.current_side == 'forward':
                    #if FH.tick_price <= FH.t_dn:
                    if FH.stable_spread and self.D > self.D_std:
                        self.forward_gap_balance = True
                    #elif FH.tick_price >= FH.t_up:
                        #if FH.t_f >= 0.0:
                    if FH.stable_spread and self.D < self.D_std:
                        self.backward_gap_balance = True
                elif self.current_side == 'biside':
                    self.T_guide_up += FH.tap / FH.limit_size - self.T_std_up
                    self.T_guide_dn += FH.tap / FH.limit_size - self.T_std_dn
                    self.T_std_up = FH.tap / FH.limit_size
                    self.T_std_dn = FH.tap / FH.limit_size
                    self.D_std = FH.tap
                    if  FH.tick_price >= FH.t_up:
                        if FH.stable_spread and self.D < self.D_std:
                            #if FH.t_f >= 0.0:
                            self.backward_gap_balance = True
                    elif FH.tick_price <= FH.t_dn:
                        if FH.stable_spread and self.D < self.D_std:
                            #if FH.t_b >= 0.0:
                            self.forward_gap_balance = True

        if self.forward_gap_balance:
            if FH.forward_position_size > 0.0:
                if self.current_side == 'forward':
                    self.forward_balance_size = int(min(self.D-self.D_std, FH.forward_positions.iloc[0]['volume'])*100+0.001)/100.0
                    self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                    print('d1', self.D-self.D_std, FH.forward_positions.iloc[0]['volume'])
                else:
                    #if FH.forward_positions.iloc[0]['profit'] < 0:
                    if False:
                        self.forward_balance_size = int(min(self.D_std-self.D, FH.forward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[0]['profit'])))*100+0.001)/100.0
                        self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                        print ('d2', self.D_std-self.D, FH.forward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[0]['profit'])))
                    else:
                        self.forward_balance_size = int(min(self.D_std-self.D, FH.forward_positions.iloc[0]['volume']) * 100 + 0.001) / 100.0
                        self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                        print('d2',self.D_std-self.D, FH.forward_positions.iloc[0]['volume'])
        if self.backward_gap_balance:
            if FH.backward_position_size > 0.0:
                if self.current_side == 'backward':
                    self.backward_balance_size = int(min(self.D-self.D_std, FH.backward_positions.iloc[0]['volume'])*100+0.001)/100.0
                    self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                    print ('d3', self.D-self.D_std, FH.backward_positions.iloc[0]['volume'])
                else:
                    #if FH.backward_positions.iloc[0]['profit'] < 0:
                    if False:
                        self.backward_balance_size = int(min(self.D_std-self.D, FH.backward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[0]['profit'])))*100+0.001)/100.0
                        self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                        print ('d4', self.D_std-self.D, FH.backward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[0]['profit'])))
                    else:
                        self.backward_balance_size = int(min(self.D_std-self.D, FH.backward_positions.iloc[0]['volume']) * 100 + 0.001) / 100.0
                        self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                        print ('d4',self.D_std-self.D, FH.backward_positions.iloc[0]['volume'])

        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        if FH.catch:
            if len(FH.orders) == 0:
                if self.current_side == 'backward':
                    #if  FH.tick_price <= FH.S_up:
                        if FH.stable_spread and self.D < self.D_std:
                            #if FH.t_b >= 0.0:
                                self.backward_catch = True
                                self.backward_catch_size = int(min(self.D_std-self.D, FH.backward_limit-FH.backward_position_size)*100+0.001)/100.0
                                print ('b1',self.D_std-self.D, FH.backward_limit-FH.backward_position_size)
                    #elif FH.tick_price >= FH.S_dn:
                        if FH.stable_spread and self.D > self.D_std:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(self.D-self.D_std, FH.forward_limit-FH.forward_position_size)*100+0.001)/100.0
                            print ('b2',self.D-self.D_std, FH.forward_limit-FH.forward_position_size)
                elif self.current_side == 'forward':
                    #if FH.tick_price >= FH.S_up:
                        if FH.stable_spread and self.D < self.D_std:
                            #if FH.t_f >= 0.0:
                                self.forward_catch = True
                                self.forward_catch_size = int(min(self.D_std-self.D, FH.forward_limit-FH.forward_position_size)*100+0.001)/100.0
                                print ('b3',self.D_std-self.D, FH.forward_limit-FH.forward_position_size)
                    #elif FH.tick_price <= FH.S_dn:
                        if FH.stable_spread and self.D > self.D_std:
                            self.backward_catch = True
                            self.backward_catch_size = int(min(self.D-self.D_std, FH.backward_limit-FH.backward_position_size)*100+0.001)/100.0
                            print ('b4',self.D-self.D_std, FH.backward_limit-FH.backward_position_size)
                elif self.current_side == 'biside':
                    self.T_guide_up += FH.tap/FH.limit_size - self.T_std_up
                    self.T_guide_dn += FH.tap/FH.limit_size - self.T_std_dn
                    self.T_std_up = FH.tap/FH.limit_size
                    self.T_std_dn = FH.tap/FH.limit_size
                    self.D_std = FH.tap
                    if  FH.tick_price <= FH.S_dn:
                        if FH.stable_spread and self.D < self.D_std:
                            #if FH.t_b >= 0.0:
                            self.backward_catch = True
                            self.backward_catch_size = int(min(self.D_std-self.D, FH.backward_limit-FH.backward_position_size)*100+0.001)/100.0
                            print ('b5',self.D_std-self.D, FH.backward_limit-FH.backward_position_size)
                    elif FH.tick_price >= FH.S_up:
                        if FH.stable_spread and self.D < self.D_std:
                            #if FH.t_f >= 0.0:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(self.D_std-self.D, FH.forward_limit-FH.forward_position_size)*100+0.001)/100.0
                            print ('b6',self.D_std-self.D, FH.forward_limit-FH.forward_position_size)

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
            #if FH.goods_rt < -0.8:
            #    if FH.stable_spread:
            #        if FH.forward_position_size < FH.backward_position_size:
            #            FH.T_guide += (1.0 - ((FH.backward_position_size - FH.tap) - FH.forward_position_size) / FH.limit_size) - FH.T_std
            #            FH.T_std = 1.0 - ((FH.backward_position_size - FH.tap) - FH.forward_position_size) / FH.limit_size
            #            self.D_std = (FH.backward_position_size - FH.tap) - FH.forward_position_size
            #            mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
            #                            "type": mt5.ORDER_TYPE_BUY, "position": int(FH.backward_positions.iloc[len(FH.backward_positions)-1]['ticket']),
            #                            "volume": FH.tap, "price": FH.ask_1,
            #                            "deviation": 0, "magic": 1000})
            #        elif FH.backward_position_size < FH.forward_position_size:
            #            FH.T_guide += (1.0 - ((FH.forward_position_size - FH.tap) - FH.backward_position_size) / FH.limit_size) - FH.T_std
            #            FH.T_std = 1.0 - ((FH.forward_position_size - FH.tap) - FH.backward_position_size) / FH.limit_size
            #            self.D_std = (FH.forward_position_size - FH.tap) - FH.backward_position_size
            #            mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
            #                            "type": mt5.ORDER_TYPE_SELL, "position": int(FH.forward_positions.iloc[len(FH.forward_positions)-1]['ticket']),
            #                            "volume": FH.tap, "price": FH.bid_1,
            #                            "deviation": 0, "magic": 1000})
            #else:
                if not self.forward_increase_clear:
                    if FH.forward_position_size < FH.forward_limit:
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
                    if FH.backward_position_size < FH.backward_limit:
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


