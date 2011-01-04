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
## - Check for end of data when changing days
## - Prev and Next buttons that don't advance days, just let you view chart.
## 
## Chart
## - Allow screen resizing that also resizes the chart
## - Add bottom bar for showing volume and other indicators
## - Add compare, see: http://bigcharts.marketwatch.com/advchart/frames/frames.asp?symb=&time=&freq=
## - Add point and figure chart view
## - Add support for symbol lookup
## 
## Accounts
## - Alert user that they have pending orders.
## - Allow user to specify when their order should go through, today's close 
##   or tomorrow's open or other.
## - Add purchase price to portfolio.  Also if stock is already held, make 
##   purchase price average of the two purchases.  Ex: if I own 100 shares of 
##   msft @ 50 and buy 100 more @ 60, the portfolio should say 200 shares @ 55
##
## Bugs
## - Try:  INDEXDJX:.DJI
##   
###############################################################################

from __future__ import division
import os,sys,time

from PyQt4 import QtCore, QtGui
from urllib import urlopen

## import QtDesigner UI module
from ui_chart import Ui_chartWidget

import numpy


###############################################################################
##  Account
##  Buy/Sell, Stop/Limit, Account Balance, Percentage Gain/Loss, etc.
###############################################################################

class Account():
  def __init__(self):
    self.balance = 10000
    self.shares = 0
    self.portfolio = {}
    self.pendingBuys = {}
    self.pendingSales = {}

  def getPrice(self, symbol, ohlc=1):
    d = [ii.data for ii in chartViews if ii.symbol == symbol]
    if d: 
      return d[0].data[time.currentDay][ohlc]
    else:
      d = Data(symbol)
      return d.currentDay(time.currentDay)[ohlc].data[time.currentDay][1]

  def buy(self, symbol, shares, stop):
    if stop: stop = float(stop)
    self.pendingBuys[symbol] = (shares, stop)
  
  def sell(self, symbol, shares, stop):
    if stop: stop = float(stop)
    self.pendingSales[symbol] = (shares, stop)

  def buyShares(self, symbol, shares):
    price = self.getPrice(symbol, 4)
    maxshares = int(self.balance / price)
    if not shares: shares = maxshares
    elif int(shares) > maxshares: shares = maxshares
    else: shares = int(shares)
    self.balance -= shares*price
    self.portfolio[symbol] = self.portfolio.get(symbol, 0) + shares
    del self.pendingBuys[symbol]

  def sellShares(self, symbol, shares):
    price = self.getPrice(symbol, 4)
    if not shares: shares = self.portfolio[symbol]
    elif int(shares) > self.portfolio[symbol]: shares = self.portfolio[symbol]
    else: shares = int(shares)
    self.portfolio[symbol] -= shares
    self.balance += shares * price
    del self.pendingSales[symbol]
  
  def update(self):
    for key, value in self.pendingSales.items():
      p = self.getPrice(key, 3)
      if p < value[1] or not value[1]:
        self.sellShares(key, value[0])
    for key, value in self.pendingBuys.items():
      p = self.getPrice(key, 2)
      if p > value[1] or not value[1]:
        self.buyShares(key, value[0])

  def portfolioValue(self):
    v = self.balance
    for key, item in self.portfolio.items():
      v += item * self.getPrice(key, 4)
    return v




###############################################################################
##  Data
##  Download and Access Data, Adjust Prices for Charting, Technical Indicator 
##  Calculation
##  TODO:
##    Rename some of the methods to make more clear
###############################################################################

class Data():
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
    mul = screenHeight/(hi-lo)
    return [[ii[0], (ii[1]-lo)*mul, (ii[2]-lo)*mul, (ii[3]-lo)*mul, (ii[4]-lo)*mul, ii[5]] for ii in d]

  def adjustPrices(self, prices):
    mul = screenHeight/(self.high-self.low)
    return [(price-self.low)*mul for price in prices]

  def currentDay(self, day):
    return self.data[day]

  def chartData(self, day, length):
    return self.data[day:length+day]

  def loadSymbol(self, symbol):
    self.data = self.googDownload(symbol)

  def adjustDataList(self, d):
    mul = screenHeight / (self.high - self.low)
    return [(ii-self.low)*mul for ii in d]

  def forEachPeriod(self, fun, period, day, length, ohlc=4):
    d = self.data[day:day+length+period]
    return [fun([ii for ii in d[c:c+period]]) for c in range(length)]

  def sma(self, period, day, length):
    return self.forEachPeriod(lambda x: sum([ii[4] for ii in x])/period, period, day, length)
  
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

class Time():
  def __init__(self):
    self.currentDay = 1






###############################################################################
##  Charting
##  Draw candlesticks, ohlc, horizontal lines, moving average type lines
##  TODO:
##    Make into a chart widget instead of main window
##    Add tabbed charts to allow having > 1 chart open
###############################################################################

class Scene(QtGui.QGraphicsScene):
  def __init__(self):
    QtGui.QGraphicsScene.__init__(self)
    
    self.setSceneRect(0, 0, screenWidth, screenHeight)
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
  def __init__(self, scene, symbol):
    QtGui.QGraphicsView.__init__(self)
    
    self.symbol = symbol
    self.scene = scene
    self.setScene(self.scene)
    self.data = Data(symbol)
    self.chartLength = 60
    
    self.chartStyle = self.drawCandlesticks
    self.data.setHighLow(time.currentDay, self.chartLength)
    self.drawChart()
    
  def drawOHLC(self, day, length):
    d = self.data.adjustData(day, length)
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod
    
    for ii, today in enumerate(d):
      b = self.scene.addRect(offset+offsetmod/4, screenHeight-today[2], 1, today[2]-today[3])
      self.scene.addRect(offset+offsetmod/4, screenHeight-today[4], offsetmod/4, 1)
      self.scene.addRect(offset+offsetmod/4, screenHeight-today[1], -(offsetmod/4), 1)
      
      p = self.data.data[day+ii]
      b.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod

  def drawHLC(self, day, length):
    d = self.data.adjustData(day, length)
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod
    
    for ii, today in enumerate(d):
      b = self.scene.addRect(offset+offsetmod/4, screenHeight-today[2], 1, today[2]-today[3])
      self.scene.addRect(offset+offsetmod/4, screenHeight-today[4], offsetmod/4, 1)
      
      p = self.data.data[day+ii]
      b.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod

  def drawBar(self, day, length):
    d = self.data.adjustData(day, length)
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod
    b = QtGui.QColor(50,50,50,250)
    
    for ii, today in enumerate(d):
      body = self.scene.addRect(offset+offsetmod, screenHeight-today[2], offsetmod/2, screenHeight+100, brush=b)
      
      p = self.data.data[day+ii]
      body.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod

  def drawDot(self, day, length):
    d = self.data.adjustData(day, length)
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod
    b = QtGui.QColor(50,50,50,250)
    
    for ii, today in enumerate(d):
      body = self.scene.addRect(offset+offsetmod/4, screenHeight-today[4], 2, 2, brush=b)
      
      p = self.data.data[day+ii]
      body.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod

  def drawClose(self, day, length):
    d = self.data.adjustData(day, length)
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod
    b = QtGui.QColor(50,50,50,250)
    
    for ii, today in enumerate(d):
      body = self.scene.addRect(offset+offsetmod/4, screenHeight-today[4], 2, 2, brush=b)
      
      p = self.data.data[day+ii]
      body.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod

  def drawClose(self, day, length):
    d = self.data.chartData(day, length)
    self.drawLine([ii[4] for ii in d])

  def drawCandlesticks(self, day, length):
    d = self.data.adjustData(day, length)
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod

    for ii, today in enumerate(d):
      if today[1] > today[4]:
        b = QtGui.QColor("black")
      else:
        b = QtGui.QColor("white")

      self.scene.addRect(offset+offsetmod/4, screenHeight-today[2], 1, today[2]-today[3], brush=b)
      b = self.scene.addRect(offset, screenHeight-today[1], offsetmod/2, today[1]-today[4], brush=b)
      
      p = self.data.data[day+ii]
      b.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod

  def drawLine(self, d, color="black"):
    """Used for moving averages, bollinger bands, etc"""
    p = QtGui.QPen(QtGui.QColor(color), 2, QtCore.Qt.SolidLine)
    d = self.data.adjustDataList(d)
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod-offsetmod
    for ii in range(len(d))[1:]:
      self.scene.addLine(offset+offsetmod/4, screenHeight-d[ii], offset+offsetmod/4+offsetmod, screenHeight-(d[ii-1]), p)
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
      self.scene.addLine(0, screenHeight-price, screenWidth, screenHeight-price)
      # BUG: If scene.addText() is used drawing trendlines breaks, this is reproducable in a minimal example
      t = self.scene.addSimpleText(str(lineList[ii]))
      t.setPos(screenWidth-30, screenHeight-price)
    

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

    ## Create a new GraphicsScene and set GraphicsView (chart) to scene
    chartViews.append(ChartView(Scene(), "msft"))
    self.chartView = chartViews[0]
    self.ui.chart.setScene(self.chartView.scene)

    ## Maximize screen 
    #self.setWindowState(QtCore.Qt.WindowMaximized)
    
    ## Connect buttons
    self.connect(self.ui.zoomIn, QtCore.SIGNAL("clicked()"), self.onZoomIn)
    self.connect(self.ui.zoomOut, QtCore.SIGNAL("clicked()"), self.onZoomOut)
    self.connect(self.ui.nextDay, QtCore.SIGNAL("clicked()"), self.onNextDay)
    self.connect(self.ui.prevDay, QtCore.SIGNAL("clicked()"), self.onPrevDay)
    self.connect(self.ui.next30, QtCore.SIGNAL("clicked()"), self.onNext30)
    self.connect(self.ui.prev30, QtCore.SIGNAL("clicked()"), self.onPrev30)
    self.connect(self.ui.buy, QtCore.SIGNAL("clicked()"), self.onBuy)
    self.connect(self.ui.sell, QtCore.SIGNAL("clicked()"), self.onSell)
    
    self.connect(self.ui.sma, QtCore.SIGNAL("clicked()"), self.onSMA)
    self.connect(self.ui.macd, QtCore.SIGNAL("clicked()"), self.onMACD)
    self.connect(self.ui.bollingerBands, QtCore.SIGNAL("clicked()"), self.onBollingerBands)
    self.connect(self.ui.donchianChannel, QtCore.SIGNAL("clicked()"), self.onDonchianChannel)

    self.connect(self.ui.loadSymbol, QtCore.SIGNAL("clicked()"), self.onLoadSymbol)
    self.connect(self.ui.symbolEntry, QtCore.SIGNAL("returnPressed()"), self.onNewTab)
    
    self.connect(self.ui.candlestick, QtCore.SIGNAL("clicked()"), self.onCandlestick)
    self.connect(self.ui.ohlc, QtCore.SIGNAL("clicked()"), self.onOHLC)
    self.connect(self.ui.hlc, QtCore.SIGNAL("clicked()"), self.onHLC)
    self.connect(self.ui.bar, QtCore.SIGNAL("clicked()"), self.onBar)
    self.connect(self.ui.dot, QtCore.SIGNAL("clicked()"), self.onDot)
    self.connect(self.ui.close, QtCore.SIGNAL("clicked()"), self.onClose)

    self.connect(self.ui.newTab, QtCore.SIGNAL("clicked()"), self.onNewTab)
    self.connect(self.ui.chartTabs, QtCore.SIGNAL("currentChanged(QWidget *)"), self.onChangeTab)
    self.connect(self.ui.chartTabs, QtCore.SIGNAL("tabCloseRequested(int)"), self.onCloseTab)
    
    self.ui.chartTabs.setTabsClosable(True)

    ## Defaults
    self.update()
    
    



###############################################################################
## Event Handlers
###############################################################################

  def update(self):
      self.updateAccounts()
      self.updateTime()
      self.updateChartControls()

###############################################################################
##  Mulit-Chart View and Symbol Loading
###############################################################################

  def onNewTab(self):
    t = str(self.ui.symbolEntry.text())
    self.ui.symbolEntry.clear()
    c = ChartView(Scene(), t)
    chartViews.append(c)
    self.ui.chartTabs.addTab(c, t)

  def onCloseTab(self, num):
    chartViews.pop(num)
    self.ui.chartTabs.removeTab(num)

  def onChangeTab(self, x):
    self.chartView = chartViews[self.ui.chartTabs.currentIndex()]
    self.chartView.drawChart()
    self.update()
    
  def onLoadSymbol(self):
    self.chartView.data = Data(str(self.ui.symbolEntry.text()))
    self.ui.symbolEntry.clear()
    self.chartView.drawChart()
 

###############################################################################
##  Chart Controls
##  Zoom In/Out, Chart Style (ohlc, candlestick, etc), Normal/Log Scale, etc
###############################################################################
  
  def updateChartControls(self):
      self.ui.chartLength.setText(str(self.chartView.chartLength))

  def onZoomIn(self):
    self.chartView.chartLength -= 10
    self.chartView.drawChart()
    self.update()
    
  def onZoomOut(self):
    self.chartView.chartLength += 10
    self.chartView.drawChart()
    self.update()

  def onCandlestick(self):
    self.chartView.chartStyle = self.chartView.drawCandlesticks
    self.chartView.drawChart()
    
  def onOHLC(self):
    self.chartView.chartStyle = self.chartView.drawOHLC
    self.chartView.drawChart()
    
  def onHLC(self):
    self.chartView.chartStyle = self.chartView.drawHLC
    self.chartView.drawChart()

  def onBar(self):
    self.chartView.chartStyle = self.chartView.drawBar
    self.chartView.drawChart()

  def onDot(self):
    self.chartView.chartStyle = self.chartView.drawDot
    self.chartView.drawChart()

  def onClose(self):
    self.chartView.chartStyle = self.chartView.drawClose
    self.chartView.drawChart()


###############################################################################
##  Current Day Display
##  Date, Open, High, Low, Close
###############################################################################

  def updateCurrentDayDisplay(self):
    todayData = self.chartView.data.currentDay(time.currentDay)
    self.ui.currentDayDate.setText(todayData[0])
    self.ui.currentDayOpen.setText(str(todayData[1]))
    self.ui.currentDayHigh.setText(str(todayData[2]))
    self.ui.currentDayLow.setText(str(todayData[3]))
    self.ui.currentDayClose.setText(str(todayData[4]))
    self.ui.currentDayVolume.setText(str(todayData[5]))


###############################################################################
##  Time Controls
##  Next/Prev Day
###############################################################################

  def updateTime(self):
    self.updateCurrentDayDisplay()
    self.ui.daysLeft.display(time.currentDay)

  def onNextDay(self):
    time.currentDay -= 1
    self.chartView.drawChart()
    self.update()

  def onPrevDay(self):
    time.currentDay += 1
    self.chartView.drawChart()
    self.update()
    
  def onNext30(self):
    for ii in range(30):
      time.currentDay -=1
      self.update()
    self.chartView.drawChart()

  def onPrev30(self):
    for ii in range(30):
      time.currentDay +=1
      self.update()
    self.chartView.drawChart()


###############################################################################
##  Account Controls
##  Buy/Sell, Stop/Limit, % Gain/Loss of last trade, % Gain/Loss Total, etc.
###############################################################################

  def updateAccounts(self):
    account.update()
    self.ui.showBalance.setText(str(account.balance))
    self.ui.showPortfolio.setText(str(account.portfolio))
    self.ui.showPortfolioValue.setText(str(account.portfolioValue()))

  def onBuy(self):
    account.buy(self.chartView.symbol, self.ui.buyShares.text(), self.ui.buyStop.text())
    self.ui.buyShares.clear()
    # TODO: Add code in to view pending orders, this should be cleared
    #self.ui.buyStop.clear() 
    self.update()
  
  def onSell(self):
    account.sell(self.chartView.symbol, self.ui.sellShares.text(), self.ui.sellStop.text())
    self.ui.sellShares.clear()
    # TODO: Add code in to view pending orders, this should be cleared
    #self.ui.sellStop.clear() 
    self.update()


###############################################################################
##  Technical Indicators
##  Moving Averages, Bollinger Bands, RSI, Volume, etc
###############################################################################

  def onSMA(self):
    days = int(self.ui.shortPeriod.text())
    self.ui.shortPeriod.clear()
    self.chartView.drawLine(self.chartView.data.sma(days, time.currentDay, self.chartView.chartLength), "green")

  def onMACD(self):
    shortLength = int(self.ui.shortPeriod.text())
    longLength = int(self.ui.longPeriod.text())
    self.ui.shortPeriod.clear()
    self.ui.longPeriod.clear()
    self.chartView.drawLine(self.chartView.data.sma(shortLength, time.currentDay, self.chartView.chartLength), "red")
    self.chartView.drawLine(self.chartView.data.sma(longLength, time.currentDay, self.chartView.chartLength), "blue")

  def onBollingerBands(self):
    l = int(self.ui.shortPeriod.text())
    self.ui.shortPeriod.clear()
    d = self.chartView.data.bollingerBands(l, time.currentDay, self.chartView.chartLength)
    self.chartView.drawLine(d[0], "red")
    self.chartView.drawLine(d[1], "blue")
    self.chartView.drawLine(d[2], "green")
   
  def onDonchianChannel(self):
    p = int(self.ui.shortPeriod.text())
    self.ui.shortPeriod.clear()
    d = self.chartView.data.donchianChannel(p, time.currentDay, self.chartView.chartLength)
    self.chartView.drawLine(d[0], "red")
    self.chartView.drawLine(d[1], "green")


if __name__ == "__main__":
  time = Time()
  account = Account()
  chartViews = []
  screenWidth = 1024
  screenHeight = 800

  app = QtGui.QApplication(sys.argv)
  window=Main()
  window.show()

  sys.exit(app.exec_())
