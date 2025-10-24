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
    double D;
    double D_std;
    
    bool get_flag();
    void put_position();
    
    void adjust_guide(double D_std);
    
    Handler_T2(double init_tap);
  };
//+------------------------------------------------------------------+
//|                                                                  |
//+------------------------------------------------------------------+
Handler_T2::Handler_T2(double init_tap)
  {
    this.tip = "t2";
    this.tap = _tap;
    this.T_guide = -limit_size;
  }
//+------------------------------------------------------------------+
bool Handler_T2::get_flag()
  {
    if (forward_position_size == 0 && backward_position_size == 0)
        if (margin < 0.0)
            return false;

    this.get_std_flag();

    this.D = backward_position_size;

    if (first_price > 0.0)
        this.D_std = this.T_guide - (first_price - tick_price) / m5_hl;
    
    if (this.D_std < this.D && this.D == 0.0){
        this.adjust_guide(this.D);
    }

    Print (this.tip, " ", this.T_guide);
    Print (this.D, " ", this.D_std);

    this.gap_balance = false;
    this.balance_size = 0;

    if (true){
        if (stable_spread && this.D > this.D_std)
            this.gap_balance = true;
     }
       
    if (this.gap_balance){
         if (backward_position_size > 0.0){
                 this.balance_size = af(MathMin(cutoff(this.tap,0,this.D,this.D_std,"red"), backward_first_volume));
                 this.balance_ticket = backward_first_position;
                 Print ("d3 ", this.D-this.D_std, " ", backward_first_volume);
         }
    }
    
    this.catch = false;
    this.catch_size = 0;
    if (true){
            if (stable_spread && this.D < this.D_std) {
                this.catch = true;
                this.catch_size = af(MathMin(cutoff(this.tap, 0, this.D, this.D_std, "inc"),limit_size - backward_position_size));
                Print ("b2 ", this.D_std - this.D, " ", limit_size - backward_position_size);
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

      if (order_type == ORDER_TYPE_SELL && order_magic == 0){
          if (this.catch){
              if (bid_1 < order_price){
                  MqlTradeRequest request={};
                  MqlTradeResult result={};
                  request.action = TRADE_ACTION_REMOVE;
                  request.order = order_id;
                  OrderSend(request,result);
              }
          }
      }
      else if (order_type == ORDER_TYPE_SELL && order_magic && 1000){
          if (this.gap_balance){
              if (order_price < ask_1){
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
          if (backward_position_size < limit_size){
              if (this.catch && this.catch_size > 0){
                  MqlTradeRequest request={};
                  MqlTradeResult result={};
                  request.action = TRADE_ACTION_DEAL;
                  request.symbol = _Symbol;
                  request.type = ORDER_TYPE_SELL;
                  request.volume = this.catch_size;
                  request.price = bid_1;
                  request.deviation = 0;
                  request.magic = 0;
                  OrderSend(request,result);
              }
          }
          if (this.gap_balance){
              if (backward_position_size > 0){
                  if (this.balance_size > 0){
                      MqlTradeRequest request={};
                      MqlTradeResult result={};
                      request.action = TRADE_ACTION_DEAL;
                      request.symbol = _Symbol;
                      request.type = ORDER_TYPE_BUY;
                      request.position = this.balance_ticket;
                      request.volume = this.balance_size;
                      request.price = ask_1;
                      request.deviation = 0;
                      request.magic = 1000;
                      OrderSend(request,result);
                  }
              }
           }
      
   }
}
//+------------------------------------------------------------------+
void Handler_T2::adjust_guide(double D_std)
  {
    this.T_guide += D_std - (this.T_guide - (first_price - tick_price) / m5_hl);
    this.D_std = D_std;
  }
//+------------------------------------------------------------------+
