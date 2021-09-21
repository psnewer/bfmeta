//+------------------------------------------------------------------+
//|                                                       bfmeta.mq5 |
//|                                                        haidi1231 |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
//--- include files
#include <conf.mqh>
#include <Handler.mqh>
#include <Handler_T1.mqh>
#include <Handler_T2.mqh>
#include <Handler_W.mqh>
#include <Handler_A.mqh>
//--- input parameters


Handler handler;
Handler_T1 handler_t1("forward");
Handler_T2 handler_t2("backward");
Handler_A handler_a;
Handler_W handler_w;
string current_handler;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//--- create timer
   current_handler = "t";
   T_level = AccountInfoInteger(ACCOUNT_LEVERAGE);
   unit = SymbolInfoDouble(Symbol(),SYMBOL_TRADE_CONTRACT_SIZE);
   symbol_order_mode = (int)SymbolInfoInteger(Symbol(),SYMBOL_ORDER_MODE);
   
   EventSetTimer(60); 
//---
   return(INIT_SUCCEEDED);
  }
//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
//--- destroy timer
   EventKillTimer();
   
  }
//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {

  }
  
//+------------------------------------------------------------------+
void get_handler()
  {
    if (current_handler == "w"){
        if (forward_position_size == 0 && backward_position_size == 0){
            balance_overflow = 0.0;
            handler_t1 = Handler_T1("forward");
            handler_t2 = Handler_T2("backward");
            current_handler = "t";
        }
    }
    else if (current_handler == "t"){
        if (af(forward_position_size) == af(backward_position_size) && margin > 0.0){
            handler_w = Handler_W();
            current_handler = "w";
        }
        else if(af(forward_position_size) == af(backward_position_size) && forward_position_size > 0.0){
            handler_t1.adjust_rt(handler_t1.tap);
            handler_t1.adjust_guide(forward_position_size);
            handler_t2.adjust_rt(handler_t2.tap);
            handler_t2.adjust_guide(forward_position_size - handler_t2.tap);
        }
    }
            //else if (handler_t1.D >= limit_size && handler_t2.D_std <= 0.0){
            //    if (handler_t1.forward_catch || handler_t1.backward_catch)
            //        if (stable_spread){
            //            //if (handler_t1.alert_rt()){
            //            //    handler_w = Handler_W();
            //            //    current_handler = "w";
            //            //}else{
            //                  handler_a = Handler_A();
            //                  handler_a.current_side = handler_t2.current_side;
            //                  current_handler = "a";
            //            //}
            //        }
            //}
    //}
    //else if (current_handler == "a"){
    //        if (af(handler_a.D) == handler_a.D_std){
    //            if (forward_position_size > backward_position_size){
    //                handler_t1 = Handler_T1("forward");
    //                handler_t2 = Handler_T2("backward");
    //                handler_t1.adjust_rt(forward_position_size - backward_position_size);
    //                handler_t1.adjust_guide(forward_position_size);
    //                handler_t2.adjust_rt(backward_position_size / (forward_position_size - backward_position_size) * _tap);
    //                handler_t2.adjust_guide(backward_position_size);
    //            }
    //            else{
    //                handler_t1 = Handler_T1("backward");
    //                handler_t2 = Handler_T2("forward");
    //                handler_t1.adjust_rt(2.0*(backward_position_size - forward_position_size));
    //                handler_t1.adjust_guide(backward_position_size);
    //                handler_t2.adjust_rt(2.0*forward_position_size / (backward_position_size - forward_position_size) * _tap);
    //                handler_t2.adjust_guide(forward_position_size);
    //            }
    //            current_handler = "t";
    //        }
    //}
  }
 //+------------------------------------------------------------------+
//| Timer function                                                   |
//+------------------------------------------------------------------+
void OnTimer()
  {
    double forward_first_price = UINT_MAX;
    double backward_first_price = 0.0;
    forward_goods = 0.0;
    backward_goods = 0.0;
    forward_position_size = 0.0;
    backward_position_size = 0.0;
    int total=PositionsTotal();
    for (int i=total-1; i>=0; i--){
        ulong ticket = PositionGetTicket(i);
        double size = PositionGetDouble(POSITION_VOLUME);
        double price_open = PositionGetDouble(POSITION_PRICE_OPEN);
        double profit = PositionGetDouble(POSITION_PROFIT);
        ENUM_POINTER_TYPE type = PositionGetInteger(POSITION_TYPE);
        if (type == POSITION_TYPE_BUY){
            forward_position_size += size;
            forward_goods += profit;
            if (price_open < forward_first_price){
                forward_first_price = price_open;
                forward_first_position = ticket;
                forward_first_volume = size;
            }
        }
        else if (type == POSITION_TYPE_SELL){
            backward_position_size += size;
            backward_goods += profit;
            if (price_open > backward_first_price){
                backward_first_price = price_open;
                backward_first_position = ticket;
                backward_first_volume = size;
            }
        }
      } 
    
      bid_1 = SymbolInfoDouble(Symbol(),SYMBOL_BID);
      ask_1 = SymbolInfoDouble(Symbol(),SYMBOL_ASK);
      tick_price = (bid_1 + ask_1) / 2.0;
      Print("price ", ask_1, " ", bid_1, " ", tick_price);
      
    if (current_handler == "t"){
        if (handler_t1.get_flag() && handler_t2.get_flag()){
            get_handler();
            if (current_handler == "t"){
                Print("aaaa ", TimeCurrent(), " ", current_handler);
                Print(balance_overflow, " ", margin, " ", goods_rt);
                if (stable_spread){
                    if (handler_t1.forward_balance_size >= _tap || handler_t1.forward_catch_size >= _tap || handler_t1.backward_balance_size >= _tap || handler_t1.backward_catch_size >= _tap)
                        handler_t1.put_position();
                    else
                        handler_t2.put_position();
                   }
               }
            }
        else
            Print ("qqqq", " ", GetLastError());
     }
     else if (current_handler == "w"){
             handler_w.get_flag();
             get_handler();
             if (current_handler == "w"){
                 Print("aaaa ", TimeCurrent(), " ", current_handler);
                 Print(balance_overflow, " ", margin, " ", goods_rt);
                 if (stable_spread)
                     handler_w.put_position();
             } 
     }
     else if (current_handler == "a"){
         if (handler_a.get_flag()){
             get_handler();
             if (current_handler == "a"){
                 Print("aaaa ", TimeCurrent(), " ", current_handler);
                 Print(balance_overflow, " ", margin, " ", goods_rt);
                 if (stable_spread)
                     handler_a.put_position();
             }
         }
         else
             Print ("qqqq ",GetLastError());
     }
   
  }
//+------------------------------------------------------------------+
//| Trade function                                                   |
//+------------------------------------------------------------------+
void OnTrade()
  {
    
  }
//+------------------------------------------------------------------+
//| TradeTransaction function                                        |
//+------------------------------------------------------------------+
void OnTradeTransaction(const MqlTradeTransaction& trans,
                        const MqlTradeRequest& request,
                        const MqlTradeResult& result)
  {
    ENUM_TRADE_TRANSACTION_TYPE type = (ENUM_TRADE_TRANSACTION_TYPE)trans.type;
    if (result.deal != 0){      
        ulong ticket = result.deal;
        HistoryDealSelect(ticket);       
        double profit = HistoryDealGetDouble(ticket,DEAL_PROFIT);
        ENUM_DEAL_REASON reason = HistoryDealGetInteger(ticket,DEAL_REASON);
        if (reason == DEAL_REASON_EXPERT || reason == DEAL_REASON_SO)
            balance_overflow += profit;
    } 
  }
//+------------------------------------------------------------------+
//| Tester function                                                  |
//+------------------------------------------------------------------+
double OnTester()
  {
//---
   double ret=0.0;
//---

//---
   return(ret);
  }
//+------------------------------------------------------------------+
//| TesterInit function                                              |
//+------------------------------------------------------------------+
void OnTesterInit()
  {
//---
   
  }
//+------------------------------------------------------------------+
//| TesterPass function                                              |
//+------------------------------------------------------------------+
void OnTesterPass()
  {
//---
   
  }
//+------------------------------------------------------------------+
//| TesterDeinit function                                            |
//+------------------------------------------------------------------+
void OnTesterDeinit()
  {
//---
   
  }
//+------------------------------------------------------------------+
//| ChartEvent function                                              |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
  {
//---
   
  }
//+------------------------------------------------------------------+
//| BookEvent function                                               |
//+------------------------------------------------------------------+
void OnBookEvent(const string &symbol)
  {
    
   
  }
//+------------------------------------------------------------------+
