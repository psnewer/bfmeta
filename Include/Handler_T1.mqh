//+------------------------------------------------------------------+
//|                                                   Handler_T1.mqh |
//|                                                        haidi1231 |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "haidi1231"
#property link      "https://www.mql5.com"
#property version   "1.00"

#include <conf.mqh>
#include <Handler.mqh>

class Handler_T1: public Handler
  {
public:
    
    virtual bool get_flag() override;
    virtual void put_position() override;
    
    void adjust_guide(double D_std);
    
    Handler_T1(double init_tap);
  };
//+------------------------------------------------------------------+
bool Handler_T1::get_flag()
  {
    if (forward_position_size == 0 && backward_position_size == 0)
        if (margin < 0.0)
            return false;

    this.get_std_flag();

    this.D = forward_position_size;

    if (tick_price > first_price && this.D == 0.0){
        first_price = tick_price;
    }
    
    this.D_std = this.D; 
    if (first_price > 0.0)
        this.D_std = this.T_guide - (tick_price - first_price) / m5_hl * this.tap;
    
    Print (this.tip, " ", this.D, " ", this.D_std);

    this.gap_balance = false;
    this.balance_size = 0;
    
    if (true){
        if (stable_spread && this.D > this.D_std)
            this.gap_balance = true;
    }

    if (this.gap_balance){
        if (forward_position_size > 0.0){
                this.balance_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"red"), forward_first_volume));
                this.balance_ticket = forward_first_position;
                Print ("d1 ", this.D-this.D_std, " ", forward_first_volume);
        }
    }
    
    this.catch = false;
    this.catch_size = 0;
    if (true){
            if (stable_spread && this.D < this.D_std){
                this.catch = true;
                this.catch_size = af(MathMin(cutoff(this.tap, 0, this.D, this.D_std, "inc"),limit_size - forward_position_size));
                Print ("b4 ", this.D_std - this.D, " ", limit_size - forward_position_size);
            }
    }
      
    return true;
  }
//+------------------------------------------------------------------+
Handler_T1::Handler_T1(double init_tap)
  {
    this.tip = "t1";
    this.tap = _tap;
    this.T_guide = init_tap;
  }
//+------------------------------------------------------------------+
void Handler_T1::put_position(void)
{
  int orders = OrdersTotal();
  for (int i = orders - 1; i >= 0; i--){
      ulong  order_id = OrderGetTicket(i);
      double order_price = OrderGetDouble(ORDER_PRICE_OPEN);
      ENUM_ORDER_TYPE order_type = OrderGetInteger(ORDER_TYPE);
      ulong order_magic = OrderGetInteger(ORDER_MAGIC);
    
      if (order_type == ORDER_TYPE_BUY && order_magic == 0){
          if (this.catch){
              if (ask_1 > order_price){
                  MqlTradeRequest request={};
                  MqlTradeResult result={};
                  request.action = TRADE_ACTION_REMOVE;
                  request.order = order_id;
                  OrderSend(request,result);
              }
          }
      }
      else if (order_type == ORDER_TYPE_SELL && order_magic == 1000){
          if (this.gap_balance){
              if (order_price > bid_1){
                  MqlTradeRequest request={};
                  MqlTradeResult result={};
                  request.action = TRADE_ACTION_REMOVE;
                  request.order = order_id;
                  OrderSend(request,result);
               }
           }             
      }
}
  if (orders == 0){
          if (forward_position_size < limit_size){
             if (this.catch && this.catch_size > 0){
                  MqlTradeRequest request={};
                  MqlTradeResult result={};
                  request.action = TRADE_ACTION_DEAL;
                  request.symbol = _Symbol;
                  request.type = ORDER_TYPE_BUY;
                  request.volume = this.catch_size;
                  request.price = ask_1;
                  request.deviation = 0;
                  request.type_filling = ORDER_FILLING_IOC;
                  request.magic = 0;
                  Print("1111");
                  OrderSend(request,result);
             }
          }
          if (this.gap_balance){
              if (forward_position_size > 0){
                  if (this.balance_size > 0){
                      MqlTradeRequest request={};
                      MqlTradeResult result={};
                      request.action = TRADE_ACTION_DEAL;
                      request.symbol = _Symbol;
                      request.type = ORDER_TYPE_SELL;
                      request.position = this.balance_ticket;
                      request.volume = this.balance_size;
                      request.price = bid_1;
                      request.deviation = 0;
                      request.type_filling = ORDER_FILLING_IOC;
                      request.magic = 1000;            
                         OrderSend(request,result);
                     }
              }
          }
      
   }
}
//+------------------------------------------------------------------+
void Handler_T1::adjust_guide(double D_std)
  {
    this.T_guide += D_std - (this.T_guide - (tick_price - first_price) / m5_hl * this.tap);
    this.D_std = D_std;
  }
//+------------------------------------------------------------------+
