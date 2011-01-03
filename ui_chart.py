# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'chartWidget.ui'
#
# Created: Mon Jan  3 03:52:17 2011
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_chartWidget(object):
    def setupUi(self, chartWidget):
        chartWidget.setObjectName("chartWidget")
        chartWidget.resize(1078, 974)
        self.chart = QtGui.QGraphicsView(chartWidget)
        self.chart.setGeometry(QtCore.QRect(0, 0, 1071, 871))
        self.chart.setObjectName("chart")
        self.tabWidget = QtGui.QTabWidget(chartWidget)
        self.tabWidget.setGeometry(QtCore.QRect(0, 870, 841, 101))
        self.tabWidget.setObjectName("tabWidget")
        self.chartControls = QtGui.QWidget()
        self.chartControls.setObjectName("chartControls")
        self.zoomIn = QtGui.QPushButton(self.chartControls)
        self.zoomIn.setGeometry(QtCore.QRect(120, 30, 110, 29))
        self.zoomIn.setObjectName("zoomIn")
        self.zoomOut = QtGui.QPushButton(self.chartControls)
        self.zoomOut.setGeometry(QtCore.QRect(0, 30, 110, 29))
        self.zoomOut.setObjectName("zoomOut")
        self.sma = QtGui.QPushButton(self.chartControls)
        self.sma.setGeometry(QtCore.QRect(300, 30, 110, 29))
        self.sma.setObjectName("sma")
        self.chartLength = QtGui.QLabel(self.chartControls)
        self.chartLength.setGeometry(QtCore.QRect(70, 10, 71, 19))
        self.chartLength.setObjectName("chartLength")
        self.tabWidget.addTab(self.chartControls, "")
        self.account = QtGui.QWidget()
        self.account.setObjectName("account")
        self.buy = QtGui.QPushButton(self.account)
        self.buy.setGeometry(QtCore.QRect(130, 30, 110, 29))
        self.buy.setObjectName("buy")
        self.sell = QtGui.QPushButton(self.account)
        self.sell.setGeometry(QtCore.QRect(10, 30, 110, 29))
        self.sell.setObjectName("sell")
        self.showBalance = QtGui.QLabel(self.account)
        self.showBalance.setGeometry(QtCore.QRect(140, 10, 101, 20))
        self.showBalance.setObjectName("showBalance")
        self.balanceLabel = QtGui.QLabel(self.account)
        self.balanceLabel.setGeometry(QtCore.QRect(30, 10, 71, 19))
        self.balanceLabel.setObjectName("balanceLabel")
        self.tabWidget.addTab(self.account, "")
        self.nextDay = QtGui.QPushButton(chartWidget)
        self.nextDay.setGeometry(QtCore.QRect(850, 890, 110, 29))
        self.nextDay.setObjectName("nextDay")
        self.next30 = QtGui.QPushButton(chartWidget)
        self.next30.setGeometry(QtCore.QRect(960, 890, 110, 29))
        self.next30.setObjectName("next30")
        self.prev30 = QtGui.QPushButton(chartWidget)
        self.prev30.setGeometry(QtCore.QRect(960, 940, 110, 29))
        self.prev30.setObjectName("prev30")
        self.prevDay = QtGui.QPushButton(chartWidget)
        self.prevDay.setGeometry(QtCore.QRect(850, 940, 110, 29))
        self.prevDay.setObjectName("prevDay")

        self.retranslateUi(chartWidget)
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(chartWidget)

    def retranslateUi(self, chartWidget):
        chartWidget.setWindowTitle(QtGui.QApplication.translate("chartWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.zoomIn.setText(QtGui.QApplication.translate("chartWidget", "Zoom In", None, QtGui.QApplication.UnicodeUTF8))
        self.zoomOut.setText(QtGui.QApplication.translate("chartWidget", "Zoom Out", None, QtGui.QApplication.UnicodeUTF8))
        self.sma.setText(QtGui.QApplication.translate("chartWidget", "sma", None, QtGui.QApplication.UnicodeUTF8))
        self.chartLength.setText(QtGui.QApplication.translate("chartWidget", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.chartControls), QtGui.QApplication.translate("chartWidget", "Chart Controls", None, QtGui.QApplication.UnicodeUTF8))
        self.buy.setText(QtGui.QApplication.translate("chartWidget", "Buy", None, QtGui.QApplication.UnicodeUTF8))
        self.sell.setText(QtGui.QApplication.translate("chartWidget", "Sell", None, QtGui.QApplication.UnicodeUTF8))
        self.showBalance.setText(QtGui.QApplication.translate("chartWidget", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))
        self.balanceLabel.setText(QtGui.QApplication.translate("chartWidget", "Balance:", None, QtGui.QApplication.UnicodeUTF8))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.account), QtGui.QApplication.translate("chartWidget", "Account", None, QtGui.QApplication.UnicodeUTF8))
        self.nextDay.setText(QtGui.QApplication.translate("chartWidget", "Next Day", None, QtGui.QApplication.UnicodeUTF8))
        self.next30.setText(QtGui.QApplication.translate("chartWidget", "Next 30", None, QtGui.QApplication.UnicodeUTF8))
        self.prev30.setText(QtGui.QApplication.translate("chartWidget", "Prev 30", None, QtGui.QApplication.UnicodeUTF8))
        self.prevDay.setText(QtGui.QApplication.translate("chartWidget", "Prev Day", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    chartWidget = QtGui.QWidget()
    ui = Ui_chartWidget()
    ui.setupUi(chartWidget)
    chartWidget.show()
    sys.exit(app.exec_())

