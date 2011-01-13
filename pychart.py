# -*- coding: utf-8 -*-
#!/usr/bin/env python
###############################################################################
## pyChart
## 
## A charting/paper trading program written in Python and Qt
## 
## 
## To produce a python module from QTDesigner:
##   pyuic4 -o ui_chart.py -x chartWidget.ui
##   
## TODO:
## 
## Game
## - Add game display (days left, total profit/loss, % profit/loss, goals, etc.)
## - Add goals (eg 2% per month or 20% per year)
## - Prev and Next buttons that don't advance days, just let you view chart.
## 
## Chart
## - Add bottom bar for showing volume and other indicators
## - Add compare, see: http://bigcharts.marketwatch.com/advchart/frames/frames.asp?symb=&time=&freq=
## - Add point and figure chart view
## - Add support for symbol lookup
## - Allow persistent indicators and trendlines
## 
## Accounts
## - Alert user that they have pending orders.
## - Allow user to specify when their order should go through, today's close 
##   or tomorrow's open or other.
## - Add purchase price to portfolio.  Also if stock is already held, make 
##   purchase price average of the two purchases.  Ex: if I own 100 shares of 
##   msft @ 50 and buy 100 more @ 60, the portfolio should say 200 shares @ 55
##
## BUG:
## - Try:  INDEXDJX:.DJI
## - Start program and close first tab.  Or at any time close all tabs.
## - Buy stock in MSFT, then sell it, then open GE, then close MSFT tab.
## - Press "New Tab" with nothing in the symbol box
## - Set indicator(s) then switch stocks, indicators are not persistent
##   This is because the command is specific to the chartView
##   
###############################################################################

from __future__ import division
import sys

from PyQt4 import QtCore, QtGui
from urllib import urlopen

## import QtDesigner UI module
from ui_chart import Ui_chartWidget

import numpy
import math



###############################################################################
##  Account
##  Buy/Sell, Stop/Limit, Account Balance, Percentage Gain/Loss, etc.
###############################################################################

class Position:
  def __init__(self, symbol, shares, price):
    self.isOpen = True
    self.symbol = symbol
    self.shares = shares
    self.price = price              ## The adjusted purchase price
    self.log = [(shares, price)]
    
  def __repr__(self):
    if self.isOpen:
      return str(self.shares) + " @ " + str(self.price)
    else:
      return "$" + str(self.profit) + ' : ' + str(self.profitPercentage) + "%"

  def getPrice(self, symbol, ohlc=4):
    d = [ii.data for ii in chartViews if ii.symbol == symbol]
    if d: 
      return d[0].data[time.currentDay][ohlc]
    else:
      d = Data(symbol)
      return d.currentDay(time.currentDay)[ohlc].data[time.currentDay][1]

  def addShares(self, shares, price):
    self.price = (self.shares*self.price + shares*price) / (self.shares + shares)
    self.shares += shares
    self.log.append((shares, price))
    
  def sellShares(self, shares, price):
    if self.shares - shares <= 0:
      self.closePosition(shares, price)
    else:
      self.price += (shares / self.shares) * (self.price - price)
      self.shares -= shares
    self.log.append((-shares, price))

  def closePosition(self, shares, price):
    self.isOpen = False
    self.profit = (price - self.price) * shares
    self.profitPercentage = ((price / self.price) - 1) * 100


  def value(self):
    if self.isOpen:
      return self.shares * self.getPrice(self.symbol)
    else:
      return 0



class Account:
  def __init__(self):
    self.initialBalance = 10000
    self.balance = self.initialBalance
    self.portfolio = {}
    self.queue = []
    
  def getPrice(self, symbol, ohlc=4):
    d = [ii.data for ii in chartViews if ii.symbol == symbol]
    if d: 
      return d[0].data[time.currentDay][ohlc]
    else:
      d = Data(symbol)
      return d.currentDay(time.currentDay)[ohlc].data[time.currentDay][1]
      
  def addPosition(self, symbol, shares, price):
    if symbol in self.portfolio:
      positionList = self.portfolio[symbol]
      mostRecentPosition = positionList[0]
      if mostRecentPosition.isOpen:
        mostRecentPosition.addShares(shares, price)
      else:
        self.portfolio[symbol].insert(0, Position(symbol, shares, price))
    else:
      self.portfolio[symbol] = [Position(symbol, shares, price)]
  
  
  def buy(self, symbol, shares):
    price = self.getPrice(symbol)
    if not shares or (price*int(shares)) > self.balance: 
      shares = int(self.balance / price)-1
    self.addPosition(symbol, int(shares), price)
    self.balance -= price*int(shares)

  def sell(self, symbol, shares):
    price = self.getPrice(symbol)
    if symbol in self.portfolio:
      currentPosition = self.portfolio[symbol][0]
      if currentPosition.isOpen:
        if not shares or int(shares) > currentPosition.shares:
          shares = currentPosition.shares
        currentPosition.sellShares(int(shares), price)
        self.balance += int(shares) * price
  
  def setStop(self, symbol, price, shares):
    self.queue.append((symbol, price, shares))
  
  def update(self):
    """This will be used for stop-loss, limit, etc orders"""
    for order in self.queue:
      p = self.getPrice(order[0], ohlc=3)
      if p < order[1]:
        self.sell(order[0], order[2])
        
  
  
  def portfolioValue(self):
    pv = self.balance
    for symbol, position in self.portfolio.items():
      pv += position[0].value()
    return pv
    
  
  def portfolioProfit(self):
    return self.portfolioValue() - self.initialBalance
    
  def portfolioPercentage(self):
    return int(((self.portfolioValue()/self.initialBalance) - 1) * 100)
    


###############################################################################
##  Data
##  Download and Access Data, Adjust Prices for Charting, Technical Indicator 
##  Calculation
##  TODO:
##    Rename some of the methods to make more clear
###############################################################################

class Data:
  def __init__(self, symbol):
    self.symbol = symbol
    self.data = self.googDownload(symbol)
    self.low, self.high = 0, 0

  def googDownload(self, symbol):
    dat = urlopen("http://www.google.com/finance/historical?q="+symbol+"&startdate=Dec+30%2C+2000&enddate=Dec+31%2C+2010&num=30&output=csv").read()
    data = [ii.split(',') for ii in dat.split('\n')]
    return [[ii[0], float(ii[1]), float(ii[2]), float(ii[3]), float(ii[4]), int(ii[5])] for ii in data[1:-1]]

  def setHighLow(self, day, length):
    d = self.chartData(day, length)
    self.low, self.high = min([ii[3] for ii in d]), max([ii[4] for ii in d])

  def adjustData(self, day, length):
    self.setHighLow(day, length)
    d = self.chartData(day, length)
    hi,lo = self.high, self.low
    mul = screen.height/(hi-lo)
    return [[ii[0], (ii[1]-lo)*mul, (ii[2]-lo)*mul, (ii[3]-lo)*mul, (ii[4]-lo)*mul, ii[5]] for ii in d]

  def adjustPrices(self, prices):
    mul = screen.height/(self.high-self.low)
    return [(price-self.low)*mul for price in prices]

  def currentDay(self, day):
    return self.data[day]

  def chartData(self, day, length):
    return self.data[day:length+day]

  def loadSymbol(self, symbol):
    self.data = self.googDownload(symbol)

  def forEachPeriod(self, fun, period, day, length, ohlc=4):
    d = self.data[day:day+length+period]
    return [fun([ii for ii in d[c:c+period]]) for c in range(length)]

  def sma(self, period, day, length):
    return self.forEachPeriod(lambda x: sum([ii[4] for ii in x])/period, period, day, length)
  
  def wma(self, period, day, length):
    return self.forEachPeriod(lambda x: numpy.average([d[4] for d in x], weights=range(period,0,-1)), period, day, length)

  def ema(self, period, day, length):
    d = [ii[4] for ii in self.data[day:day+length+period]]
    return self.doEMA(d, period)

  # TODO: Broke! FIX SOON! Other indicators are based on this!!!
  def doEMA(self, d, period):
    ema = [sum(d[:period])/period]
    multiplier = 2 / (1 + period)
    for day in d[period+1:]:
      ema.append(((day - ema[-1]) * multiplier) + ema[-1])
    return ema
    
  # TODO: Add ability to set custom standard deviation multiple
  def bollingerBands(self, period, day, length):
    s = self.sma(period, day, length)
    std = self.forEachPeriod(lambda x: numpy.std([ii[4] for ii in x])*2, period, day, length)
    stdBig = [a+d for a,d in zip(s, std)]
    stdSmall = [a-d for a,d in zip(s,std)]
    return (stdBig, s, stdSmall)
    
  def donchianChannel(self, period, day, length):
    h = self.forEachPeriod(lambda x: max([ii[2] for ii in x]), period, day, length)
    l = self.forEachPeriod(lambda x: min([ii[3] for ii in x]), period, day, length)
    return (l,h)



###############################################################################
##  Time
###############################################################################

class Time:
  def __init__(self):
    self.currentDay = 1



###############################################################################
##  Screen
###############################################################################

class Screen:
  def __init__(self):
    self.width = 1024
    self.height = 860
    


###############################################################################
##  Charting  (QGraphicsScene and QGraphicsView)
##  Draw candlesticks, ohlc, horizontal lines, moving average type lines
###############################################################################

class Scene(QtGui.QGraphicsScene):
  def __init__(self):
    QtGui.QGraphicsScene.__init__(self)
    
    self.setSceneRect(0, 0, screen.width, screen.height)
    self.newLine = None
    self.newLineX = 0
    self.newLineY = 0

  ## Drawing Trendlines
  def mousePressEvent(self, event):
    x, y = event.scenePos().x(), event.scenePos().y()
    self.newLineX, self.newLineY = x, y
    self.newLine = self.addLine(x, y, x, y)
    pen = QtGui.QPen(QtCore.Qt.CustomDashLine)
    pen.setWidth(3)
    pen.setColor(QtGui.QColor(QtCore.Qt.red))
    self.newLine.setPen(pen)

  def mouseMoveEvent(self, event):
    epx = event.scenePos().x()
    epy = event.scenePos().y()
    self.newLine.setLine(epx, epy, self.newLineX, self.newLineY)

    

class ChartView(QtGui.QGraphicsView):
  def __init__(self, symbol):
    QtGui.QGraphicsView.__init__(self)
    
    self.symbol = symbol
    self.scene = Scene()
    self.setScene(self.scene)
    self.data = Data(symbol)
    self.chartLength = 60
    
    self.chartStyle = self.drawCandlesticks
    self.data.setHighLow(time.currentDay, self.chartLength)
    self.drawChart()
    
  def resizeEvent(self, event):
    screen.width, screen.height = event.size().width(), event.size().height()
    self.scene.setSceneRect(0,0,screen.width,screen.height)
    self.drawChart()
    
  ## Basic Chart Styles (Bar, Dot, Line)
  def drawBar(self, day, length):
    d = [ii[4] for ii in self.data.data[day:day+length]]
    self.drawBars(d)

  def drawBars(self, d, color="black"):
    adjustedData = self.data.adjustPrices(d)
    offsetmod = screen.width/len(d)
    offset = screen.width-offsetmod
    b = QtGui.QColor(color)
    for adjusted, real in zip(adjustedData, d):
      body = self.scene.addRect(offset, screen.height-adjusted, offsetmod/2, screen.height+100, brush=b)
      body.setToolTip(str(real))
      offset -= offsetmod

  def drawDot(self, day, length):
    d = [ii[4] for ii in self.data.data[day:day+length]]
    self.drawDots(d)
    
  def drawDots(self, d, color="black"):
    adjustedData = self.data.adjustPrices(d)
    offsetmod = screen.width/len(d)
    offset = screen.width-offsetmod
    b = QtGui.QColor(color)
    for adjusted, real in zip(adjustedData, d):
      body = self.scene.addRect(offset+offsetmod/4, screen.height-adjusted, 2, 2, brush=b)
      body.setToolTip(str(real))
      offset -= offsetmod

  def drawClose(self, day, length):
    d = self.data.chartData(day, length)
    self.drawLine([ii[4] for ii in d])

  def drawLine(self, d, color="black"):
    """Used for moving averages, bollinger bands, etc"""
    p = QtGui.QPen(QtGui.QColor(color), 2, QtCore.Qt.SolidLine)
    d = self.data.adjustPrices(d)
    offsetmod = screen.width/len(d)
    offset = screen.width-offsetmod-offsetmod
    for ii in range(len(d))[1:]:
      self.scene.addLine(offset+offsetmod/4, screen.height-d[ii], offset+offsetmod/4+offsetmod, screen.height-(d[ii-1]), p)
      offset -= offsetmod
      
  ## Main Chart Styles (Candlestick, OHLC, HLC)
  def drawCandlesticks(self, day, length):
    d = self.data.adjustData(day, length)
    offsetmod = screen.width/len(d)
    offset = screen.width-offsetmod

    for ii, today in enumerate(d):
      if today[1] > today[4]:
        b = QtGui.QColor("black")
      else:
        b = QtGui.QColor("white")

      self.scene.addRect(offset+offsetmod/4, screen.height-today[2], 1, today[2]-today[3], brush=b)
      b = self.scene.addRect(offset, screen.height-today[1], offsetmod/2, today[1]-today[4], brush=b)
      
      p = self.data.data[day+ii]
      b.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod

  def drawOHLC(self, day, length):
    d = self.data.adjustData(day, length)
    offsetmod = screen.width/len(d)
    offset = screen.width-offsetmod
    
    for ii, today in enumerate(d):
      b = self.scene.addRect(offset+offsetmod/4, screen.height-today[2], 1, today[2]-today[3])
      self.scene.addRect(offset+offsetmod/4, screen.height-today[4], offsetmod/4, 1)
      self.scene.addRect(offset+offsetmod/4, screen.height-today[1], -(offsetmod/4), 1)
      
      p = self.data.data[day+ii]
      b.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod

  def drawHLC(self, day, length):
    d = self.data.adjustData(day, length)
    offsetmod = screen.width/len(d)
    offset = screen.width-offsetmod
    
    for ii, today in enumerate(d):
      b = self.scene.addRect(offset+offsetmod/4, screen.height-today[2], 1, today[2]-today[3])
      self.scene.addRect(offset+offsetmod/4, screen.height-today[4], offsetmod/4, 1)
      
      p = self.data.data[day+ii]
      b.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod


  def drawHorizontalLines(self, day, length):
    self.data.setHighLow(day, length)
    high, low = self.data.high, self.data.low
    
    # [low, (high-int(low)+1) -> int(high), high]
    lineList = [low]
    c = int(low)+1
    while c < high:
      lineList.append(c)
      c += 1
    lineList.append(high)
    
    adjusted = self.data.adjustPrices(lineList)
    for ii, price in enumerate(adjusted):
      self.scene.addLine(0, screen.height-price, screen.width, screen.height-price)
      # BUG: If scene.addText() is used drawing trendlines breaks, this is reproducable in a minimal example
      t = self.scene.addSimpleText(str(lineList[ii]))
      t.setPos(screen.width-30, screen.height-price)
    

  def drawChart(self):
    self.scene.clear()
    self.scene.update()
    self.drawHorizontalLines(time.currentDay, self.chartLength)
    self.chartStyle(time.currentDay, self.chartLength)



###############################################################################
##  Main
###############################################################################


class Main(QtGui.QWidget):
  def __init__(self):
    QtGui.QWidget.__init__(self)

    # This is always the same
    self.ui = Ui_chartWidget()
    self.ui.setupUi(self)
    
    self.indicators = []

    ## Create a new GraphicsScene and set GraphicsView (chart) to scene
    chartViews.append(ChartView("msft"))
    self.chartView = chartViews[0]
    self.ui.chartTabs.addTab(self.chartView, "msft")

    ## Connect buttons
    self.connect(self.ui.chartLength, QtCore.SIGNAL("valueChanged(int)"), self.onZoomChart)
    self.connect(self.ui.nextDay, QtCore.SIGNAL("clicked()"), self.onNextDay)
    self.connect(self.ui.prevDay, QtCore.SIGNAL("clicked()"), self.onPrevDay)
    self.connect(self.ui.next30, QtCore.SIGNAL("clicked()"), self.onNext30)
    self.connect(self.ui.prev30, QtCore.SIGNAL("clicked()"), self.onPrev30)
    self.connect(self.ui.buy, QtCore.SIGNAL("clicked()"), self.onBuy)
    self.connect(self.ui.sell, QtCore.SIGNAL("clicked()"), self.onSell)
    
    ## Indicators
    self.connect(self.ui.addIndicator, QtCore.SIGNAL("clicked()"), self.onAddIndicator)

    ## Chart Styles
    self.connect(self.ui.chartStyle, QtCore.SIGNAL("currentIndexChanged(int)"), self.onChartStyleChange)

    ## Chart and Tab Controls
    self.connect(self.ui.symbolEntry, QtCore.SIGNAL("returnPressed()"), self.onNewTab)
    self.connect(self.ui.newTab, QtCore.SIGNAL("clicked()"), self.onNewTab)
    self.connect(self.ui.chartTabs, QtCore.SIGNAL("currentChanged(int)"), self.onChangeTab)
    self.connect(self.ui.chartTabs, QtCore.SIGNAL("tabCloseRequested(int)"), self.onCloseTab)
    
    ## Maximize screen 
    #self.setWindowState(QtCore.Qt.WindowMaximized)
    
    ## Defaults
    #self.ui.chartTabs.setTabsClosable(True)
    self.update()
    
    



  #############################################################################
  ## Event Handlers
  #############################################################################

  def update(self):
      self.updateAccounts()
      self.updateTime()
      self.chartView.drawChart()
      for ii in self.indicators:
        apply(ii[0], ii[1:])

  #############################################################################
  ##  Mulit-Chart View and Symbol Loading
  #############################################################################

  def onNewTab(self):
    t = str(self.ui.symbolEntry.text())
    self.ui.symbolEntry.clear()
    c = ChartView(t)
    chartViews.append(c)
    self.ui.chartTabs.addTab(c, t)

  def onCloseTab(self, num):
    chartViews.pop(num-1)
    self.ui.chartTabs.removeTab(num)

  def onChangeTab(self, x):
    self.chartView = chartViews[self.ui.chartTabs.currentIndex()-1]
    self.chartView.drawChart()
    self.update()
    

  #############################################################################
  ##  Chart Controls
  ##  Zoom In/Out, Chart Style (ohlc, candlestick, etc), Normal/Log Scale, etc
  #############################################################################
  
  def onZoomChart(self, i):
    self.chartView.chartLength = i
    self.chartView.drawChart()
    self.update()

  def onChartStyleChange(self, i):
    choices = [self.chartView.drawCandlesticks, self.chartView.drawOHLC, 
               self.chartView.drawHLC, self.chartView.drawBar,
               self.chartView.drawDot, self.chartView.drawClose]
    self.chartView.chartStyle = choices[i]
    self.chartView.drawChart()
    self.update()


  #############################################################################
  ##  Current Day Display
  ##  Date, Open, High, Low, Close
  #############################################################################

  def updateCurrentDayDisplay(self):
    todayData = self.chartView.data.currentDay(time.currentDay)
    self.ui.currentDayDate.setText(todayData[0])
    self.ui.currentDayOpen.setText(str(todayData[1]))
    self.ui.currentDayHigh.setText(str(todayData[2]))
    self.ui.currentDayLow.setText(str(todayData[3]))
    self.ui.currentDayClose.setText(str(todayData[4]))
    self.ui.currentDayVolume.setText(str(todayData[5]))


  #############################################################################
  ##  Time Controls
  ##  Next/Prev Day
  #############################################################################

  def updateTime(self):
    self.updateCurrentDayDisplay()
    self.ui.daysLeft.display(time.currentDay)

  def onNextDay(self):
    if time.currentDay > 0:
      time.currentDay -= 1
      self.chartView.drawChart()
      self.update()

  def onPrevDay(self):
    time.currentDay += 1
    self.chartView.drawChart()
    self.update()
    
  def onNext30(self):
    for ii in range(30):
      if time.currentDay > 0:
        time.currentDay -=1
        self.update()
    self.chartView.drawChart()
    self.update()

  def onPrev30(self):
    for ii in range(30):
      time.currentDay +=1
      self.update()
    self.chartView.drawChart()
    self.update()


  #############################################################################
  ##  Account Controls
  ##  Buy/Sell, Stop/Limit, % Gain/Loss of last trade, % Gain/Loss Total, etc.
  #############################################################################

  def updateAccounts(self):
    account.update()
    self.ui.showBalance.setText(str(account.balance))
    self.ui.showPortfolio.setText(str(account.portfolio))
    self.ui.showPortfolioValue.setText(str(account.portfolioValue()))
    p = account.portfolioProfit()
    pp = account.portfolioPercentage()
    c = "green" if p >= 0 else "red"
    self.ui.showProfit.setText(str(p))
    self.ui.showProfitPercent.setText(str(pp)+"%")
    self.ui.showProfit.setStyleSheet("QLabel { color : " + c + ";}")
    self.ui.showProfitPercent.setStyleSheet("QLabel { color : " + c + ";}")

  def onBuy(self):
    account.buy(self.chartView.symbol, self.ui.buyShares.text())
    self.ui.buyShares.clear()
    # TODO: Add code in to view pending orders, this should be cleared
    #self.ui.buyStop.clear() 
    self.update()
  
  def onSell(self):
    if self.ui.stopLoss.text():
      account.setStop(self.chartView.symbol, float(self.ui.stopLoss.text()), self.ui.sellShares.text())
    else:
      account.sell(self.chartView.symbol, self.ui.sellShares.text())
    self.ui.sellShares.clear()
    # TODO: Add code in to view pending orders, this should be cleared
    #self.ui.sellStop.clear() 
    self.update()


  #############################################################################
  ##  Technical Indicators
  ##  Moving Averages, Bollinger Bands, RSI, Volume, etc
  ##  TODO:
  ##    Add "your stop loss" indicator that plots the stop loss price
  #############################################################################
  def drawSMA(self, days, color="red"):
    self.chartView.drawLine(self.chartView.data.sma(days, time.currentDay, self.chartView.chartLength), color)

  def drawWMA(self, days, color="red"):
    self.chartView.drawLine(self.chartView.data.wma(days, time.currentDay, self.chartView.chartLength), color)

  def drawEMA(self, days, color="red"):
    self.chartView.drawLine(self.chartView.data.ema(days, time.currentDay, self.chartView.chartLength), color)
  
  def drawBollingerBands(self, days, color1="green", color2="blue", color3="red"):
    d = self.chartView.data.bollingerBands(days, time.currentDay, self.chartView.chartLength)
    self.chartView.drawLine(d[0], color1)
    self.chartView.drawLine(d[1], color2)
    self.chartView.drawLine(d[2], color3)
   
  def drawDonchianChannel(self, days, color1="green", color2="red"):
    d = self.chartView.data.donchianChannel(days, time.currentDay, self.chartView.chartLength)
    self.chartView.drawLine(d[0], color1)
    self.chartView.drawLine(d[1], color2)

  def onAddIndicator(self):
    i = self.ui.newIndicator.currentIndex()
    #self.indicators += (i, options)
    l = len(self.indicators)
    if i == 0:
      self.addSinglePeriod(l, self.drawSMA, "Simple Moving Average")
    elif i == 1:
      self.addSinglePeriod(l, self.drawWMA, "Weighted Moving Average")
    elif i == 2:
      self.addSinglePeriod(l, self.drawEMA, "Exponential Moving Average")
    elif i == 3:
      self.addSinglePeriodThreeLines(l, self.drawBollingerBands, "Bollinger Bands")
    elif i == 4:
      self.addSinglePeriodTwoLines(l, self.drawDonchianChannel, "Donchian Channel")
    self.update()


  def addSinglePeriod(self, i, command, label):
    #self.indicators.append((self.chartView.drawSMA
    indicator = IndicatorSinglePeriod(self, i, command)
    self.indicators.append((command, indicator.period.value(), indicator.color.currentText()))
    self.ui.indicators.addItem(indicator, label)
    self.ui.indicators.setCurrentIndex(i+1)
    
  def addSinglePeriodTwoLines(self, i, command, label):
    indicator = IndicatorSinglePeriodTwoLines(self, i, command)
    self.indicators.append((command, indicator.period.value(), indicator.color.currentText(), indicator.color2.currentText()))
    self.ui.indicators.addItem(indicator, label)
    self.ui.indicators.setCurrentIndex(i+1)

  def addSinglePeriodThreeLines(self, i, command, label):
    indicator = IndicatorSinglePeriodThreeLines(self, i, command)
    self.indicators.append((command, indicator.period.value(), indicator.color.currentText(), indicator.color2.currentText(), indicator.color3.currentText()))
    self.ui.indicators.addItem(indicator, label)
    self.ui.indicators.setCurrentIndex(i+1)



## TODO:  Make a indicator-creator that will auto-generate this code
## A single period, three line display (like bollinger bands) will display as...
## Top Line:                   color |green|
## Middle Line:  period |10|   color |blue |
## Bottom Line:                color |red  |
## |           Remove Indicator            |

#((line, "Top Band", False),
 #(line, "SMA", spinbox),
 #(line, "Bottom Band", False)
 #(parameter, "Standard Deviation", spinbox))

class IndicatorSinglePeriod(QtGui.QWidget):
  def __init__(self, main, i, command):
    self.main = main
    self.i = i
    self.command = command
    
    QtGui.QWidget.__init__(self)
    self.setGeometry(QtCore.QRect(0, 0, 194, 598))
    self.setObjectName("FirstPage")
    
    self.verticalLayout = QtGui.QVBoxLayout(self)
    self.verticalLayout.setObjectName("verticalLayout")
    
    ## periodLayout
    self.periodLayout = QtGui.QHBoxLayout()
    self.periodLayout.setObjectName("periodLayout")
    
    self.periodLabel = QtGui.QLabel(self)
    self.periodLabel.setObjectName("period_label")
    self.periodLabel.setText("Period:")
    self.periodLayout.addWidget(self.periodLabel)
    
    self.period = QtGui.QSpinBox(self)
    self.period.setMinimum(1)
    self.period.setMaximum(99)
    self.period.setProperty("value", 10)
    self.period.setObjectName("period")
    self.periodLayout.addWidget(self.period)
    
    ## colorLayout
    self.colorLayout = QtGui.QHBoxLayout()
    self.colorLayout.setObjectName("colorLayout")
    
    self.colorLabel = QtGui.QLabel(self)
    self.colorLabel.setObjectName("colorLabel")
    self.colorLabel.setText("Color:")
    self.colorLayout.addWidget(self.colorLabel)
    
    self.color = QtGui.QComboBox(self)
    self.color.setObjectName("color")
    self.color.addItem("red")
    self.color.addItem("green")
    self.color.addItem("blue")
    self.color.addItem("orange")
    self.color.addItem("yellow")
    self.color.addItem("gold")
    self.color.addItem("silver")
    self.colorLayout.addWidget(self.color)
    
    self.removeButton = QtGui.QPushButton(self)
    self.removeButton.setObjectName("removeButton")
    self.removeButton.setText("Remove Indicator")
    
    self.spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    
    self.connect(self.removeButton, QtCore.SIGNAL("clicked()"), self.remove)
    self.connect(self.period, QtCore.SIGNAL("valueChanged(int)"), self.update)
    self.connect(self.color, QtCore.SIGNAL("currentIndexChanged(int)"), self.update)

    self.verticalLayout.addLayout(self.periodLayout)
    self.verticalLayout.addLayout(self.colorLayout)
    self.verticalLayout.addWidget(self.removeButton)
    self.verticalLayout.addItem(self.spacerItem)
    
    
  def update(self):
    index = self.main.ui.indicators.currentIndex() - 1
    self.main.indicators[index] = (self.command, self.period.value(), self.color.currentText())
    self.main.update()
    
  def remove(self):
    index = self.main.ui.indicators.currentIndex()
    self.main.indicators.pop(index-1)
    self.main.ui.indicators.removeItem(index)
    self.main.update()



class IndicatorSinglePeriodTwoLines(QtGui.QWidget):
  def __init__(self, main, i, command):
    self.main = main
    self.i = i
    self.command = command
    
    QtGui.QWidget.__init__(self)
    self.setGeometry(QtCore.QRect(0, 0, 194, 598))
    self.setObjectName("FirstPage")
    
    self.verticalLayout = QtGui.QVBoxLayout(self)
    self.verticalLayout.setObjectName("verticalLayout")
    
    ## periodLayout
    self.periodLayout = QtGui.QHBoxLayout()
    self.periodLayout.setObjectName("periodLayout")
    
    self.periodLabel = QtGui.QLabel(self)
    self.periodLabel.setObjectName("period_label")
    self.periodLabel.setText("Period:")
    self.periodLayout.addWidget(self.periodLabel)
    
    self.period = QtGui.QSpinBox(self)
    self.period.setMinimum(1)
    self.period.setMaximum(99)
    self.period.setProperty("value", 10)
    self.period.setObjectName("period")
    self.periodLayout.addWidget(self.period)
    
    ## colorLayout
    self.colorLayout = QtGui.QHBoxLayout()
    self.colorLayout.setObjectName("colorLayout")
    
    self.colorLabel = QtGui.QLabel(self)
    self.colorLabel.setObjectName("colorLabel")
    self.colorLabel.setText("Color:")
    self.colorLayout.addWidget(self.colorLabel)
    
    self.color = QtGui.QComboBox(self)
    self.color.setObjectName("color")
    self.color.addItem("red")
    self.color.addItem("green")
    self.color.addItem("blue")
    self.color.addItem("orange")
    self.color.addItem("yellow")
    self.color.addItem("gold")
    self.color.addItem("silver")
    self.colorLayout.addWidget(self.color)
    
    ## colorLayout
    self.color2Layout = QtGui.QHBoxLayout()
    self.color2Layout.setObjectName("colorLayout")
    
    self.color2Label = QtGui.QLabel(self)
    self.color2Label.setObjectName("colorLabel")
    self.color2Label.setText("Color:")
    self.color2Layout.addWidget(self.color2Label)
    
    self.color2 = QtGui.QComboBox(self)
    self.color2.setObjectName("color2")
    self.color2.addItem("red")
    self.color2.addItem("green")
    self.color2.addItem("blue")
    self.color2.addItem("orange")
    self.color2.addItem("yellow")
    self.color2.addItem("gold")
    self.color2.addItem("silver")
    self.color2.setCurrentIndex(1)
    self.color2Layout.addWidget(self.color2)


    self.removeButton = QtGui.QPushButton(self)
    self.removeButton.setObjectName("removeButton")
    self.removeButton.setText("Remove Indicator")
    
    self.spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    
    self.connect(self.removeButton, QtCore.SIGNAL("clicked()"), self.remove)
    self.connect(self.period, QtCore.SIGNAL("valueChanged(int)"), self.update)
    self.connect(self.color, QtCore.SIGNAL("currentIndexChanged(int)"), self.update)
    self.connect(self.color2, QtCore.SIGNAL("currentIndexChanged(int)"), self.update)

    self.verticalLayout.addLayout(self.periodLayout)
    self.verticalLayout.addLayout(self.colorLayout)
    self.verticalLayout.addLayout(self.color2Layout)
    self.verticalLayout.addWidget(self.removeButton)
    self.verticalLayout.addItem(self.spacerItem)
    
    
  def update(self):
    index = self.main.ui.indicators.currentIndex() - 1
    self.main.indicators[index] = (self.command, self.period.value(), self.color.currentText(), self.color2.currentText())
    self.main.update()
    
  def remove(self):
    index = self.main.ui.indicators.currentIndex()
    self.main.indicators.pop(index-1)
    self.main.ui.indicators.removeItem(index)
    self.main.update()



class IndicatorSinglePeriodThreeLines(QtGui.QWidget):
  def __init__(self, main, i, command):
    self.main = main
    self.i = i
    self.command = command
    
    QtGui.QWidget.__init__(self)
    self.setGeometry(QtCore.QRect(0, 0, 194, 598))
    self.setObjectName("FirstPage")
    
    self.verticalLayout = QtGui.QVBoxLayout(self)
    self.verticalLayout.setObjectName("verticalLayout")
    
    ## periodLayout
    self.periodLayout = QtGui.QHBoxLayout()
    self.periodLayout.setObjectName("periodLayout")
    
    self.periodLabel = QtGui.QLabel(self)
    self.periodLabel.setObjectName("period_label")
    self.periodLabel.setText("Period:")
    self.periodLayout.addWidget(self.periodLabel)
    
    self.period = QtGui.QSpinBox(self)
    self.period.setMinimum(1)
    self.period.setMaximum(99)
    self.period.setProperty("value", 10)
    self.period.setObjectName("period")
    self.periodLayout.addWidget(self.period)
    
    ## colorLayout
    self.colorLayout = QtGui.QHBoxLayout()
    self.colorLayout.setObjectName("colorLayout")
    
    self.colorLabel = QtGui.QLabel(self)
    self.colorLabel.setObjectName("colorLabel")
    self.colorLabel.setText("Color:")
    self.colorLayout.addWidget(self.colorLabel)
    
    self.color = QtGui.QComboBox(self)
    self.color.setObjectName("color")
    self.color.addItem("red")
    self.color.addItem("green")
    self.color.addItem("blue")
    self.color.addItem("orange")
    self.color.addItem("yellow")
    self.color.addItem("gold")
    self.color.addItem("silver")
    self.colorLayout.addWidget(self.color)
    
    ## colorLayout
    self.color2Layout = QtGui.QHBoxLayout()
    self.color2Layout.setObjectName("colorLayout")
    
    self.color2Label = QtGui.QLabel(self)
    self.color2Label.setObjectName("colorLabel")
    self.color2Label.setText("Color:")
    self.color2Layout.addWidget(self.color2Label)
    
    self.color2 = QtGui.QComboBox(self)
    self.color2.setObjectName("color2")
    self.color2.addItem("red")
    self.color2.addItem("green")
    self.color2.addItem("blue")
    self.color2.addItem("orange")
    self.color2.addItem("yellow")
    self.color2.addItem("gold")
    self.color2.addItem("silver")
    self.color2.setCurrentIndex(1)
    self.color2Layout.addWidget(self.color2)

    ## colorLayout
    self.color3Layout = QtGui.QHBoxLayout()
    self.color3Layout.setObjectName("colorLayout")
    
    self.color3Label = QtGui.QLabel(self)
    self.color3Label.setObjectName("colorLabel")
    self.color3Label.setText("Color:")
    self.color3Layout.addWidget(self.color3Label)
    
    self.color3 = QtGui.QComboBox(self)
    self.color3.setObjectName("color3")
    self.color3.addItem("red")
    self.color3.addItem("green")
    self.color3.addItem("blue")
    self.color3.addItem("orange")
    self.color3.addItem("yellow")
    self.color3.addItem("gold")
    self.color3.addItem("silver")
    self.color3.setCurrentIndex(2)
    self.color3Layout.addWidget(self.color3)


    self.removeButton = QtGui.QPushButton(self)
    self.removeButton.setObjectName("removeButton")
    self.removeButton.setText("Remove Indicator")
    
    self.spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
    
    self.connect(self.removeButton, QtCore.SIGNAL("clicked()"), self.remove)
    self.connect(self.period, QtCore.SIGNAL("valueChanged(int)"), self.update)
    self.connect(self.color, QtCore.SIGNAL("currentIndexChanged(int)"), self.update)
    self.connect(self.color2, QtCore.SIGNAL("currentIndexChanged(int)"), self.update)
    self.connect(self.color3, QtCore.SIGNAL("currentIndexChanged(int)"), self.update)

    self.verticalLayout.addLayout(self.periodLayout)
    self.verticalLayout.addLayout(self.colorLayout)
    self.verticalLayout.addLayout(self.color2Layout)
    self.verticalLayout.addLayout(self.color3Layout)
    self.verticalLayout.addWidget(self.removeButton)
    self.verticalLayout.addItem(self.spacerItem)
    
    
  def update(self):
    index = self.main.ui.indicators.currentIndex() - 1
    self.main.indicators[index] = (self.command, self.period.value(), self.color.currentText(), self.color2.currentText(), self.color3.currentText())
    self.main.update()
    
  def remove(self):
    index = self.main.ui.indicators.currentIndex()
    self.main.indicators.pop(index-1)
    self.main.ui.indicators.removeItem(index)
    self.main.update()





if __name__ == "__main__":
  time = Time()
  account = Account()
  screen = Screen()
  chartViews = []

  app = QtGui.QApplication(sys.argv)
  window=Main()
  window.show()

  sys.exit(app.exec_())
