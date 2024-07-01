# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'srthebing.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
                            QMetaObject, QObject, QPoint, QRect,
                            QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
                           QFont, QFontDatabase, QGradient, QIcon,
                           QImage, QKeySequence, QLinearGradient, QPainter,
                           QPalette, QPixmap, QRadialGradient, QTransform)

from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLineEdit,
                               QMainWindow, QMenuBar, QPlainTextEdit, QPushButton,
                               QSizePolicy, QStatusBar, QVBoxLayout, QWidget)

from videotrans.configure import config


class Ui_srthebing(object):
    def setupUi(self, srthebing):
        if not srthebing.objectName():
            srthebing.setObjectName(u"srthebing")
        srthebing.resize(643, 535)
        srthebing.setWindowModality(QtCore.Qt.NonModal)

        # sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # sizePolicy.setHorizontalStretch(1)
        # sizePolicy.setVerticalStretch(1)
        # sizePolicy.setHeightForWidth(srthebing.sizePolicy().hasHeightForWidth())
        # srthebing.setSizePolicy(sizePolicy)

        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(srthebing.sizePolicy().hasHeightForWidth())
        srthebing.setSizePolicy(sizePolicy)
        srthebing.setMaximumSize(QtCore.QSize(643, 535))

        # self.centralwidget = QWidget(srthebing)
        # self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_3 = QHBoxLayout(srthebing)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.srtinput1 = QLineEdit(srthebing)
        self.srtinput1.setObjectName(u"srtinput1")
        self.srtinput1.setMinimumSize(QSize(0, 35))

        self.srtinput1.setReadOnly(True)

        self.horizontalLayout.addWidget(self.srtinput1)

        self.srtbtn1 = QPushButton(srthebing)
        self.srtbtn1.setObjectName(u"srtbtn1")
        self.srtbtn1.setMinimumSize(QSize(180, 35))
        self.srtbtn1.setCursor(QCursor(Qt.PointingHandCursor))
        self.srtbtn1.setMouseTracking(False)

        self.horizontalLayout.addWidget(self.srtbtn1)

        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.srtinput2 = QLineEdit(srthebing)
        self.srtinput2.setObjectName(u"srtinput2")
        self.srtinput2.setMinimumSize(QSize(0, 35))
        self.srtinput2.setReadOnly(True)

        self.horizontalLayout_2.addWidget(self.srtinput2)

        self.srtbtn2 = QPushButton(srthebing)
        self.srtbtn2.setObjectName(u"srtbtn2")
        self.srtbtn2.setMinimumSize(QSize(180, 35))
        self.srtbtn2.setCursor(QCursor(Qt.PointingHandCursor))

        self.horizontalLayout_2.addWidget(self.srtbtn2)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.startbtn = QPushButton(srthebing)
        self.startbtn.setObjectName(u"startbtn")
        self.startbtn.setMinimumSize(QSize(0, 35))
        self.startbtn.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout.addWidget(self.startbtn)

        self.resultinput = QPlainTextEdit(srthebing)
        self.resultinput.setObjectName(u"resultinput")

        self.verticalLayout.addWidget(self.resultinput)

        self.resultlabel = QLabel(srthebing)
        self.resultlabel.setObjectName(u"resultlabel")

        self.verticalLayout.addWidget(self.resultlabel)

        self.resultbtn = QPushButton(srthebing)
        self.resultbtn.setObjectName(u"resultbtn")
        self.resultbtn.setMinimumSize(QSize(0, 30))
        self.resultbtn.setCursor(QCursor(Qt.PointingHandCursor))

        self.verticalLayout.addWidget(self.resultbtn)

        self.horizontalLayout_3.addLayout(self.verticalLayout)

        # srthebing.setCentralWidget(srthebing)

        self.retranslateUi(srthebing)

        QMetaObject.connectSlotsByName(srthebing)

    # setupUi

    def retranslateUi(self, srthebing):
        srthebing.setWindowTitle("合并2个字幕组成双语字幕" if config.defaulelang == 'zh' else 'Merge 2 subtitles')
        self.srtinput1.setPlaceholderText(
            "第一个字幕文件:最终字幕长度以此为准" if config.defaulelang == 'zh' else 'Subtitle file 1:The final length of the subtitles will be determined accordingly.')
        self.srtinput1.setToolTip(
            "第一个字幕文件:最终字幕长度以此为准" if config.defaulelang == 'zh' else 'Subtitle file 1:The final length of the subtitles will be determined accordingly.')
        self.srtinput2.setPlaceholderText("第二个字幕文件" if config.defaulelang == 'zh' else 'Subtitle file 2')
        self.srtbtn1.setText("选择第一个字幕" if config.defaulelang == 'zh' else 'Select the first subtitle')
        self.srtbtn2.setText("选择第二个字幕" if config.defaulelang == 'zh' else 'Select the second subtitle')
        self.startbtn.setText("开始执行合并" if config.defaulelang == 'zh' else 'commencement of execution')
        self.resultlabel.setText("")
        self.resultinput.setPlaceholderText("这里显示合并结果" if config.defaulelang == 'zh' else "The merge result is shown here") 
        self.resultbtn.setText("打开保存结果目录" if config.defaulelang == 'zh' else 'Open the save results directory')
    # retranslateUi
