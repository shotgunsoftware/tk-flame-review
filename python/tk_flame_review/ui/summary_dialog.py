# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'summary_dialog.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

try:
    from tank.platform.qt.QtCore import *
except ImportError:
    from PySide2.QtCore import *
try:
    from tank.platform.qt.QtGui import *
except ImportError:
    from PySide2.QtGui import *
try:
    from tank.platform.qt.QtWidgets import *
except ImportError:
    from PySide2.QtWidgets import *

from  . import resources_rc

class Ui_SummaryDialog(object):
    def setupUi(self, SummaryDialog):
        if not SummaryDialog.objectName():
            SummaryDialog.setObjectName("SummaryDialog")
        SummaryDialog.resize(501, 175)
        self.verticalLayout = QVBoxLayout(SummaryDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(20, -1, 20, -1)
        self.stackedWidget = QStackedWidget(SummaryDialog)
        self.stackedWidget.setObjectName("stackedWidget")
        self.page = QWidget()
        self.page.setObjectName("page")
        self.verticalLayout_2 = QVBoxLayout(self.page)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QLabel(self.page)
        self.label.setObjectName("label")
        self.label.setPixmap(QPixmap(":/tk-flame-review/submission_complete.png"))

        self.verticalLayout_2.addWidget(self.label)

        self.stackedWidget.addWidget(self.page)
        self.page_2 = QWidget()
        self.page_2.setObjectName("page_2")
        self.verticalLayout_3 = QVBoxLayout(self.page_2)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label_2 = QLabel(self.page_2)
        self.label_2.setObjectName("label_2")
        self.label_2.setPixmap(QPixmap(":/tk-flame-review/submission_failed.png"))

        self.verticalLayout_3.addWidget(self.label_2)

        self.stackedWidget.addWidget(self.page_2)

        self.verticalLayout.addWidget(self.stackedWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalSpacer = QSpacerItem(368, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.submit = QPushButton(SummaryDialog)
        self.submit.setObjectName("submit")

        self.horizontalLayout.addWidget(self.submit)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(SummaryDialog)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(SummaryDialog)
    # setupUi

    def retranslateUi(self, SummaryDialog):
        SummaryDialog.setWindowTitle(QCoreApplication.translate("SummaryDialog", "Submit to ShotGrid", None))
        self.label.setText("")
        self.label_2.setText("")
        self.submit.setText(QCoreApplication.translate("SummaryDialog", "Ok", None))
    # retranslateUi

