# coding:utf-8
from mock import mockbase
import sys
import os
import os.path
from collections import OrderedDict
from operator import itemgetter
from signals import exitsigs 
from prettytable import PrettyTable


class KLINE(mockbase):

    def __init__(self, startday, baseday, codearr, dirs, forcetp):

        self.__stopwin = 1.20
        self.__stoplos = 0.90

        super(KLINE, self).__init__(startday, baseday)

        self.__dropout     = {}
        self.__observed    = {}
        self.__qs          = {}
        self.__opset       = {} 
        self.__clset       = {}
        self.__hiset       = {}
        self.__lwset       = {}
        self.__lastdayk    = {}

        subdir = 'kline'
        for c in codearr:
            tmp   = c.split('-')
            fname = tmp[-1]
            fsize = fname.split('.')
            if len(fsize) > 2:
                continue
            code  = fname[0:8]
            self.loadMtime(dirs, code)
            self.loadTrades(dirs, subdir, code)

    def resortTrades(self, tups):
        return tups

    def initExit(self, mtime, instdaymap, lastdayk):
        self.__exit = exitsigs.ExitSignals(mtime, instdaymap, lastdayk)

        self.__exit.setOHLC(self.__opset, self.__hiset, \
                            self.__lwset, self.__clset)

    def setStop(self, win, loss):
        self.__stopwin = win
        self.__stoplos = loss

    def mockrange(self):
        print 'TEST:', self.getsDay(), self.geteDay()

    def initDayK(self, op, hi, lw, cl, lastdayk):
        self.__opset    = op
        self.__clset    = cl
        self.__hiset    = hi
        self.__lwset    = lw
        self.__lastdayk = lastdayk

    def initZUHE(self, dirs, subdir, forcetp):
        zuhe  = {}
        ozuhe = []
        fname = './data/zuhe.kline.txt'
        if os.path.isfile(fname): 
            for line in open(fname):
                arr = line.strip().split(' ')
                zuhe[arr[2]] = arr[0]
                ozuhe.append(arr[2])
        return (zuhe, ozuhe)

    # 选股
    def select(self, tup, nday):

        zuhe  = tup[0]
        ozuhe = tup[1]
        yday  = tup[2]

        tzuhe = PrettyTable(['T日', '代码', '名称', '止盈价', '止损价', 'Holds'])
        tzuhe.float_format = '.4'
        tzuhe.align = 'l'
        for k in ozuhe:
            maxhold = 2
            inst   = k
            sigday = zuhe[k]
            trades = self.getTrades()[sigday]
            name   = ''
            for t in trades:
                if t[0] == k:
                    name   = t[1]
                    if float(t[5]) == 8 or float(t[5]) == 6:
                        maxhold = 3
                        break
            # 长阴破位离场
            mkey     = k + '|' + sigday
            fibprice = float(self.getMtime()[mkey][30])
            jypw     = self.__exit.JYPW(inst, yday, nday, None, fibprice)
            if jypw == 1:
                print 'DEBUG', 'JYPW SELL on OPEN', yday, nday, inst, name, fibprice 
                continue
            holds = self.__exit.HoldTime(k, sigday, nday)
            if holds == maxhold:
                print 'DEBUG', 'MXHD SELL on CLOSE', nday, inst, name 
                continue
            tzuhe.add_row([nday, k, name, '--', '--', holds])
        print tzuhe

        # 选股
        tzuhe = PrettyTable(['T日', '代码', '名称', '得分', '收益率', '持有天数', '开仓价', '止盈价', '止损价', '手数'])
        tzuhe.float_format = '.4'
        tzuhe.align = 'l'
        trades = self.getTrades()[nday]
        stocks = []
        for t in trades:
            inst    = t[0]
            name    = t[1]
            jhold   = -0.50
            maxhold = 2

            if float(t[5]) == 8 or float(t[5]) == 6:
                maxhold = 3

            if float(t[5]) == 5:
                print 'DEBUG', 'Drop Buy CROSS_STAR', nday, inst, name, t[5]
                continue

            if float(t[2]) > 5000:
                print 'DEBUG', 'Drop Buy BIGGER SCORE', nday, inst, name, t[2], t[5]
                continue

            if float(t[5]) == 5 or float(t[5]) == 7:
                jhold = 0.00
                if float(t[2]) < 0:
                    print 'DEBUG', 'Drop Buy SCORE < 0', nday, inst, name, t[2], t[5]
                    continue

            if float(t[5]) == 6:
                jhold = -0.04

            if float(t[5]) == 8:
                jhold = -0.04
                if float(t[2]) < 0:
                    print 'DEBUG', 'Drop Buy SCORE < 0', nday, inst, name, t[2], t[5]
                    continue

            if (float(t[5]) == 2 or float(t[5]) == 4) and float(t[2]) < -100:
                print 'DEBUG', 'Drop Buy MAGIC SCORE', nday, inst, t[2], t[5]
                continue

            nclose = float(self.__clset[t[0] + '|' + nday])
            tmin = "{:.4f}".format(nclose * (1 + jhold)) 
            tmax = "{:.4f}".format(nclose * 1.03)
            stocks.append((t[0], tmin, tmax, maxhold))
            price = '[' + str(tmin) + ' ' + str(tmax) + ']'
            tzuhe.add_row([nday, inst, name, t[2], '--', maxhold, price, '--', '--', '--'])
        print tzuhe

        self.dumpSelect(stocks, nday)

    def dumpSelect(self, tups, nday):
        f = open('./output/kline/' + nday + '.kl.txt', 'w')
        for t in tups:
            line = t[0][-6:] + ',hcqs,ctgd,' + nday + ',' + t[1] + ',' + t[2] + ',' + str(t[3])
            f.write(line)
            f.write('\n')
        f.close()

    def buy(self, tup, nxday, nday, tp):
        buyprice = None; ret = True

        inst  = tup[0]
        name  = tup[1]
        jhold = -0.50
        
        mkey = inst + '|' + nday
        fibs = float(self.getMtime()[mkey][28])
        if fibs == 1:
            print 'DEBUG', 'Drop Buy Fibs StopLine', nday, inst, fibs 
            return buyprice

        bias5120 = float(self.getMtime()[mkey][29])
        if bias5120 != 1024 and bias5120 > 0.70:
            print 'DEBUG', 'Drop Buy High Bias5120', nday, inst, bias5120 
            return buyprice

        trades = self.getTrades()[nday]
        for t in trades:
            if t[0] == inst:
                if float(t[5]) == 5:
                    return buyprice

                if float(t[2]) > 5000:
                    print 'DEBUG', 'Drop Buy BIGGER SCORE', nday, inst, name, t[2], t[5]
                    return buyprice

                if float(t[5]) == 5 or float(t[5]) == 7:
                    jhold = 0.00
                    if float(t[2]) < 0:
                        return buyprice

                if float(t[5]) == 6:
                    jhold = -0.04

                if float(t[5]) == 8:
                    jhold = -0.04
                    if float(t[2]) < 0:
                        return buyprice

                if (float(t[5]) == 2 or float(t[5]) == 4) and float(t[2]) < -100:
                    print 'DEBUG', 'Drop Buy MAGIC SCORE', nday, inst, t[2], t[5]
                    return buyprice

        dkey = inst + '|' + nxday
        if dkey not in self.__opset:
            ret = False
            print 'DEBUG:', nday, 'Drop Suspension ', inst, name, nxday, dkey
            return buyprice

        nxopen = float(self.__opset[dkey])
        nclose = float(self.__clset[inst + '|' + nday])

        # 过滤高空3个点或者低开1个点的价格
        jump = (nxopen - nclose) / nclose 
        if jump > 0.03 or jump < jhold:
            print 'DEBUG:', nday, 'DROP BarOpen', inst, name, nxday, nclose, nxopen, jump  
            ret = False
        if ret is True:
            bkey = inst + '|' + nxday
            # 按次日的开盘价买入
            if tp == 0:
                if bkey in self.__opset:
                    buyprice = float(self.__opset[bkey])
        return buyprice 
  
    def pred(self, pkey):
        ret = 0.0 
        return ret

    def filter(self, key):
        ret    = False
        reason = ''
        return (ret, reason)

    def forceSell(self, tup, tday, nxday, flag, ref=None):
        inst = tup[0]
        sellprice = None
        if nxday is None:
            return sellprice
        skey = inst + '|' + nxday
        if skey not in self.__hiset:
            skey = inst + '|' + self.__lastdayk[inst]
        if flag == 1:
            sellprice = float(self.__opset[skey])
        if flag == 2:
            op = float(self.__opset[skey])
            lw = float(self.__lwset[skey])
            if op < ref:
                sellprice = op
            else:
                if lw < ref:
                    sellprice = ref
        return sellprice

    def sell(self, tup, tday, nxday, instlast, yday, baseday=None):
        sellprice = None

        sigday  = tup[0]
        tup     = tup[1]
        inst    = tup[0]
        maxhold = 2

        if nxday is None:
            return sellprice

        skey = inst + '|' + nxday
        if skey not in self.__hiset:
            skey = inst + '|' + self.__lastdayk[inst]

        cls  = float(self.__clset[skey])
        ops  = float(self.__opset[skey])
        # tkdk = self.__exit.tkdk(inst, tday, nxday)
        # if tkdk == 1:
        #     print 'DEBUG', 'TKDK SELL on OPEN ', tday, nxday, inst 
        #     sellprice = ops 
        #     return sellprice

        mkey     = inst + '|' + sigday 
        # 长阴破位离场
        fibprice = float(self.getMtime()[mkey][30])
        jypw     = self.__exit.JYPW(inst, yday, tday, nxday, fibprice)
        if jypw == 1:
            print 'DEBUG', 'JYPW SELL on OPEN', yday, tday, nxday, inst, fibprice 
            sellprice = ops 
            return sellprice

        trades = self.getTrades()[sigday]
        for t in trades:
            if t[0] == inst:
                if float(t[5]) == 8 or float(t[5]) == 6:
                    maxhold = 3
                    break

        # 买入第二日卖出
        holds = self.__exit.HoldTime(inst, sigday, tday)

        if holds == maxhold:
            sellprice = cls

        return sellprice
#
