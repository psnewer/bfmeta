//+------------------------------------------------------------------+
//|                                                    Handler_W.mqh |
//|                                                        haidi1231 |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "haidi1231"
#property link      "https://www.mql5.com"
#property version   "1.00"

#include <Handler.mqh>

class Handler_W : public Handler
  {
public:
    Handler_W();
    bool get_flag();
    void put_position();
  };
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
Handler_W::Handler_W()
  {
     this.tip = "w";
  }
//+------------------------------------------------------------------+
bool Handler_W::get_flag(void)
  {
    if (forward_position_size == 0 && backward_position_size == 0)
        if (margin < 0.0)
            return false;

    this.get_std_flag();

    bool forward_reap = false;
    bool backward_reap = false;

    if (forward_position_size > 0.0)
        forward_reap = true;
    if (backward_position_size > 0.0)
        backward_reap = true;

    this.forward_gap_balance = false;
    this.backward_gap_balance = false;
    if (forward_reap)
        if (stable_spread){
            this.forward_gap_balance = true;
            this.forward_balance_ticket = forward_first_position;
            this.forward_balance_size =  forward_first_volume;
        }
   if (backward_reap)
       if (stable_spread){
           this.backward_gap_balance = true;
           this.backward_balance_ticket = backward_first_position;
           this.backward_balance_size =  backward_first_volume;
       }
       
   this.forward_catch = false;
   this.backward_catch = false;

   return true;
}                                                              
//+------------------------------------------------------------------+
void Handler_W::put_position(void)
{
  int orders = OrdersTotal();
  for (int i = orders - 1; i >= 0; i--){
      ulong  order_id = OrderGetTicket(i);
      double order_price = OrderGetDouble(ORDER_PRICE_OPEN);
      ENUM_ORDER_TYPE order_type = OrderGetInteger(ORDER_TYPE);
      ulong order_magic = OrderGetInteger(ORDER_MAGIC);
    
      if (order_type == ORDER_TYPE_BUY && order_magic == 0){
          if (this.forward_catch){
              if (ask_1 > order_price){
                  MqlTradeRequest request={};
                  MqlTradeResult result={};
                  request.action = TRADE_ACTION_REMOVE;
                  request.order = order_id;
                  OrderSend(request,result);
              }
          }
          else{
                MqlTradeRequest request={};
                MqlTradeResult result={};
                request.action = TRADE_ACTION_REMOVE;
                request.order = order_id;
                OrderSend(request,result);
          }
      }
      else if (order_type == ORDER_TYPE_SELL && order_magic == 1000){
          if (this.forward_gap_balance){
              if (order_price > bid_1){
                  MqlTradeRequest request={};
                  MqlTradeResult result={};
                  request.action = TRADE_ACTION_REMOVE;
                  request.order = order_id;
                  OrderSend(request,result);
               }
           }             
           else{
                 MqlTradeRequest request={};
                 MqlTradeResult result={};
                 request.action = TRADE_ACTION_REMOVE;
                 request.order = order_id;
                 OrderSend(request,result);
           }
      }

      if (order_type == ORDER_TYPE_SELL && order_magic == 0){
          if (this.backward_catch){
              if (bid_1 < order_price){
                  MqlTradeRequest request={};
                  MqlTradeResult result={};
                  request.action = TRADE_ACTION_REMOVE;
                  request.order = order_id;
                  OrderSend(request,result);
              }
          }
          else{
                MqlTradeRequest request={};
                MqlTradeResult result={};
                request.action = TRADE_ACTION_REMOVE;
                request.order = order_id;
                OrderSend(request,result);
          }
      }
      else if (order_type == ORDER_TYPE_SELL && order_magic && 1000){
          if (this.backward_gap_balance){
              if (order_price < ask_1){
                  MqlTradeRequest request={};
                  MqlTradeResult result={};
                  request.action = TRADE_ACTION_REMOVE;
                  request.order = order_id;
                  OrderSend(request,result);
              }
          }
          else{
                MqlTradeRequest request={};
                MqlTradeResult result={};
                request.action = TRADE_ACTION_REMOVE;
                request.order = order_id;
                OrderSend(request,result);
          }
      }
  }
  if (orders == 0){
      if (forward_position_size < limit_size){
          if (this.forward_catch && this.forward_catch_size > 0){
              MqlTradeRequest request={};
              MqlTradeResult result={};
              request.action = TRADE_ACTION_DEAL;
              request.symbol = _Symbol;
              request.type = ORDER_TYPE_BUY;
              request.volume = this.forward_catch_size;
              request.price = ask_1;
              request.deviation = 0;
              request.magic = 0;
              OrderSend(request,result);
          }
       }
       if (this.forward_gap_balance && !this.backward_gap_balance){
           if (forward_position_size > 0){
                if (this.forward_balance_size > 0){
                    MqlTradeRequest request={};
                    MqlTradeResult result={};
                    request.action = TRADE_ACTION_DEAL;
                    request.symbol = _Symbol;
                    request.type = ORDER_TYPE_SELL;
                    request.position = this.forward_balance_ticket;
                    request.volume = this.forward_balance_size;
                    request.price = bid_1;
                    request.deviation = 0;
                    request.magic = 1000;            
                    OrderSend(request,result);
                }
           }
        }
        if (backward_position_size < limit_size){
            if (this.backward_catch && this.backward_catch_size > 0){
                    MqlTradeRequest request={};
                    MqlTradeResult result={};
                    request.action = TRADE_ACTION_DEAL;
                    request.symbol = _Symbol;
                    request.type = ORDER_TYPE_SELL;
                    request.volume = this.backward_catch_size;
                    request.price = bid_1;
                    request.deviation = 0;
                    request.magic = 0;
                    OrderSend(request,result);
            }
        }
        if (this.backward_gap_balance && !this.forward_gap_balance){
            if (backward_position_size > 0){
                if (this.backward_balance_size > 0){
                    MqlTradeRequest request={};
                    MqlTradeResult result={};
                    request.action = TRADE_ACTION_DEAL;
                    request.symbol = _Symbol;
                    request.type = ORDER_TYPE_BUY;
                    request.position = this.backward_balance_ticket;
                    request.volume = this.backward_balance_size;
                    request.price = ask_1;
                    request.deviation = 0;
                    request.magic = 1000;
                    OrderSend(request,result);
                }
            }
         }

         if (this.forward_gap_balance && this.backward_gap_balance){
             if (forward_position_size > 0 && backward_position_size > 0){
                 if (this.forward_balance_size > 0 && this.backward_balance_size > 0){
                     MqlTradeRequest request={};
                     MqlTradeResult result={};
                     request.action = TRADE_ACTION_CLOSE_BY;
                     request.position = this.backward_balance_ticket;
                     request.position_by = this.forward_balance_ticket;
                     request.magic = 1001;
                     OrderSend(request,result);
                 }
             }
         }
   }
}
//+------------------------------------------------------------------+
