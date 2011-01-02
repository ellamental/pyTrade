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
###############################################################################


import os,sys,time

from PyQt4 import QtCore, QtGui
from urllib import urlopen

## import QtDesigner UI module
from ui_chart import Ui_Form



screenWidth = 1024
screenHeight = 860

def googDownload(symbol):
  dat = urlopen("http://www.google.com/finance/historical?q="+symbol+"&startdate=Dec+30%2C+2000&enddate=Dec+31%2C+2010&num=30&output=csv").read()
  data = [ii.split(',') for ii in dat.split('\n')]
  return [[ii[0], float(ii[1]), float(ii[2]), float(ii[3]), float(ii[4]), int(ii[5])] for ii in data[1:-1]]

def adjustPrices(data):
  minprice = min([ii[3] for ii in data])
  adjprices = [[ii[0], ii[1]-minprice, ii[2]-minprice, ii[3]-minprice, ii[4]-minprice, ii[5]] for ii in data]
  maxprice = max([ii[4] for ii in adjprices])
  multiple = screenHeight/maxprice
  return [[ii[0], ii[1]*multiple, ii[2]*multiple, ii[3]*multiple, ii[4]*multiple, ii[5]] for ii in adjprices]


# Create a class for our main window
class Main(QtGui.QWidget):
  def __init__(self):
    QtGui.QWidget.__init__(self)

    # This is always the same
    self.ui=Ui_Form()
    self.ui.setupUi(self)

    ## Create a new Graphics Scene
    self.scene = QtGui.QGraphicsScene()
    self.scene.setSceneRect(0,0,screenWidth-100,screenHeight-100)
    
    ## Set the GraphicsView (chart) to view the GraphicsScene above
    self.ui.chart.setScene(self.scene)

    ## initialize data to be used with the chart
    self.data = googDownload("msft")
    self.currentDay = 0
    self.chartLength = 60

    ## draw the chart
    self.drawChart()
    
    ## Maximize screen 
    #self.setWindowState(QtCore.Qt.WindowMaximized)
    
    ## Connect buttons
    self.connect(self.ui.zoomIn, QtCore.SIGNAL("clicked()"), self.onZoomIn)
    self.connect(self.ui.zoomOut, QtCore.SIGNAL("clicked()"), self.onZoomOut)


  def drawChart(self):
    
    d = adjustPrices(self.data[self.currentDay:self.chartLength])

    offsetmod = screenWidth/len(d)
    offset = screenWidth-offsetmod

    for ii in d:
      if ii[1] > ii[4]:
        b = QtGui.QColor(50,50,50,250)
      else:
        b = QtGui.QColor(250,250,250,250)
      
      self.scene.addRect(offset+offsetmod/4, screenHeight-ii[2], 1, ii[2]-ii[3], brush=b)
      self.scene.addRect(offset, screenHeight-ii[1], offsetmod/2, ii[1]-ii[4], brush=b)
      
      offset -= offsetmod

  def onZoomIn(self):
    self.scene.clear()
    self.scene.update()
    self.chartLength -= 10
    self.drawChart()
    
  def onZoomOut(self):
    self.scene.clear()
    self.scene.update()
    self.chartLength += 10
    self.drawChart()


def main():
  # Again, this is boilerplate, it's going to be the same on
  # almost every app you write
  app = QtGui.QApplication(sys.argv)
  window=Main()
  window.show()

  # It's exec_ because exec is a reserved word in Python
  sys.exit(app.exec_())


if __name__ == "__main__":
    main()
