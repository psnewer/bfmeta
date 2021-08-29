//+------------------------------------------------------------------+
//|                                                         conf.mqh |
//|                                                        haidi1231 |
//|                                             https://www.mql5.com |
//+------------------------------------------------------------------+
#property copyright "haidi1231"
#property link      "https://www.mql5.com"
//+------------------------------------------------------------------+
//| defines                                                          |
//+------------------------------------------------------------------+
// #define MacrosHello   "Hello, world!"
// #define MacrosYear    2010
//+------------------------------------------------------------------+
//| DLL imports                                                      |
//+------------------------------------------------------------------+
// #import "user32.dll"
//   int      SendMessageA(int hWnd,int Msg,int wParam,int lParam);
// #import "my_expert.dll"
//   int      ExpertRecalculate(int wParam,int lParam);
// #import
//+------------------------------------------------------------------+
//| EX5 imports                                                      |
//+------------------------------------------------------------------+
// #import "stdlib.ex5"
//   string ErrorDescription(int error_code);
// #import
//+------------------------------------------------------------------+

double af(double ff){
    if (ff < 0.0)
        return (int) (ff * 100 - 0.001) / 100.0;
    else if (ff > 0.0)
        return (int) (ff * 100 + 0.001) / 100.0;
    else
        return ff;
}

double cutoff(double tap,double star,double D,double D_std,string der="",double top=0,double bot=0){
    double nn = star;
    if (D_std < star)
        nn =   star + int((D_std - star) / tap - 0.001) * tap;
    else if (D_std > star)
        nn =   star + int((D_std - star) / tap + 0.001) * tap;

    double res;
    if (der == "inc"){
        if (MathAbs(D_std - nn) < 0.0001)
            res = af(D_std - D);
        else
            if (D_std > star)
                res = nn - D;
            else
                res = (nn - tap) - D;
    }
    else if (der == "red"){
        if (MathAbs(D_std - nn) < DBL_MIN)
            res = af(D - D_std);
        else{
            if (D_std > star)
                res = D - (nn + tap);
            else
                res = D -nn;
            }
    }
    if (top != 0){
        if (nn > top)
            res -= nn - top;
    }
    else if (bot != 0){
        if (nn < bot)
            res -= bot - nn;
    }
    if (res < 0.0)
        res = 0.0;
    return af(res);
}