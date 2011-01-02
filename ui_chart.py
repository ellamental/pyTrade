# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'chartWidget.ui'
#
# Created: Sun Jan  2 06:18:02 2011
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_chartWidget(object):
    def setupUi(self, chartWidget):
        chartWidget.setObjectName("chartWidget")
        chartWidget.resize(1073, 963)
        self.chart = QtGui.QGraphicsView(chartWidget)
        self.chart.setGeometry(QtCore.QRect(0, 0, 1071, 871))
        self.chart.setObjectName("chart")
        self.zoomIn = QtGui.QPushButton(chartWidget)
        self.zoomIn.setGeometry(QtCore.QRect(0, 880, 110, 29))
        self.zoomIn.setObjectName("zoomIn")
        self.zoomOut = QtGui.QPushButton(chartWidget)
        self.zoomOut.setGeometry(QtCore.QRect(0, 930, 110, 29))
        self.zoomOut.setObjectName("zoomOut")
        self.chartLength = QtGui.QLabel(chartWidget)
        self.chartLength.setGeometry(QtCore.QRect(20, 910, 71, 19))
        self.chartLength.setObjectName("chartLength")
        self.nextDay = QtGui.QPushButton(chartWidget)
        self.nextDay.setGeometry(QtCore.QRect(850, 880, 110, 29))
        self.nextDay.setObjectName("nextDay")
        self.prevDay = QtGui.QPushButton(chartWidget)
        self.prevDay.setGeometry(QtCore.QRect(850, 930, 110, 29))
        self.prevDay.setObjectName("prevDay")
        self.next30 = QtGui.QPushButton(chartWidget)
        self.next30.setGeometry(QtCore.QRect(960, 880, 110, 29))
        self.next30.setObjectName("next30")
        self.prev30 = QtGui.QPushButton(chartWidget)
        self.prev30.setGeometry(QtCore.QRect(960, 930, 110, 29))
        self.prev30.setObjectName("prev30")
        self.sell = QtGui.QPushButton(chartWidget)
        self.sell.setGeometry(QtCore.QRect(540, 930, 110, 29))
        self.sell.setObjectName("sell")
        self.buy = QtGui.QPushButton(chartWidget)
        self.buy.setGeometry(QtCore.QRect(660, 930, 110, 29))
        self.buy.setObjectName("buy")
        self.balanceLabel = QtGui.QLabel(chartWidget)
        self.balanceLabel.setGeometry(QtCore.QRect(560, 900, 71, 19))
        self.balanceLabel.setObjectName("balanceLabel")
        self.showBalance = QtGui.QLabel(chartWidget)
        self.showBalance.setGeometry(QtCore.QRect(680, 900, 71, 19))
        self.showBalance.setObjectName("showBalance")

        self.retranslateUi(chartWidget)
        QtCore.QMetaObject.connectSlotsByName(chartWidget)

    def retranslateUi(self, chartWidget):
        chartWidget.setWindowTitle(QtGui.QApplication.translate("chartWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.zoomIn.setText(QtGui.QApplication.translate("chartWidget", "Zoom In", None, QtGui.QApplication.UnicodeUTF8))
        self.zoomOut.setText(QtGui.QApplication.translate("chartWidget", "Zoom Out", None, QtGui.QApplication.UnicodeUTF8))
        self.chartLength.setText(QtGui.QApplication.translate("chartWidget", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.nextDay.setText(QtGui.QApplication.translate("chartWidget", "Next Day", None, QtGui.QApplication.UnicodeUTF8))
        self.prevDay.setText(QtGui.QApplication.translate("chartWidget", "Prev Day", None, QtGui.QApplication.UnicodeUTF8))
        self.next30.setText(QtGui.QApplication.translate("chartWidget", "Next 30", None, QtGui.QApplication.UnicodeUTF8))
        self.prev30.setText(QtGui.QApplication.translate("chartWidget", "Prev 30", None, QtGui.QApplication.UnicodeUTF8))
        self.sell.setText(QtGui.QApplication.translate("chartWidget", "Sell", None, QtGui.QApplication.UnicodeUTF8))
        self.buy.setText(QtGui.QApplication.translate("chartWidget", "Buy", None, QtGui.QApplication.UnicodeUTF8))
        self.balanceLabel.setText(QtGui.QApplication.translate("chartWidget", "Balance:", None, QtGui.QApplication.UnicodeUTF8))
        self.showBalance.setText(QtGui.QApplication.translate("chartWidget", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    chartWidget = QtGui.QWidget()
    ui = Ui_chartWidget()
    ui.setupUi(chartWidget)
    chartWidget.show()
    sys.exit(app.exec_())

