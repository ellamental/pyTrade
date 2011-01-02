# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'chartWidget.ui'
#
# Created: Sun Jan  2 03:54:21 2011
#      by: PyQt4 UI code generator 4.7.2
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_chartWidget(object):
    def setupUi(self, chartWidget):
        chartWidget.setObjectName("chartWidget")
        chartWidget.resize(873, 710)
        self.chart = QtGui.QGraphicsView(chartWidget)
        self.chart.setGeometry(QtCore.QRect(0, 0, 881, 631))
        self.chart.setObjectName("chart")
        self.zoomIn = QtGui.QPushButton(chartWidget)
        self.zoomIn.setGeometry(QtCore.QRect(0, 630, 110, 29))
        self.zoomIn.setObjectName("zoomIn")
        self.zoomOut = QtGui.QPushButton(chartWidget)
        self.zoomOut.setGeometry(QtCore.QRect(0, 680, 110, 29))
        self.zoomOut.setObjectName("zoomOut")
        self.chartLength = QtGui.QLabel(chartWidget)
        self.chartLength.setGeometry(QtCore.QRect(20, 660, 71, 19))
        self.chartLength.setObjectName("chartLength")

        self.retranslateUi(chartWidget)
        QtCore.QMetaObject.connectSlotsByName(chartWidget)

    def retranslateUi(self, chartWidget):
        chartWidget.setWindowTitle(QtGui.QApplication.translate("chartWidget", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.zoomIn.setText(QtGui.QApplication.translate("chartWidget", "Zoom In", None, QtGui.QApplication.UnicodeUTF8))
        self.zoomOut.setText(QtGui.QApplication.translate("chartWidget", "Zoom Out", None, QtGui.QApplication.UnicodeUTF8))
        self.chartLength.setText(QtGui.QApplication.translate("chartWidget", "TextLabel", None, QtGui.QApplication.UnicodeUTF8))


if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    chartWidget = QtGui.QWidget()
    ui = Ui_chartWidget()
    ui.setupUi(chartWidget)
    chartWidget.show()
    sys.exit(app.exec_())

