# -*- coding: utf-8 -*-
#!/usr/bin/env python
###############################################################################
## pyChart
## 
## A charting/paper trading program written in Python and Qt
## 
## Currently this is only the chart widget, but more will follow
## 
## To produce a python module from QTDesigner:
##   pyuic4 -o ui_chart.py -x chartWidget.ui
##   
## TODO:
## Chart gets screwed up when it is zoomed out too far.
## Make time controls into a seperate widget
## Allow screen resizing that also resizes the chart
###############################################################################


import os,sys,time

from PyQt4 import QtCore, QtGui
from urllib import urlopen

## import QtDesigner UI module
from ui_chart import Ui_chartWidget



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
    

account = Account()
screenWidth = 1024
screenHeight = 860



# Create a class for our main window
class Main(QtGui.QWidget):
  def __init__(self):
    QtGui.QWidget.__init__(self)

    # This is always the same
    self.ui = Ui_chartWidget()
    self.ui.setupUi(self)

    ## Create a new Graphics Scene
    self.scene = QtGui.QGraphicsScene()
    self.scene.setSceneRect(0,0,screenWidth,screenHeight)
    ## New Trendline Variables
    self.scene.mouseMoveEvent = self.mouseMove
    self.scene.mousePressEvent = self.mousePress
    self.newLine = None
    self.newLineX = 0
    self.newLineY = 0
    
    ## Set the GraphicsView (chart) to view the GraphicsScene above
    self.ui.chart.setScene(self.scene)

    ## initialize data to be used with the chart
    self.data = Data("msft")
    self.currentDay = 1
    self.chartLength = 60

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

    ## Defaults
    self.drawChart()
    self.ui.chartLength.setText(str(self.chartLength))
    self.ui.showBalance.setText(str(account.balance))


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
      b.setToolTip(" ".join(["Date:", p[0], "\nOpen:", str(p[1]), 
                             "\nHigh:", str(p[2]), "\nLow:", str(p[3]), 
                             "\nClose", str(p[4]), "\nVolume:", str(p[5])]))  # We can use this to display price data
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
      t = self.scene.addText(str(lineList[ii]))
      t.setPos(screenWidth-30, screenHeight-price)
    

  def drawChart(self):
    self.drawLines(self.currentDay, self.chartLength)
    self.drawCandlesticks(self.currentDay, self.chartLength)
    #d = self.data.adjustPrices(self.currentDay, self.chartLength)
    #p = self.data.chartData(self.currentDay, self.chartLength)

    ## BUG:  Lines don't display correctly, neither the labels or line heights
    ##       are correct.  I'm leaving this implementation here because even 
    ##       incorrect lines still give a visual aid to the chart
    ## Draw Horizontal Lines
    #lineHeightRange = range(int(self.data.high) - int(self.data.low))
    #linePriceInts = [ii+int(self.data.low) for ii in lineHeightRange]
    #multiple = screenHeight / (self.data.high - self.data.low)
    #adj = [screenHeight-ii*multiple for ii in lineHeightRange]

  def onZoomIn(self):
    self.scene.clear()
    self.scene.update()
    self.chartLength -= 10
    self.drawChart()
    self.ui.chartLength.setText(str(self.chartLength))
    
  def onZoomOut(self):
    self.scene.clear()
    self.scene.update()
    self.chartLength += 10
    self.drawChart()
    self.ui.chartLength.setText(str(self.chartLength))

  def onNextDay(self):
    self.currentDay -= 1
    self.scene.clear()
    self.scene.update()
    self.drawChart()

  def onPrevDay(self):
    self.currentDay += 1
    self.scene.clear()
    self.scene.update()
    self.drawChart()
    
  def onNext30(self):
    self.currentDay -= 30
    self.scene.clear()
    self.scene.update()
    self.drawChart()

  def onPrev30(self):
    self.currentDay += 30
    self.scene.clear()
    self.scene.update()
    self.drawChart()

  def onBuy(self):
    account.buy(self.data.currentDay(self.currentDay)[4])
    self.ui.showBalance.setText(str(account.balance))
  
  def onSell(self):
    account.sell(self.data.currentDay(self.currentDay)[4])
    self.ui.showBalance.setText(str(account.balance))

  def mousePress(self, event):
    x, y = event.scenePos().x(), event.scenePos().y()
    self.newLineX, self.newLineY = x, y
    self.newLine = self.scene.addLine(x, y, x, y)
    pen = QtGui.QPen(QtCore.Qt.CustomDashLine)
    pen.setWidth(3)
    pen.setColor(QtGui.QColor(QtCore.Qt.red))
    self.newLine.setPen(pen)

  def mouseMove(self, event):
    epx = event.scenePos().x()
    epy = event.scenePos().y()
    self.newLine.setLine(epx, epy, self.newLineX, self.newLineY)


if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  window=Main()
  window.show()

  sys.exit(app.exec_())
