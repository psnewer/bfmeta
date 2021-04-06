# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import requests
import time
import math
import pandas as pd
import numpy as np
from conf import *

class FH(object):
    balance_overflow = 2.42
    account_from = 0
    order_from = 0
    goods = 2.42
    goods_rt = 0.0
    forward_goods = 0.0
    backward_goods = 0.0
    limit_value = 0.0
    pre_side = ''
    current_side = ''
    catch = False
    balance = False
    S_up = 0.0
    S_dn = 0.0
    t_up = 0.0
    t_dn = 0.0
    S_up_t = 0.0
    S_dn_t = 0.0
    t_up_S = 0.0
    t_dn_S = 0.0

    def __init__(self,contract = '',contract_params = {}):
        FH.contract = contract
        FH.quanto = contract_params['quanto']
        FH.D_01 = contract_params['D_01']
        FH.limit_size = contract_params['limit_size']
        FH.limit_spread = contract_params['limit_spread']
        FH.surplus_endure = contract_params['surplus_endure']

    def get_std_flag(self):
        FH.orders = mt5.orders_get(symbol=FH.contract)
        candles = mt5.copy_rates_from_pos(FH.contract,mt5.TIMEFRAME_M1,0,11)
        candles_5m = mt5.copy_rates_from_pos(FH.contract,mt5.TIMEFRAME_M5,0,11)
        candles_1h = mt5.copy_rates_from_pos(FH.contract,mt5.TIMEFRAME_H1,0,11)
        book = mt5.symbol_info_tick(FH.contract)
        FH.bid_1 = book.bid
        FH.ask_1 = book.ask
        FH.last = book.last
        FH.tick_price = (FH.ask_1 + FH.bid_1) / 2
        positions = mt5.positions_get(symbol=FH.contract)
        if len(positions) > 0:
            positions = pd.DataFrame(list(positions),columns = positions[0]._asdict().keys())
            FH.forward_positions = positions[positions['type']==mt5.POSITION_TYPE_BUY].sort_values(by='price_open',ascending=True)
            FH.backward_positions = positions[positions['type']==mt5.POSITION_TYPE_SELL].sort_values(by='price_open',ascending=False)
            FH.forward_position_size = float(format(FH.forward_positions['volume'].sum(),FH.quanto))
            FH.forward_profit = FH.forward_positions['profit'].sum()
            FH.backward_position_size = float(format(FH.backward_positions['volume'].sum(),FH.quanto))
            FH.backward_profit = FH.backward_positions['profit'].sum()
            FH.forward_positions['value'] = FH.forward_positions['profit']*FH.forward_positions['price_open']/(FH.bid_1-FH.forward_positions['price_open'])
            FH.backward_positions['value'] = FH.backward_positions['profit']*FH.backward_positions['price_open']/(FH.backward_positions['price_open']-FH.ask_1)
            FH.forward_value = FH.forward_positions['value'].sum()
            FH.backward_value = FH.backward_positions['value'].sum()
        else:
            FH.forward_position_size = 0
            FH.backward_position_size = 0

        print ('price',FH.ask_1,FH.bid_1,FH.tick_price,FH.last)

        FH.forward_limit = FH.limit_size
        FH.backward_limit = FH.limit_size

        if FH.forward_position_size == 0:
            FH.forward_entry_price = FH.ask_1
        else:
            FH.forward_entry_price = FH.forward_value / FH.forward_position_size / 100000
        if FH.backward_position_size == 0:
            FH.backward_entry_price = FH.bid_1
        else:
            FH.backward_entry_price = FH.backward_value / FH.backward_position_size / 100000

        if FH.forward_position_size > 0:
            FH.t_f = FH.forward_profit
        else:
            FH.t_f = 0.0
        if FH.backward_position_size > 0:
            FH.t_b = FH.backward_profit
        else:
            FH.t_b = 0.0

        FH.forward_stable_price = False
        FH.backward_stable_price = False
        FH.stable_spread = False
        if FH.ask_1 - FH.bid_1 < FH.limit_spread:
            FH.stable_spread = True
            if len(candles) > 0:
                o = float(candles[len(candles)-1]['open'])
                c = float(candles[len(candles)-1]['close'])
                if (c - o) < 0.0:
                    FH.forward_stable_price = True
                if (c - o) > -0.0:
                    FH.backward_stable_price = True

        if len(candles_5m) > 10:
            abs5m = []
            for i in range(2,12):
                o = float(candles_5m[len(candles_5m)-i]['open'])
                c = float(candles_5m[len(candles_5m)-i]['close'])
                abs5m.append(abs(c - o))
            abs5m = np.nan_to_num(abs5m)
            max_5m = np.max(abs5m)
            FH.step_hard = max_5m
            FH.step_soft = max_5m

#        if len(candles_1h) > 10:
#            abs1h = []
#            for i in range(1,11):
#                o = float(candles_1h[len(candles_1h)-i]['open'])
#                c = float(candles_1h[len(candles_1h)-i]['close'])
#                abs1h.append(abs(c - o))
#            abs1h = np.nan_to_num(abs1h)
#            max_1h = np.max(abs1h)
#            FH.step_hard = max_1h



        if FH.forward_position_size == 0:
            FH.forward_goods = 0.0
        else:
            FH.forward_goods = FH.forward_profit
        if FH.backward_position_size == 0:
            FH.backward_goods = 0.0
        else:
            FH.backward_goods = FH.backward_profit

        FH.limit_value = FH.tick_price * FH.limit_size * 100000

        if not math.isinf(FH.limit_value) and not math.isnan(FH.limit_value):
            FH.endure_goods = FH.surplus_endure/FH.tick_price * FH.limit_value

        if FH.account_from == 0:
            position_deals = mt5.history_deals_get(time.time()-24*3600, time.time()+24*3600, group=FH.contract)
            if len(position_deals) > 0:
                df = pd.DataFrame(list(position_deals), columns=position_deals[0]._asdict().keys()).sort_values(
                    by='time_msc')
                FH.account_from = df.iloc[-1]['time_msc'] * 0.001
                FH.order_from =  df.iloc[-1]['order']
            else:
                FH.account_from = time.time()
                FH.order_from = 0

        account_book = mt5.history_deals_get(FH.account_from, time.time() + 24 * 3600, group=FH.contract)
        for item in account_book:
            if item.time_msc * 0.001 > FH.account_from and item.order != FH.order_from and FH.contract in item.symbol:
                FH.goods += float(item.profit)
                FH.account_from = item.time_msc * 0.001
                FH.order_from = item.order
                FH.balance_overflow += float(item.profit)

        if FH.forward_position_size < 0.001 and FH.backward_position_size < 0.001:
            FH.balance_overflow = 0.0

        FH.margin = FH.forward_goods + FH.backward_goods + FH.balance_overflow
        FH.goods_rt = FH.margin / FH.limit_value * 400

    def get_side(self):

        if FH.current_side == 'backward':
            FH.step_soft = -FH.step_soft
            FH.step_hard = -FH.step_hard

        if FH.current_side != FH.pre_side:
            FH.pre_side = FH.current_side
            FH.catch = False
            FH.balance = False

        if FH.balance and not FH.catch:
            if (FH.tick_price >= FH.t_up_S and FH.step_soft > 0) or (FH.tick_price <= FH.t_up_S and FH.step_soft < 0):
                FH.balance = False
                FH.catch = True
                FH.S_up = FH.tick_price
                FH.S_up_t = FH.tick_price + FH.step_hard
                FH.S_dn = FH.tick_price - FH.step_soft
                FH.S_dn_t = FH.tick_price - 2*FH.step_soft
            elif (FH.tick_price <= FH.t_dn_S and FH.step_soft > 0) or (FH.tick_price >= FH.t_dn_S and FH.step_soft < 0):
                FH.balance = False
                FH.catch = True
                FH.S_dn = FH.tick_price
                FH.S_dn_t = FH.tick_price - FH.step_soft
                FH.S_up = FH.tick_price + FH.step_hard
                FH.S_up_t = FH.tick_price + 2*FH.step_hard
            print ('balance',FH.tick_price,FH.t_up_S,FH.t_up,FH.t_dn,FH.t_dn_S)
        elif not FH.balance and FH.catch:
            if (FH.tick_price >= FH.S_up_t and FH.step_soft > 0) or (FH.tick_price <= FH.S_up_t and FH.step_soft < 0):
                FH.catch = False
                FH.balance = True
                FH.t_up = FH.tick_price
                FH.t_dn = FH.tick_price - FH.step_soft
                FH.t_up_S = FH.tick_price + FH.step_hard
                FH.t_dn_S = FH.tick_price - 2*FH.step_soft
            elif (FH.tick_price <= FH.S_dn_t and FH.step_soft > 0) or (FH.tick_price >= FH.S_dn_t and FH.step_soft < 0):
                FH.catch = False
                FH.balance = True
                FH.t_dn = FH.tick_price
                FH.t_up =  FH.tick_price + FH.step_hard
                FH.t_dn_S = FH.tick_price - FH.step_soft
                FH.t_up_S = FH.tick_price + 2*FH.step_hard
            print ('catch',FH.tick_price,FH.S_up_t,FH.S_up,FH.S_dn,FH.S_dn_t)
        elif not FH.balance and not FH.catch:
            FH.catch = True
            FH.S_up = FH.tick_price + FH.step_hard
            FH.S_dn = FH.tick_price - FH.step_hard
            FH.S_up_t = FH.tick_price + 2 * FH.step_hard
            FH.S_dn_t = FH.tick_price - 2 * FH.step_hard

