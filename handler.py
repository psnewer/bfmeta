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
    balance_overflow = 0.57
    account_from = 0
    order_from = 0
    goods = 0.57
    forward_goods = 0.0
    backward_goods = 0.0
    limit_value = 0.0
    catch = False
    balance = False
    forward_sprint = False
    backward_sprint = False
    forward_band_price = -1.0
    backward_band_price = -1.0
    T_guide = 1.0
    _T = None
    T_std = 1.0
    S_up = 0.0
    S_dn = 0.0
    t_up = 0.0
    t_dn = 0.0
    S_up_t = 0.0
    S_dn_t = 0.0
    t_up_S = 0.0
    t_dn_S = 0.0
    t_head = -1
    t_tail = -1
    pre_side = 'biside'

    def __init__(self,contract = '',contract_params = {}):
        FH.contract = contract
        FH.quanto = contract_params['quanto']
        FH.T_rt =  contract_params['T_rt']
        FH.limit_size = contract_params['limit_size']
        FH.limit_spread = contract_params['limit_spread']
        FH.balance_rt = contract_params['balance_rt']
        FH.surplus_abandon = contract_params['surplus_abandon']
        FH.surplus_endure = contract_params['surplus_endure']
        FH.step_soft_std = contract_params['step_soft']
        FH.step_hard_std = contract_params['step_hard']
        FH.std_mom_std = contract_params['std_mom']
        FH.std_sprint_std = contract_params['std_sprint']

    def get_std_flag(self):
        FH.orders = mt5.orders_get(symbol=FH.contract)
        candles = mt5.copy_rates_from_pos(FH.contract,mt5.TIMEFRAME_M1,0,11)
        candles_5m = mt5.copy_rates_from_pos(FH.contract,mt5.TIMEFRAME_M5,0,11)
        candles_1h = mt5.copy_rates_from_pos(FH.contract,mt5.TIMEFRAME_H1,0,11)
        book = mt5.symbol_info_tick(FH.contract)
        FH.bid_1 = book.bid
        FH.ask_1 = book.ask
        FH.tick_price = (FH.ask_1 + FH.bid_1) / 2
        positions = mt5.positions_get(symbol=FH.contract)
        if len(positions) > 0:
            positions = pd.DataFrame(list(positions),columns = positions[0]._asdict().keys())
            FH.forward_positions = positions[positions['type']==mt5.POSITION_TYPE_BUY].sort_values(by='price_open',ascending=False)
            FH.backward_positions = positions[positions['type']==mt5.POSITION_TYPE_SELL].sort_values(by='price_open',ascending=True)
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

        if FH.t_tail == -1:
            FH.t_tail = sys.float_info.min if FH.t_f > FH.t_b else sys.float_info.max
        if FH.t_head == -1:
            FH.t_head = sys.float_info.max if FH.t_f > FH.t_b else sys.float_info.min

        FH.forward_stable_price = False
        FH.backward_stable_price = False
        if FH.ask_1 - FH.bid_1 < FH.limit_spread:
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
            med_5m = np.median(abs5m)
            max_5m = np.max(abs5m)
            FH.std_mom = max(FH.std_mom_std,med_5m)
            FH.step_soft = max(FH.step_soft_std, max_5m)

        if len(candles_1h) > 10:
            abs1h = []
            for i in range(1,11):
                o = float(candles_1h[len(candles_1h)-i]['open'])
                c = float(candles_1h[len(candles_1h)-i]['close'])
                abs1h.append(abs(c - o))
            abs1h = np.nan_to_num(abs1h)
            max_1h = np.max(abs1h)
            med_1h = np.median(abs1h)
            FH.std_sprint = max(FH.std_sprint_std,med_1h)
            FH.step_hard = max(FH.step_hard_std,max_1h)
            #FH.step_soft = max(FH.step_soft_std, max_1h)

        if FH.t_f > FH.t_b:
            FH.current_side = 'forward'
        elif FH.t_f < FH.t_b:
            FH.current_side = 'backward'
            FH.step_soft = -FH.step_soft
            FH.step_hard = -FH.step_hard
        else:
            FH.current_side = 'biside'

        if FH.current_side != FH.pre_side:
            FH.pre_side = FH.current_side
            FH.pre_t = 't'
            FH.t_tail = -1
            FH.catch = False
            FH.balance = False

        print('step', FH.step_soft, FH.step_hard)
        FH.forward_mom = False
        FH.backward_mom = False
        FH.co = 0.0
        if len(candles_5m) > 1:
            o = float(candles_5m[len(candles_5m)-2]['open'])
            c = float(candles_5m[len(candles_5m)-2]['close'])
            FH.co = (c - o)
            if FH.co >= FH.std_mom:
                FH.forward_mom = True
            elif FH.co <= -FH.std_mom:
                FH.backward_mom = True

        if FH.forward_mom:
            if FH.forward_band_price < 0.0:
                FH.forward_band_price = FH.ask_1
            if FH.backward_band_price > 0 and (FH.backward_band_price - FH.ask_1) >= FH.std_sprint:
                FH.forward_sprint = False
                FH.backward_sprint = True
            FH.backward_band_price = -1.0
        elif FH.backward_mom:
            if FH.backward_band_price < 0.0:
                FH.backward_band_price = FH.bid_1
            if FH.forward_band_price > 0 and (FH.bid_1 - FH.forward_band_price) >= FH.std_sprint:
                FH.backward_sprint = False
                FH.forward_sprint = True
            FH.forward_band_price = -1.0

        print(FH.forward_mom,FH.co,FH.forward_sprint)
        print(FH.backward_mom,FH.co,FH.backward_sprint)
        print(FH.std_mom,FH.std_sprint,FH.forward_band_price,FH.backward_band_price)

        if FH.forward_position_size == 0:
            FH.forward_goods = 0.0
        else:
            FH.forward_goods = FH.forward_profit
        if FH.backward_position_size == 0:
            FH.backward_goods = 0.0
        else:
            FH.backward_goods = FH.backward_profit
        if FH.forward_position_size > 0.001:
            FH.limit_value = FH.forward_positions.iloc[0]['value']*FH.limit_size/FH.forward_positions.iloc[0]['volume']
        elif FH.backward_position_size > 0.001:
            FH.limit_value = FH.backward_positions.iloc[0]['value']*FH.limit_size/FH.backward_positions.iloc[0]['volume']
        else:
            FH.limit_value = 0.0
        FH.abandon_goods = FH.surplus_abandon/FH.tick_price * FH.limit_value
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

        if FH.t_f <= FH.t_b:
            if FH.t_f != 0:
                FH._T = float(FH.backward_position_size) / float(FH.forward_position_size)
            else:
                FH._T = 1.0
        elif FH.t_f >= FH.t_b:
            if FH.t_b != 0:
                FH._T = float(FH.forward_position_size) / float(FH.backward_position_size)
            else:
                FH._T = 1.0

        #if FH.forward_position_size < 0.001 and FH.backward_position_size < 0.001:
        #    FH.balance_overflow = 0.0
        if FH.forward_goods + FH.backward_goods + FH.balance_overflow > 0.0:
            FH.balance_overflow = max(0.0,-(FH.forward_goods + FH.backward_goods))