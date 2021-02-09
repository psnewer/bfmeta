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

        FH.T_N = FH.limit_size / 0.01
        FH.T_d = 2.0 * FH.D_rt / FH.T_N / (FH.T_N - 1)
        FH.L_d = 2.0 * FH.L_rt / FH.T_N / (FH.T_N - 1)
        FH.T_para = 1.0 / FH.T_N / FH.T_d
        FH.L_para = FH.T_para * FH.TL_rt
        FH.T_floor = FH.D / 0.01 if FH._T < 1.0 else FH.tap / 0.01
        FH.L = (FH.D/0.01) * (FH.D/0.01 - 1) / 2 * FH.L_d
        FH.LT = (FH.D/0.01) * (FH.D/0.01 - 1) / 2 * FH.T_d
        FH.T = (FH.forward_goods+FH.backward_goods+FH.balance_overflow)/FH.limit_value*400
        if FH.T < -FH.L and FH.T_D:
            FH.T_limit = 1.0 - FH.D / FH.limit_size
            FH.T_D = False
        elif FH.T >= -FH.L and not FH.T_D:
            FH.T_limit = 0.0
            FH.T_D = True
        if FH.T_D:
            FH.T_rt = FH.T_para / FH.T_floor
        else:
            FH.T_rt = FH.L_para / FH.T_floor
        if abs(FH.T_rt - FH.T_rt_pre) > 0.0001:
            FH.T_rt_pre = FH.T_rt
            print('qqqq', FH.T_rt)
            if FH.limit_value > 0.0:
                FH.T_guide += FH.T_std - (FH.T_guide + (FH.forward_goods + FH.backward_goods + FH.balance_overflow) / FH.limit_value * 400 * FH.T_rt)

        if FH.limit_value > 0.0:
            FH.T_std = FH.T_guide + (FH.forward_goods + FH.backward_goods + FH.balance_overflow) / FH.limit_value * 400 * FH.T_rt
        if FH.T_std < FH.T_limit and len(FH.orders) == 0:
            FH.T_guide += FH.T_limit - FH.T_std
            FH.T_std = FH.T_limit
        elif FH.T_std > 1.0 and len(FH.orders) == 0:
            FH.T_guide += 1.0 - FH.T_std
            FH.T_std = 1.0
        FH.D_std = FH.limit_size * (1.0 - FH.T_std)

        print(FH.T, -FH.L, FH.T_D, FH.T_limit)

        #if FH.forward_position_size == 0 or FH.backward_position_size == 0:
        #    FH.catch = True
        #    FH.balance = False
        #    FH.S_dn = FH.tick_price
        #    FH.S_dn_t = FH.tick_price - FH.step_soft
        #    FH.S_up = FH.tick_price + FH.step_soft
        #    FH.S_up_t = FH.tick_price + 2*FH.step_soft
        #else:
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
            #elif FH.forward_position_size <= 0.1 and FH.backward_position_size <= 0.1:
            #    FH.balance = False
            #    FH.catch = True
            #    FH.S_up = FH.tick_price
            #    FH.S_dn = FH.tick_price - FH.step_soft
            #    FH.S_up_t = FH.tick_price + FH.step_soft
            #    FH.S_dn_t = FH.tick_price - 2 * FH.step_soft
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
            #elif FH.forward_position_size >= FH.forward_limit and FH.backward_position_size >= FH.backward_limit:
            #    FH.catch = False
            #    FH.balance = True
            #    FH.t_up = FH.tick_price
            #    FH.t_dn = FH.tick_price - FH.step_soft
            #    FH.t_up_S = FH.tick_price + FH.step_soft
            #    FH.t_dn_S = FH.tick_price - 2 * FH.step_soft
            print ('catch',FH.tick_price,FH.S_up_t,FH.S_up,FH.S_dn,FH.S_dn_t)
        elif not FH.balance and not FH.catch:
            FH.balance = True
            FH.t_up = FH.tick_price + FH.step_soft
            FH.t_dn = FH.tick_price - FH.step_soft
            FH.t_up_S = FH.tick_price + 2 * FH.step_soft
            FH.t_dn_S = FH.tick_price - 2 * FH.step_soft

            #if FH.step_soft > 0:
            #    FH.t_up = min(FH.t_up, FH.tick_price + FH.step_soft)
            #    FH.t_dn = max(FH.t_dn, FH.tick_price - FH.step_soft)
            #    FH.t_up_S = min(FH.t_up_S, FH.tick_price + 2 * FH.step_soft)
            #    FH.t_dn_S = max(FH.t_dn_S, FH.tick_price - 2 * FH.step_soft)
            #elif FH.step_soft < 0:
            #    FH.t_up = max(FH.t_up, FH.tick_price + FH.step_soft)
            #    FH.t_dn = min(FH.t_dn, FH.tick_price - FH.step_soft)
            #    FH.t_up_S = max(FH.t_up_S, FH.tick_price + 2 * FH.step_soft)
            #    FH.t_dn_S = min(FH.t_dn_S, FH.tick_price - 2 * FH.step_soft)

        self.forward_gap_balance = False
        self.forward_balance_size = 0
        self.backward_gap_balance = False
        self.backward_balance_size = 0
        if FH.balance:
            if len(FH.orders) == 0:
                if FH.t_f < FH.t_b:
                    if FH.stable_spread and FH.D > FH.D_std:
                        self.forward_gap_balance = True
                    elif FH.D <= FH.D_std:
                        if FH._T > 0.999:
                            FH.T_guide += (1.0 - (FH.backward_position_size - (FH.forward_position_size - FH.tap))/FH.limit_size) - FH.T_std
                            FH.T_std = 1.0 - (FH.backward_position_size - (FH.forward_position_size - FH.tap))/FH.limit_size
                            FH.D_std = FH.backward_position_size - (FH.forward_position_size - FH.tap)
                        if FH.stable_spread:
                            #if FH.tick_price <= FH.t_up:
                                if FH.t_b >= 0.0:
                                    self.backward_gap_balance = True
                elif FH.t_f > FH.t_b:
                    if FH.stable_spread and FH.D > FH.D_std:
                        self.backward_gap_balance = True
                    elif FH.D <= FH.D_std:
                        if FH._T > 0.999:
                            FH.T_guide += (1.0 - (FH.forward_position_size - (FH.backward_position_size - FH.tap)) / FH.limit_size) - FH.T_std
                            FH.T_std = 1.0 - (FH.forward_position_size - (FH.backward_position_size - FH.tap)) / FH.limit_size
                            FH.D_std = FH.forward_position_size - (FH.backward_position_size - FH.tap)
                        if FH.stable_spread:
                            #if FH.tick_price >= FH.t_up:
                                if FH.t_f >= 0.0:
                                    self.forward_gap_balance = True

        if self.forward_gap_balance:
            if FH.t_f > FH.t_b:
                self.forward_balance_size = int(min(FH.D_std-FH.D, FH.forward_positions.iloc[0]['volume'], FH.forward_position_size-FH.tap)*100+0.001)/100.0
                self.forward_balance_ticket = int(FH.forward_positions.iloc[0]['ticket'])
                print('d1', FH.D_std-FH.D, FH.forward_positions.iloc[0]['volume'])
                #if FH._T > 0.999:
                #    self.forward_balance_size = min(max(FH.tap,self.forward_balance_size),FH.forward_positions.iloc[0]['volume'])
            else:
                if FH.forward_positions.iloc[len(FH.forward_positions)-1]['profit'] < 0:
                    self.forward_balance_size = int(min(FH.D-FH.D_std, FH.forward_positions.iloc[len(FH.forward_positions)-1]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[len(FH.forward_positions)-1]['profit'])))*100+0.001)/100.0
                    self.forward_balance_ticket = int(FH.forward_positions.iloc[len(FH.forward_positions)-1]['ticket'])
                    print ('d2', FH.D-FH.D_std, FH.forward_positions.iloc[len(FH.forward_positions)-1]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.forward_positions.iloc[len(FH.forward_positions)-1]['profit'])))
                else:
                    self.forward_balance_size = int(min(FH.D-FH.D_std, FH.forward_positions.iloc[len(FH.forward_positions)-1]['volume']) * 100 + 0.001) / 100.0
                    self.forward_balance_ticket = int(FH.forward_positions.iloc[len(FH.forward_positions)-1]['ticket'])
        if self.backward_gap_balance:
            if FH.t_b > FH.t_f:
                self.backward_balance_size = int(min(FH.D_std-FH.D, FH.backward_positions.iloc[0]['volume'], FH.backward_position_size-FH.tap)*100+0.001)/100.0
                self.backward_balance_ticket = int(FH.backward_positions.iloc[0]['ticket'])
                print ('d3', FH.D_std-FH.D, FH.backward_positions.iloc[0]['volume'])
                #if FH._T > 0.999:
                #    self.backward_balance_size = min(max(FH.tap,self.backward_balance_size),FH.backward_positions.iloc[0]['volume'])
            else:
                if FH.backward_positions.iloc[len(FH.backward_positions)-1]['profit'] < 0:
                    self.backward_balance_size = int(min(FH.D-FH.D_std, FH.backward_positions.iloc[len(FH.backward_positions)-1]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[len(FH.backward_positions)-1]['profit'])))*100+0.001)/100.0
                    self.backward_balance_ticket = int(FH.backward_positions.iloc[len(FH.backward_positions)-1]['ticket'])
                    print ('d4', FH.D-FH.D_std, FH.backward_positions.iloc[len(FH.backward_positions)-1]['volume']*min(1.0,max(0.0,FH.balance_overflow)/abs(FH.backward_positions.iloc[len(FH.backward_positions)-1]['profit'])))
                else:
                    self.backward_balance_size = int(min(FH.D-FH.D_std, FH.backward_positions.iloc[len(FH.backward_positions)-1]['volume']) * 100 + 0.001) / 100.0
                    self.backward_balance_ticket = int(FH.backward_positions.iloc[len(FH.backward_positions)-1]['ticket'])

        self.forward_catch = False
        self.forward_catch_size = 0
        self.backward_catch = False
        self.backward_catch_size = 0
        print (FH._T,FH.T_std,FH.D,FH.D_std,FH.forward_stable_price,FH.backward_stable_price)
        if FH.catch:
            if len(FH.orders) == 0:
                if FH.t_f < FH.t_b:
                    if FH.D <= FH.D_std:
                        if FH._T > 0.999:
                            FH.T_guide += (1.0 - ((FH.backward_position_size + FH.tap) - FH.forward_position_size)/FH.limit_size) - FH.T_std
                            FH.T_std = 1.0 - ((FH.backward_position_size + FH.tap) - FH.forward_position_size)/FH.limit_size
                            FH.D_std = (FH.backward_position_size + FH.tap) - FH.forward_position_size
                        if FH.stable_spread and FH.tick_price <= FH.S_up:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(FH.D_std-FH.D, FH.forward_limit-FH.forward_position_size)*100+0.001)/100.0
                            print ('1111',FH.D_std-FH.D, FH.forward_limit-FH.forward_position_size)
                            #if FH._T > 0.999:
                            #    self.forward_catch_size = min(max(FH.tap, self.forward_catch_size),FH.forward_limit-FH.forward_position_size)
                    elif FH.D > FH.D_std:
                        if FH.stable_spread and FH.tick_price >= FH.S_dn:
                            self.backward_catch = True
                            self.backward_catch_size = int(min(FH.D-FH.D_std, FH.backward_limit-FH.backward_position_size)*100+0.001)/100.0
                            print ('bbbb',FH.D-FH.D_std, FH.backward_limit-FH.backward_position_size)
                elif FH.t_f > FH.t_b:
                    if FH.D <= FH.D_std:
                        if FH._T > 0.999:
                            FH.T_guide += (1.0 - ((FH.forward_position_size + FH.tap) - FH.backward_position_size) / FH.limit_size) - FH.T_std
                            FH.T_std = 1.0 - ((FH.forward_position_size + FH.tap) - FH.backward_position_size) / FH.limit_size
                            FH.D_std = (FH.forward_position_size + FH.tap) - FH.backward_position_size
                        if FH.stable_spread and FH.tick_price >= FH.S_up:
                            self.backward_catch = True
                            self.backward_catch_size = int(min(FH.D_std-FH.D, FH.backward_limit-FH.backward_position_size)*100+0.001)/100.0
                            print ('2222',FH.D_std-FH.D, FH.backward_limit-FH.backward_position_size)
                            #if FH._T > 0.999:
                            #    self.backward_catch_size = min(max(FH.tap, self.backward_catch_size),FH.backward_limit-FH.backward_position_size)
                    elif FH.D > FH.D_std:
                        if FH.stable_spread and FH.tick_price <= FH.S_dn:
                            self.forward_catch = True
                            self.forward_catch_size = int(min(FH.D-FH.D_std, FH.forward_limit-FH.forward_position_size)*100+0.001)/100.0
                            print ('cccc',FH.D-FH.D_std, FH.forward_limit-FH.forward_position_size)

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

        if len(FH.orders) == 0:
            #if FH.goods_rt < -0.8:
            #    if FH.stable_spread:
            #        if FH.forward_position_size < FH.backward_position_size:
            #            FH.T_guide += (1.0 - ((FH.backward_position_size - FH.tap) - FH.forward_position_size) / FH.limit_size) - FH.T_std
            #            FH.T_std = 1.0 - ((FH.backward_position_size - FH.tap) - FH.forward_position_size) / FH.limit_size
            #            FH.D_std = (FH.backward_position_size - FH.tap) - FH.forward_position_size
            #            mt5.order_send({"action": mt5.TRADE_ACTION_DEAL, "symbol": FH.contract,
            #                            "type": mt5.ORDER_TYPE_BUY, "position": int(FH.backward_positions.iloc[len(FH.backward_positions)-1]['ticket']),
            #                            "volume": FH.tap, "price": FH.ask_1,
            #                            "deviation": 0, "magic": 1000})
            #        elif FH.backward_position_size < FH.forward_position_size:
            #            FH.T_guide += (1.0 - ((FH.forward_position_size - FH.tap) - FH.backward_position_size) / FH.limit_size) - FH.T_std
            #            FH.T_std = 1.0 - ((FH.forward_position_size - FH.tap) - FH.backward_position_size) / FH.limit_size
            #            FH.D_std = (FH.forward_position_size - FH.tap) - FH.backward_position_size
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


