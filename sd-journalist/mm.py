import sys
from PyQt4.QtGui import QDialog, QDialogButtonBox, QApplication, QLabel, QVBoxLayout
from PyQt4.QtCore import Qt
import os
import errno
import threading
import pipereader

class SDDialog(QDialog):
    def __init__(self, parent = None):
        super(SDDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.display = QLabel()
        self.display.setText("Hello PYQT")
        layout.addWidget(self.display)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        layout.addWidget(self.buttons)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

app = QApplication([])
d = SDDialog()

def send_to_ui(poller, msg, err):
    d.display.setText(msg.rstrip())

reader = pipereader.PipeReader("myfifo", send_to_ui)
t = threading.Thread(target=reader.read)
t.start()
d.show()

app.exec_()

reader.quit()
sys.exit()
