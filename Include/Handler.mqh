//+------------------------------------------------------------------+
//|                                                      Handler.mqh |
//|                                                        haidi1231 |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "haidi1231"
#property link      "https://www.mql5.com"
#property version   "1.00"

input double   first_limit=0.04;
input double   _tap=0.02;
input double   a_limit=0.04;
input double   limit_size=0.08;
input double   limit_spread=0.0001;
input ENUM_TIMEFRAMES      M5=PERIOD_M5;

double T_level;
double unit;

double forward_goods = 0.0;
double backward_goods = 0.0;
static double balance_overflow = 0.0;
static double margin = 0.0;
static double goods_rt = 0.0;

static double bid_1 = 0.0;
static double ask_1 = 0.0;
static double tick_price = 0.0;
static double forward_position_size = 0.0;
static double backward_position_size = 0.0;

static ulong  forward_first_position = 0;
static double forward_first_volume = 0.0;
static ulong  backward_first_position = 0;
static double backward_first_volume = 0.0;

static bool   forward_stable_price = false;
static bool   backward_stable_price = false;
static bool   stable_spread = false;

static double m5_oc = 0.0;
static double m5_hl = 0.0;

class Handler
  {
public: 
   string tip; 
   bool forward_gap_balance;
   bool backward_gap_balance;
   bool forward_catch;
   bool backward_catch;
   double forward_balance_size;
   double backward_balance_size;
   double forward_catch_size;
   double backward_catch_size;
   ulong forward_balance_ticket;
   ulong backward_balance_ticket;
   string current_side;
   
   void get_std_flag();
  };                                                           
//+------------------------------------------------------------------+
void Handler::get_std_flag()
  {
    MqlRates M1_rates[];
    ArraySetAsSeries(M1_rates,true);
    int copied=CopyRates(Symbol(),PERIOD_M1,0,11,M1_rates);
    MqlRates M5_rates[];
    ArraySetAsSeries(M5_rates,true);
    copied=CopyRates(Symbol(),M5,0,10,M5_rates);
    forward_stable_price = false;
    backward_stable_price = false;
    stable_spread = false;
    if (ask_1 - bid_1 < limit_spread){
        stable_spread = true;
        if (ArraySize(M1_rates) > 0){
            double o = M1_rates[0].open;
            double c = M1_rates[0].close;
            if ((c - o) <= 0.0)
                forward_stable_price = true;
            if ((c - o) >= 0.0)
                backward_stable_price = true;
        }
    }

    if (ArraySize(M5_rates) >= 10){
        double oc[10];
        double hl[10];
            for (int i = 0; i < 10; i++){
                double o = M5_rates[i].open;
                double c = M5_rates[i].close;
                double h = M5_rates[i].high;
                double l = M5_rates[i].low;
                oc[i] = MathIsValidNumber(c - o)?MathAbs(c - o):0.0;
                hl[i] = MathIsValidNumber(h - l)?MathAbs(h - l):0.0;
            }
            double max_oc = oc[ArrayMaximum(oc,0)];
            double max_hl = hl[ArrayMaximum(hl,0)];
            m5_oc = max_oc;
            m5_hl = max_hl;
     }

     Print ("step ", m5_oc, " ", m5_hl);

     double unit_value = tick_price * unit;

     if (forward_position_size == 0.0 && backward_position_size == 0.0)
         balance_overflow = 0.0;

     margin = forward_goods + backward_goods + balance_overflow;
     goods_rt = margin / unit_value * T_level;
  }
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
