# -*- coding: utf-8 -*-

from __future__ import print_function
import requests
import time
import math
import numpy as np
from conf import *
from handler import *


class Handler_F(FH):
    def __init__(self):
        self.tip = 'f'
        self.forward_target_size = 0
        self.backward_target_size = 0

    def get_flag(self):

        self.get_std_flag()

        if FH.forward_position_size == 0 and FH.backward_position_size == 0:
            self.forward_target_size = FH.limit_size
            self.backward_target_size = FH.limit_size

        self.forward_catch = False
        self.backward_catch = False

        if FH.forward_position_size >= self.forward_target_size:
            self.forward_target_size = 0
        else:
            if FH.stable_spread:
                self.forward_catch = True
                self.forward_catch_size = float(format(self.forward_target_size - FH.forward_position_size,FH.quanto))
        if FH.backward_position_size >= self.backward_target_size:
            self.backward_target_size = 0
        else:
            if FH.stable_spread:
                self.backward_catch = True
                self.backward_catch_size = float(format(self.backward_target_size - FH.backward_position_size,FH.quanto))

        self.forward_gap_balance = False
        self.backward_gap_balance = False

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

