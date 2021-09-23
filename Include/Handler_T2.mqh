//+------------------------------------------------------------------+
//|                                                   Handler_T2.mqh |
//|                                                        haidi1231 |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "haidi1231"
#property link      "https://www.mql5.com"
#property version   "1.00"

#include <Handler.mqh>
#include <conf.mqh>

class Handler_T2 : public Handler
  {
public:
    double tap;
    double T_guide;
    double T_rt;
    double pre_D;
    double D;
    double D_std;
    double S_up;
    double S_dn;
    
    bool get_flag();
    void put_position();
    
    void adjust_guide(double D_std);
    void adjust_rt(double D_std);
    void reset_St();
    
    Handler_T2(string side);
  };
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
Handler_T2::Handler_T2(string side)
  {
    this.tip = "t2";
    this.current_side = side;
    this.tap = _tap;
    this.T_guide = 0.0;
    this.T_rt = 0.0;
    this.pre_D = 0.0;
  }
//+------------------------------------------------------------------+
bool Handler_T2::get_flag()
  {
    if (forward_position_size == 0 && backward_position_size == 0)
        if (margin < 0.0)
            return false;

    this.get_std_flag();

    if (this.current_side == "forward")
        this.D = forward_position_size;
    else if (this.current_side == "backward")
        this.D = backward_position_size;
        
    //if (forward_position_size == 0.0 && backward_position_size == 0.0){
    //    if (this.pre_D > 0.0){
    //        this.T_guide = _tap;
    //        this.T_rt = 0.0;
    //        this.pre_D = 0.0;
    //    }
    //}

    if (this.T_rt == 0.0){
        this.T_rt = tick_price / (m5_hl * T_level);
        this.reset_St();
    }

    this.D_std = this.T_guide - goods_rt * this.T_rt;

    if (cutoff(this.tap, 0, this.D, this.D_std, "red") == 0.0){
        if (af(this.pre_D) != af(this.D)){
                this.pre_D = this.D;
                this.reset_St();
        }
    }
    else if (cutoff(this.tap, 0, this.D, this.D_std, "red") > 0.0){
        if ((this.current_side == "forward" && tick_price <= this.S_dn) || (this.current_side == "backward" && tick_price >= this.S_up))
            this.reset_St();
    }

    Print (this.tip, " ", this.current_side, " ", this.T_guide, " ", this.T_rt);
    Print ("St ", this.S_up, " ", this.S_dn);
    Print (this.D, " ", this.D_std, " ", forward_stable_price, " ", backward_stable_price);

    this.forward_gap_balance = false;
    this.forward_balance_size = 0;
    this.backward_gap_balance = false;
    this.backward_balance_size = 0;
    if (true){
        if (this.current_side == "backward"){
            if (backward_stable_price && this.D > this.D_std)
                if (tick_price <= this.S_dn || backward_position_size > forward_position_size)
                    this.backward_gap_balance = true;
        }
        else if (this.current_side == "forward"){
            if (forward_stable_price && this.D > this.D_std)
                if (tick_price >= this.S_up || forward_position_size > backward_position_size)
                    this.forward_gap_balance = true;
        }
     }
       
     if (this.forward_gap_balance){
         if (forward_position_size > 0.0){
             if (this.current_side == "forward"){
                 this.forward_balance_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"red"), forward_first_volume));
                 this.forward_balance_ticket = forward_first_position;
                 Print ("d1 ", this.D-this.D_std, " ", forward_first_volume);
             }
         }
     }
     if (this.backward_gap_balance){
         if (backward_position_size > 0.0){
             if (this.current_side == "backward"){
                 this.backward_balance_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"red"), backward_first_volume));
                 this.backward_balance_ticket = backward_first_position;
                 Print ("d3 ", this.D-this.D_std, " ", backward_first_volume);
             }
         }
    }
    
    this.forward_catch = false;
    this.forward_catch_size = 0;
    this.backward_catch = false;
    this.backward_catch_size = 0;
    if (true){
        if (this.current_side == "backward"){
            if (forward_stable_price && this.D < this.D_std)
                //if (tick_price >= this.S_up)
                {
                    this.backward_catch = true;
                    this.backward_catch_size = af(MathMin(cutoff(this.tap, 0, this.D, this.D_std, "inc"),limit_size - backward_position_size));
                    Print ("b2 ", this.D_std - this.D, " ", limit_size - backward_position_size);
                }
        }
        else if (this.current_side == "forward"){
            if (backward_stable_price && this.D < this.D_std)
                //if (tick_price <= this.S_dn)
                {
                    this.forward_catch = true;
                    this.forward_catch_size = af(MathMin(cutoff(this.tap, 0, this.D, this.D_std, "inc"),limit_size - forward_position_size));
                    Print ("b4 ", this.D_std - this.D, " ", limit_size - forward_position_size);
                }
        }
    }
    
    if (af(forward_position_size) == af(backward_position_size) && forward_position_size > 0.0){
        if (this.current_side == "forward" && tick_price < this.S_dn){
            this.reset_St();
        }
        else if (this.current_side == "backward" && tick_price > this.S_up){
            this.reset_St();
        }     
    }
    
    return true;
  }
//+------------------------------------------------------------------+
void Handler_T2::put_position(void)
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
      if (this.forward_gap_balance && this.backward_gap_balance && (SYMBOL_ORDER_CLOSEBY&symbol_order_mode)==SYMBOL_ORDER_CLOSEBY){
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
      else{
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
          if (this.forward_gap_balance){
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
          if (this.backward_gap_balance){
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
      }
   }
}
//+------------------------------------------------------------------+
void Handler_T2::adjust_guide(double D_std)
  {
    this.T_guide += D_std - (this.T_guide - goods_rt * this.T_rt);
    this.D_std = D_std;
  }
//+------------------------------------------------------------------+
void Handler_T2::adjust_rt(double D_std)
  {
    if (D_std > 0.0)
        this.T_rt = -D_std / goods_rt;
  }
//+------------------------------------------------------------------+
void Handler_T2::reset_St()
  {
    this.S_up = tick_price + m5_hl;
    this.S_dn = tick_price - m5_hl;
  }
//+------------------------------------------------------------------+
