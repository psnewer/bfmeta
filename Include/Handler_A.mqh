//+------------------------------------------------------------------+
//|                                                    Handler_A.mqh |
//|                                                        haidi1231 |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "haidi1231"
#property link      "https://www.mql5.com"
#property version   "1.00"

#include <Handler.mqh>
#include <conf.mqh>

class Handler_A : public Handler
  {
public:
        double tap;
        double forward_limit;
        double backward_limit;
        double D;
        double D_std;
        
        Handler_A();
        bool get_flag();
        void put_position();
  };
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
Handler_A::Handler_A()
  {
    this.tip = "a";
    this.tap = 0.01;
    this.current_side = "";
  }
//+------------------------------------------------------------------+
bool Handler_A::get_flag()
  {
    if (forward_position_size == 0 && backward_position_size == 0)
        if (margin < 0.0)
            return false;

    this.get_std_flag();

    this.forward_limit = limit_size;
    this.backward_limit = limit_size;

    if (this.current_side == "forward"){
        this.D = forward_position_size - backward_position_size;
        this.D_std = MathMin(backward_position_size,a_limit);
    }
    else if (this.current_side == "backward"){
        this.D = backward_position_size - forward_position_size;
        this.D_std = MathMin(forward_position_size,a_limit);
    }

    Print (this.current_side);
    Print(this.D, " ", this.D_std, " ", forward_stable_price, " ", backward_stable_price);

    this.forward_gap_balance = false;
    this.forward_balance_size = 0.0;
    this.backward_gap_balance = false;
    this.backward_balance_size = 0.0;
    if (true){
        if (this.current_side == "backward"){
            if (backward_stable_price && this.D > this.D_std)
                this.backward_gap_balance = true;
            if (forward_stable_price && this.D < this.D_std)
                this.forward_gap_balance = true;
        }
        else if (this.current_side == "forward"){
            if (forward_stable_price && this.D > this.D_std)
                this.forward_gap_balance = true;
            if (backward_stable_price && this.D < this.D_std)
                this.backward_gap_balance = true;
        }    
     }
       if (this.forward_gap_balance){
            if (forward_position_size > 0.0){
                if (this.current_side == "forward"){
                    this.forward_balance_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"red"), forward_first_volume));
                    this.forward_balance_ticket = forward_first_position;
                    Print("d1 ", this.D_std-this.D, " ", forward_first_volume);
                }
                else{
                    this.forward_balance_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"inc"), forward_first_volume));
                    this.forward_balance_ticket = forward_first_position;
                    Print("d2 ", this.D - this.D_std, " ", forward_first_volume);
                }
           }
        }
        if (this.backward_gap_balance){
            if (backward_position_size > 0.0){
                if (this.current_side == "backward"){
                    this.backward_balance_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"red"), backward_first_volume));
                    this.backward_balance_ticket = backward_first_position;
                    Print ("d3 ", this.D_std-this.D, " ", backward_first_volume);
                }           
                else{
                    this.backward_balance_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"inc"), backward_first_volume));
                    this.backward_balance_ticket = backward_first_position;
                    Print("d4 ", this.D - this.D_std, " ", backward_first_volume);
                }
            }
        }
        
        this.forward_catch = false;
        this.forward_catch_size = 0;
        this.backward_catch = false;
        this.backward_catch_size = 0;
        if (true){
            if (this.current_side == "backward"){
                if (forward_stable_price && this.D < this.D_std){
                    this.backward_catch = true;
                    this.backward_catch_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"inc"), this.backward_limit-backward_position_size));
                    Print ("b1 ", this.D_std-this.D, " ", this.backward_limit-backward_position_size);
                }
                if (backward_stable_price && this.D > this.D_std){
                    this.forward_catch = true;
                    this.forward_catch_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"red"), this.forward_limit-forward_position_size));
                    Print ("b2 ", this.D-this.D_std, " ", this.forward_limit-forward_position_size);
                }
            }
            else if (this.current_side == "forward"){
                if (backward_stable_price && this.D < this.D_std){
                    this.forward_catch = true;
                    this.forward_catch_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"inc"), this.forward_limit-forward_position_size));
                    Print ("b3 ", this.D_std-this.D, " ", this.forward_limit-forward_position_size);
                }
                if (forward_stable_price && this.D > this.D_std){
                    this.backward_catch = true;
                    this.backward_catch_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"red"), this.backward_limit-backward_position_size));
                    Print ("b4 ", this.D-this.D_std, " ", this.backward_limit-backward_position_size);
                }
            }
        }
        
        if (this.forward_catch_size > 0.0 || this.backward_catch_size > 0.0){
            this.forward_gap_balance = false;
            this.backward_gap_balance = false;
        }
            
        return true;
  }
//+------------------------------------------------------------------+
void Handler_A::put_position(void)
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

