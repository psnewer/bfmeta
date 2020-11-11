# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import numpy as np
from conf import *
from handler import *

class Handler_T(FH):
    def __init__(self):
        self.tip = 't'

    def get_flag(self):

        self.get_std_flag()

        account_book = mt5.history_deals_get(FH.account_from, time.time()+24*3600, group=FH.contract)
        for item in account_book:
            if item.time_msc*0.001 > FH.account_from and item.order != FH.order_from and FH.contract in item.symbol:
                FH.goods += float(item.profit)
                FH.account_from = item.time_msc*0.001
                FH.order_from = item.order
                if float(item.profit) > 0.0:
                    FH.balance_overflow += FH.balance_rt * float(item.profit)
                else:
                    FH.balance_overflow += float(item.profit)

        FH.T_std = FH.T_guide + (FH.forward_goods + FH.backward_goods + FH.balance_overflow) / (FH.limit_value * FH.T_rt) * 400
        if FH.T_std < 0.25 or FH.T_std > 1.25:
            FH.T_guide += 1.0 - FH.T_std
        elif FH._T == 1.0 and len(FH.orders) == 0:
            FH.T_guide += 0.8 - FH.T_std

        if FH.t_f < FH.t_b:
            FH.t_tail = min(FH.t_tail, FH.tick_price - FH.step_hard)
        elif FH.t_f > FH.t_b:
            FH.t_tail = max(FH.t_tail,FH.tick_price - FH.step_hard)

        if FH.forward_position_size == 0 or FH.backward_position_size == 0:
            FH.catch = True
            FH.balance = False
            FH.S_dn = FH.tick_price
            FH.S_dn_t = FH.tick_price - FH.step_soft
            FH.S_up = FH.tick_price + FH.step_soft
            FH.S_up_t = FH.tick_price + 2*FH.step_soft
        else:
            if FH.balance and not FH.catch:
                if (FH.tick_price >= FH.t_up_S and FH.step_soft > 0) or (FH.tick_price <= FH.t_up_S and FH.step_soft < 0):
                    FH.balance = False
                    FH.catch = True
                    FH.S_up = FH.tick_price
                    FH.S_up_t = FH.tick_price + FH.step_soft
                    FH.S_dn = FH.tick_price - FH.step_soft
                    FH.S_dn_t = FH.tick_price - 2*FH.step_soft
                elif (FH.tick_price <= FH.t_dn_S and FH.step_soft > 0) or (FH.tick_price >= FH.t_dn_S and FH.step_soft < 0):
                    FH.balance = False
                    FH.catch = True
                    FH.S_dn = FH.tick_price
                    FH.S_dn_t = FH.tick_price - FH.step_soft
                    FH.S_up = FH.tick_price + FH.step_soft
                    FH.S_up_t = FH.tick_price + 2*FH.step_soft
                print ('balance',FH.tick_price,FH.t_up_S,FH.t_up,FH.t_dn,FH.t_dn_S)
            elif not FH.balance and FH.catch:
                if (FH.tick_price >= FH.S_up_t and FH.step_soft > 0) or (FH.tick_price <= FH.S_up_t and FH.step_soft < 0):
                    FH.catch = False
                    FH.balance = True
                    FH.t_up = FH.tick_price
                    FH.t_dn = FH.tick_price - FH.step_soft
                    FH.t_up_S = FH.tick_price + FH.step_soft
                    FH.t_dn_S = FH.tick_price - 2*FH.step_soft
                elif (FH.tick_price <= FH.S_dn_t and FH.step_soft > 0) or (FH.tick_price >= FH.S_dn_t and FH.step_soft < 0):
                    FH.catch = False
                    FH.balance = True
                    FH.t_dn = FH.tick_price
                    FH.t_up =  FH.tick_price + FH.step_soft
                    FH.t_dn_S = FH.tick_price - FH.step_soft
                    FH.t_up_S = FH.tick_price + 2*FH.step_soft
                print ('catch',FH.tick_price,FH.S_up_t,FH.S_up,FH.S_dn,FH.S_dn_t)
            elif not FH.balance and not FH.catch:
                FH.balance = True
                FH.t_up = FH.tick_price + FH.step_soft
                FH.t_dn = FH.tick_price - FH.step_soft
                FH.t_up_S = FH.tick_price + 2*FH.step_soft
                FH.t_dn_S = FH.tick_price - 2*FH.step_soft

        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if FH.balance:
            if FH.t_f < FH.t_b:
                if FH.forward_stable_price and FH._T < FH.T_std:
                    if FH.tick_price >= FH.t_dn:
                        self.forward_gap_balance = True
                elif FH.backward_stable_price and FH._T > FH.T_std:
                    if FH.tick_price <= FH.t_up:
                        if FH.t_b > 0.0:
                            self.backward_gap_balance = True
            elif FH.t_f > FH.t_b:
                if FH.backward_stable_price and FH._T < FH.T_std:
                    if FH.tick_price <= FH.t_dn:
                        self.backward_gap_balance = True
                elif FH.forward_stable_price and FH._T > FH.T_std:
                    if FH.tick_price >= FH.t_up:
                        if FH.t_f > 0.0:
                            self.forward_gap_balance = True

        if self.forward_gap_balance:
            if FH.t_f >= 0.0:
                self.forward_balance_size = float(format(min(FH.forward_position_size-FH.backward_position_size*FH.T_std,FH.forward_positions.iloc[0]['volume']),'.2f'))
                self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                print('d1', FH.forward_position_size-FH.backward_position_size*FH.T_std,FH.forward_positions.iloc[0]['volume'])
            else:
                self.forward_balance_size = float(format(min(FH.forward_position_size-FH.backward_position_size/FH.T_std,FH.forward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[0]['profit']))),'.2f'))
                self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                print ('d2',FH.forward_position_size-FH.backward_position_size/FH.T_std,FH.forward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[0]['profit'])))
        if self.backward_gap_balance:
            if FH.t_b >= 0.0:
                self.backward_balance_size = float(format(min(FH.backward_position_size-FH.forward_position_size*FH.T_std,FH.backward_positions.iloc[0]['volume']),'.2f'))
                self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                print ('d3',FH.backward_position_size-FH.forward_position_size*FH.T_std,FH.backward_positions.iloc[0]['volume'])
            else:
                self.backward_balance_size = float(format(min(FH.backward_position_size-FH.forward_position_size/FH.T_std,FH.backward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[0]['profit']))),'.2f'))
                self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                print ('d4',FH.backward_position_size-FH.forward_position_size/FH.T_std,FH.backward_positions.iloc[0]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[0]['profit'])))

        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        print (FH._T,FH.T_std,FH.forward_stable_price,FH.backward_stable_price)
        if FH.catch:
            if FH.t_f < FH.t_b:
                if FH._T > FH.T_std:
                    if FH.backward_stable_price and FH.tick_price <= FH.S_up:
                        self.forward_catch = True
                        self.forward_catch_size = float(format(min(FH.backward_position_size/FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size),'.2f'))
                        print ('1111',FH.backward_position_size/FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size)
                elif FH._T < FH.T_std:
                    if FH.forward_stable_price and FH.tick_price >= FH.S_dn:
                        self.backward_catch = True
                        self.backward_catch_size = float(format(min(FH.forward_position_size*FH.T_std-FH.backward_position_size,FH.backward_limit-FH.backward_position_size),'.2f'))
                        print ('bbbb',FH.forward_position_size*FH.T_std-FH.backward_position_size,FH.backward_limit-FH.backward_position_size)
            elif FH.t_f > FH.t_b:
                if FH._T > FH.T_std:
                    if FH.forward_stable_price and FH.tick_price >= FH.S_up:
                        self.backward_catch = True
                        self.backward_catch_size = float(format(min(FH.forward_position_size/FH.T_std-FH.backward_position_size,FH.backward_limit-FH.backward_position_size),'.2f'))
                        print ('2222',FH.forward_position_size/FH.T_std-FH.backward_position_size,FH.backward_limit-FH.backward_position_size)
                elif FH._T < FH.T_std:
                    if FH.backward_stable_price and FH.tick_price <= FH.S_dn:
                        self.forward_catch = True
                        self.forward_catch_size = float(format(min(FH.backward_position_size*FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size),'.2f'))
                        print ('cccc',FH.backward_position_size*FH.T_std-FH.forward_position_size,FH.forward_limit-FH.forward_position_size)

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
            if order_type is mt5.ORDER_TYPE_BUY and order_magic == 0:
                if (not self.forward_catch) or FH.forward_position_size >= FH.forward_limit:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                elif self.forward_catch and self.forward_catch_size > 0:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                elif FH.ask_1 > order_price:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
            elif order_type is mt5.ORDER_TYPE_SELL and order_magic == 1000:
                if self.forward_gap_balance:
                    if order_price > FH.bid_1 or self.forward_balance_size > 0:
                        mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                else:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})

            if order_type is mt5.ORDER_TYPE_SELL and order_magic == 0:
                if (not self.backward_catch) or FH.backward_position_size >= FH.backward_limit:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                elif self.backward_catch and self.backward_catch_size > 0:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                elif FH.bid < order_price:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
            elif order_type is mt5.ORDER_TYPE_SELL and order_magic == 1000:
                if self.backward_gap_balance:
                    if order_price < FH.ask_1 or self.backward_balance_size > 0:
                        mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})
                else:
                    mt5.order_send(request={"action": mt5.TRADE_ACTION_REMOVE, "order": order_id})

        if not self.forward_increase_clear:
            if FH.forward_position_size < FH.forward_limit:
                if self.forward_catch and self.forward_catch_size > 0:
                    mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
                                    "type": mt5.ORDER_TYPE_BUY, "volume": self.forward_catch_size,
                                    "price": FH.ask_1, "deviation": 0, "magic": 0})
        if not self.forward_reduce_clear and self.forward_gap_balance:
            if FH.forward_position_size > 0:
                if self.forward_balance_size > 0:
                    mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
                                    "type": mt5.ORDER_TYPE_SELL, "position": self.forward_balance_ticket,
                                    "volume": self.forward_balance_size, "price": FH.bid_1,
                                    "deviation": 0, "magic": 1000})

        if not self.backward_increase_clear:
            if FH.backward_position_size < FH.backward_limit:
                if self.backward_catch and self.backward_catch_size > 0:
                    mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
                                    "type": mt5.ORDER_TYPE_SELL, "volume": self.backward_catch_size,
                                    "price": FH.bid_1, "deviation": 0, "magic": 0})
        if not self.backward_reduce_clear and self.backward_gap_balance:
            if FH.backward_position_size > 0:
                if self.backward_balance_size > 0:
                    mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
                                    "type": mt5.ORDER_TYPE_BUY, "position": self.backward_balance_ticket,
                                    "volume": self.backward_balance_size, "price": FH.ask_1,
                                    "deviation": 0, "magic": 1000})
