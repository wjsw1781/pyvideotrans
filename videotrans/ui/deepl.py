# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'deepl.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_deeplform(object):
    def setupUi(self, deeplform):
        deeplform.setObjectName("deeplform")
        deeplform.setWindowModality(QtCore.Qt.NonModal)
        deeplform.resize(400, 223)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(deeplform.sizePolicy().hasHeightForWidth())
        deeplform.setSizePolicy(sizePolicy)
        deeplform.setMaximumSize(QtCore.QSize(400, 300))
        self.gridLayout = QtWidgets.QGridLayout(deeplform)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.formLayout_2.setFormAlignment(QtCore.Qt.AlignJustify|QtCore.Qt.AlignVCenter)
        self.formLayout_2.setObjectName("formLayout_2")
        self.label = QtWidgets.QLabel(deeplform)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMinimumSize(QtCore.QSize(100, 35))
        self.label.setAlignment(QtCore.Qt.AlignJustify|QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label)
        self.deepl_authkey = QtWidgets.QLineEdit(deeplform)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.deepl_authkey.sizePolicy().hasHeightForWidth())
        self.deepl_authkey.setSizePolicy(sizePolicy)
        self.deepl_authkey.setMinimumSize(QtCore.QSize(210, 35))
        self.deepl_authkey.setObjectName("deepl_authkey")
        self.formLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.deepl_authkey)
        self.verticalLayout.addLayout(self.formLayout_2)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.set_deepl = QtWidgets.QPushButton(deeplform)
        self.set_deepl.setMinimumSize(QtCore.QSize(0, 35))
        self.set_deepl.setObjectName("set_deepl")
        self.verticalLayout_2.addWidget(self.set_deepl)
        self.gridLayout.addLayout(self.verticalLayout_2, 0, 0, 1, 1)

        self.retranslateUi(deeplform)
        QtCore.QMetaObject.connectSlotsByName(deeplform)

    def retranslateUi(self, deeplform):
        _translate = QtCore.QCoreApplication.translate
        deeplform.setWindowTitle(_translate("deeplform", "Baidu"))
        self.label.setText(_translate("deeplform", "DEEPL_AUTH_KEY"))
        self.set_deepl.setText(_translate("deeplform", "OK"))