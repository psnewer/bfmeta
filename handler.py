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
    balance_overflow = 0.0
    account_from = 0
    order_from = 0
    margin = 0.0
    goods_rt = 0.0
    unit_value = 0.0
    pre_side = ''
    current_side = ''

    def __init__(self,contract = '',contract_params = {}):
        FH.contract = contract
        FH.quanto = contract_params['quanto']
        FH.T_level = contract_params['T_level']
        FH.unit = contract_params['unit']
        FH.M5 = contract_params['M5']
        FH.tap = contract_params['tap']
        FH.a_limit = contract_params['a_limit']
        FH.limit_size = contract_params['limit_size']
        FH.limit_spread = contract_params['limit_spread']
        FH.ENABLE_BY = contract_params['ENABLE_BY']
        FH.first_limit = contract_params['first_limit']

    def get_status(self):
        FH.orders = mt5.orders_get(symbol=FH.contract)
        FH.candles = mt5.copy_rates_from_pos(FH.contract,mt5.TIMEFRAME_M1,0,11)
        FH.candles_m5 = mt5.copy_rates_from_pos(FH.contract, eval('mt5.TIMEFRAME_' + FH.M5), 0, 11)
        book = mt5.symbol_info_tick(FH.contract)
        FH.bid_1 = book.bid
        FH.ask_1 = book.ask
        FH.tick_price = (FH.ask_1 + FH.bid_1) / 2
        positions = mt5.positions_get(symbol=FH.contract)
        if len(positions) > 0 and mt5.last_error()[0]:
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

        print('price', FH.ask_1, FH.bid_1, FH.tick_price)

    def get_std_flag(self):

        if FH.forward_position_size == 0:
            FH.forward_entry_price = FH.ask_1
        else:
            FH.forward_entry_price = FH.forward_value / FH.forward_position_size / FH.unit
        if FH.backward_position_size == 0:
            FH.backward_entry_price = FH.bid_1
        else:
            FH.backward_entry_price = FH.backward_value / FH.backward_position_size / FH.unit

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
            if len(FH.candles) > 0:
                o = float(FH.candles[len(FH.candles)-1]['open'])
                c = float(FH.candles[len(FH.candles)-1]['close'])
                if (c - o) < 0.0:
                    FH.forward_stable_price = True
                if (c - o) > -0.0:
                    FH.backward_stable_price = True

        if len(FH.candles_m5) > 10:
            oc = []
            hl = []
            for i in range(1,11):
                o = float(FH.candles_m5[len(FH.candles_m5)-i]['open'])
                c = float(FH.candles_m5[len(FH.candles_m5)-i]['close'])
                h = float(FH.candles_m5[len(FH.candles_m5) - i]['high'])
                l = float(FH.candles_m5[len(FH.candles_m5) - i]['low'])
                oc.append(abs(c - o))
                hl.append(abs(h - l))
            oc = np.nan_to_num(oc)
            hl = np.nan_to_num(hl)
            max_oc = np.max(oc)
            max_hl = np.max(hl)
            FH.m5_oc = max_oc
            FH.m5_hl = max_hl

        print ('step',FH.m5_oc,FH.m5_hl)

        FH.step_hard = FH.m5_hl

        if FH.forward_position_size == 0:
            FH.forward_goods = 0.0
        else:
            FH.forward_goods = FH.forward_profit
        if FH.backward_position_size == 0:
            FH.backward_goods = 0.0
        else:
            FH.backward_goods = FH.backward_profit

        FH.unit_value = FH.tick_price * FH.unit

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
                FH.account_from = item.time_msc * 0.001
                FH.order_from = item.order
                FH.balance_overflow += float(item.profit)

        if FH.forward_position_size < 0.001 and FH.backward_position_size < 0.001:
            FH.balance_overflow = 0.0

        FH.margin = FH.forward_goods + FH.backward_goods + FH.balance_overflow
        FH.goods_rt = FH.margin / FH.unit_value * FH.T_level

    #def get_side(self):

    #    if FH.current_side == 'backward':
    #        FH.step_soft = -FH.step_soft
    #        FH.step_hard = -FH.step_hard

    #    if FH.current_side != FH.pre_side:
    #        FH.pre_side = FH.current_side
    #        self.reset_St()

    #def reset_St(self):
    #    FH.S_up = FH.tick_price + FH.step_hard
    #    FH.S_dn = FH.tick_price - FH.step_hard


