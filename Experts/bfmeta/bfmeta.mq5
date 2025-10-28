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
//--- input parameters

Handler* handler_t;

//Handler_T1 handler_t(T_guide);

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
//--- create timer
   T_level = AccountInfoInteger(ACCOUNT_LEVERAGE);
   unit = SymbolInfoDouble(Symbol(),SYMBOL_TRADE_CONTRACT_SIZE);
   symbol_order_mode = (int)SymbolInfoInteger(Symbol(),SYMBOL_ORDER_MODE);
   
   EventSetTimer(60); 
   
   if (current_side == "forward")
      handler_t = new Handler_T1(T_guide);
   else 
      handler_t = new Handler_T2(T_guide);
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
        if(af(forward_position_size) == af(backward_position_size) && balance_overflow > 0.0){
            balance_overflow = 0.0;
            first_price = tick_price;
            if (current_side == "forward")
               handler_t = new Handler_T1(T_guide);
            else 
               handler_t = new Handler_T2(T_guide);
        }
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
        string symbol = PositionGetString(POSITION_SYMBOL);
        if (symbol != _Symbol)
            continue;
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
      
      if (first_price == 0.0)
         first_price = tick_price;
         
      Print("price ", ask_1, " ", bid_1, " ", tick_price, " ", first_price);
      
        if (handler_t.get_flag()){
            get_handler();
                Print(balance_overflow, " ", margin, " ", stable_spread);
                if (stable_spread){
                    if (handler_t.balance_size >= _tap || handler_t.catch_size >= _tap)
                        if (all_in){
                            if (handler_t.D_std <= 0.0)
                                handler_t.put_position();
                        }  
                        else
                            handler_t.put_position();
                   }
            }
        else
            Print ("eeee", " ", GetLastError());
   
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
