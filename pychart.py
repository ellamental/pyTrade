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
## Chart gets screwed up when it is zoomed out too far.
## Make time controls into a seperate widget
## Allow screen resizing that also resizes the chart
## Add bottom bar for showing volume and other indicators
###############################################################################


import os,sys,time

from PyQt4 import QtCore, QtGui
from urllib import urlopen

## import QtDesigner UI module
from ui_chart import Ui_chartWidget


###############################################################################
##  Account
##  Buy/Sell, Stop/Limit, Account Balance, Percentage Gain/Loss, etc.
###############################################################################

class Account():
  def __init__(self):
    self.balance = 10000
    self.shares = 0
    
  def buy(self, price):
    self.shares = self.balance // price
    self.balance -= self.shares * price

  def sell(self, price):
    self.balance += self.shares * price
    self.shares = 0



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

  def adjustPrices(self, day, length=False):
    if length: 
      d = self.chartData(day, length)
      mini, maxi = min([ii[3] for ii in d]), max([ii[4] for ii in d])
      self.low, self.high = mini, maxi
      mul = screenHeight/(maxi-mini)
      return [[ii[0], (ii[1]-mini)*mul, (ii[2]-mini)*mul, (ii[3]-mini)*mul, (ii[4]-mini)*mul, ii[5]] for ii in d]
    else:
      d = day
      mini, maxi = min(d), max(d)
      mul = screenHeight/(maxi-mini)
      return [(ii-mini)*mul for ii in d]
    
  def currentDay(self, day):
    return self.data[day]

  def chartData(self, day, length):
    return self.data[day:length+day]

  def loadSymbol(self, symbol):
    self.data = self.googDownload(symbol)

  def sma(self, period, day, length):
    d = self.data[day:day+length+period]
    a = [sum([ii[4] for ii in d[c:c+period]])/period for c in range(length)]
    mul = screenHeight/(self.high-self.low)
    return [(ii-self.low)*mul for ii in a]


account = Account()
screenWidth = 1024
screenHeight = 860



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



class Main(QtGui.QWidget):
  def __init__(self):
    QtGui.QWidget.__init__(self)

    # This is always the same
    self.ui = Ui_chartWidget()
    self.ui.setupUi(self)

    ## Create a new GraphicsScene and set GraphicsView (chart) to scene
    self.scene = Scene()
    self.ui.chart.setScene(self.scene)

    ## initialize data to be used with the chart
    self.data = Data("msft")
    self.currentDay = 1
    self.chartLength = 60
    ## TODO: Change following ugly hack to set the data.high + data.low variables
    self.data.adjustPrices(self.currentDay, self.chartLength)

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
    self.connect(self.ui.loadSymbol, QtCore.SIGNAL("clicked()"), self.onLoadSymbol)
    self.connect(self.ui.symbolEntry, QtCore.SIGNAL("returnPressed()"), self.onLoadSymbol)
    self.connect(self.ui.candlestick, QtCore.SIGNAL("clicked()"), self.onCandlestick)
    self.connect(self.ui.ohlc, QtCore.SIGNAL("clicked()"), self.onOHLC)

    ## Defaults
    self.chartStyle = self.drawCandlesticks
    self.drawChart()
    self.ui.chartLength.setText(str(self.chartLength))
    self.ui.showBalance.setText(str(account.balance))


  def drawOHLC(self, day, length):
    d = self.data.adjustPrices(day, length)
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod
    
    for ii, today in enumerate(d):
      b = self.scene.addRect(offset+offsetmod/4, screenHeight-today[2], 1, today[2]-today[3])
      self.scene.addRect(offset+offsetmod/4, screenHeight-today[4], offsetmod/4, 1)
      self.scene.addRect(offset+offsetmod/4, screenHeight-today[1], -(offsetmod/4), 1)
      
      p = self.data.data[day+ii]
      b.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod


  def drawCandlesticks(self, day, length):
    d = self.data.adjustPrices(day, length)
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod
    
    for ii, today in enumerate(d):
      if today[1] > today[4]:
        b = QtGui.QColor(50,50,50,250)
      else:
        b = QtGui.QColor(250,250,250,250)

      self.scene.addRect(offset+offsetmod/4, screenHeight-today[2], 1, today[2]-today[3], brush=b)
      b = self.scene.addRect(offset, screenHeight-today[1], offsetmod/2, today[1]-today[4], brush=b)
      
      p = self.data.data[day+ii]
      b.setToolTip(" ".join(["Date:", p[0], "Open:", str(p[1]), "High:", str(p[2]), "Low:", str(p[3]), "Close", str(p[4]), "Volume:", str(p[5])]))  # We can use this to display price data
      offset -= offsetmod

  def drawLine(self, d):
    """Used for moving averages, bollinger bands, etc"""
    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod-offsetmod
    for ii in range(len(d))[1:]:
      self.scene.addLine(offset+offsetmod/4, screenHeight-d[ii], offset+offsetmod/4+offsetmod, screenHeight-(d[ii-1]))
      offset -= offsetmod

  def drawLines(self, day, length):
    if self.data.high == 0:
      self.data.high, self.data.low = 28, 25
    high = self.data.high
    low = self.data.low
    
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
      # BUG: For some reason adding these two lines breaks drawing trendlines
      #t = self.scene.addText(str(lineList[ii]))
      #t.setPos(screenWidth-30, screenHeight-price)
    

  def drawChart(self):
    self.scene.clear()
    self.scene.update()
    self.drawLines(self.currentDay, self.chartLength)
    self.chartStyle(self.currentDay, self.chartLength)


###############################################################################
## Event Handlers
###############################################################################

###############################################################################
##  Chart Controls
##  Zoom In/Out, Chart Style (ohlc, candlestick, etc), Normal/Log Scale, etc
###############################################################################

  def onZoomIn(self):
    self.chartLength -= 10
    self.drawChart()
    self.ui.chartLength.setText(str(self.chartLength))
    
  def onZoomOut(self):
    self.chartLength += 10
    self.drawChart()
    self.ui.chartLength.setText(str(self.chartLength))

  def onCandlestick(self):
    self.chartStyle = self.drawCandlesticks
    self.drawChart()
    
  def onOHLC(self):
    self.chartStyle = self.drawOHLC
    self.drawChart()
    
    

###############################################################################
##  Time Controls
##  Next/Prev Day
###############################################################################

  def onNextDay(self):
    self.currentDay -= 1
    self.drawChart()

  def onPrevDay(self):
    self.currentDay += 1
    self.drawChart()
    
  def onNext30(self):
    self.currentDay -= 30
    self.drawChart()

  def onPrev30(self):
    self.currentDay += 30
    self.drawChart()


###############################################################################
##  Account Controls
##  Buy/Sell, Stop/Limit, % Gain/Loss of last trade, % Gain/Loss Total, etc.
###############################################################################

  def onBuy(self):
    account.buy(self.data.currentDay(self.currentDay)[4])
    self.ui.showBalance.setText(str(account.balance))
  
  def onSell(self):
    account.sell(self.data.currentDay(self.currentDay)[4])
    self.ui.showBalance.setText(str(account.balance))


###############################################################################
##  Technical Indicators
##  Moving Averages, Bollinger Bands, RSI, Volume, etc
###############################################################################

  def onSMA(self):
    self.drawLine(self.data.sma(15, self.currentDay, self.chartLength))


###############################################################################
##  Watchlist Controls
##  Load Symbol, Add Symbol
###############################################################################

  
  def onLoadSymbol(self):
    self.data = Data(str(self.ui.symbolEntry.text()))
    self.ui.symbolEntry.clear()
    self.drawChart()
    



if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  window=Main()
  window.show()

  sys.exit(app.exec_())
