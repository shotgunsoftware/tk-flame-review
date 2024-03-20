# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'submit_dialog.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from sgtk.platform.qt import QtCore
for name, cls in QtCore.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls

from sgtk.platform.qt import QtGui
for name, cls in QtGui.__dict__.items():
    if isinstance(cls, type): globals()[name] = cls



from  . import resources_rc

class Ui_SubmitDialog(object):
    def setupUi(self, SubmitDialog):
        if not SubmitDialog.objectName():
            SubmitDialog.setObjectName("SubmitDialog")
        SubmitDialog.resize(475, 559)
        self.verticalLayout = QVBoxLayout(SubmitDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout.setContentsMargins(20, -1, 20, -1)
        self.label = QLabel(SubmitDialog)
        self.label.setObjectName("label")
        self.label.setPixmap(QPixmap(":/tk-flame-review/ui_splash.png"))

        self.verticalLayout.addWidget(self.label)

        self.comments = QPlainTextEdit(SubmitDialog)
        self.comments.setObjectName("comments")
        self.comments.setMinimumSize(QSize(300, 100))

        self.verticalLayout.addWidget(self.comments)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.horizontalSpacer = QSpacerItem(368, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.cancel = QPushButton(SubmitDialog)
        self.cancel.setObjectName("cancel")

        self.horizontalLayout.addWidget(self.cancel)

        self.submit = QPushButton(SubmitDialog)
        self.submit.setObjectName("submit")

        self.horizontalLayout.addWidget(self.submit)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.comments.raise_()
        self.label.raise_()

        self.retranslateUi(SubmitDialog)

        QMetaObject.connectSlotsByName(SubmitDialog)
    # setupUi

    def retranslateUi(self, SubmitDialog):
        SubmitDialog.setWindowTitle(QCoreApplication.translate("SubmitDialog", "Submit to Flow Production Tracking", None))
        self.label.setText("")
        self.cancel.setText(QCoreApplication.translate("SubmitDialog", "Cancel", None))
        self.submit.setText(QCoreApplication.translate("SubmitDialog", "Submit to Flow Production Tracking", None))
    # retranslateUi

