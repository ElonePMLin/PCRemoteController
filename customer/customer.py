import const
import struct
import asyncio
from PyQt5 import QtGui, QtWidgets
import sys
import platform
import cv2
import numpy as np
from threading import Thread
import typing
import time

# 平台
PLATFORM = b''
if sys.platform == "win32":
    const.PLATFORM = b'win'
elif sys.platform == "darwin":
    const.PLATFORM = b'osx'
elif platform.system() == "Linux":
    const.PLATFORM = b'osx'


class ClientGUI(QtWidgets.QMainWindow):

    def __init__(self):
        super(ClientGUI, self).__init__()
        self.setWindowTitle('远程控制')
        self.setGeometry(0, 0, 970, 768)
        self.windowSize = [self.window().width(), self.window().height()]
        self.setupUi(self)
        self.reader = None
        self.writer = None
        # 开启跟踪鼠标模式
        self.grabMouse()
        self.setMouseTrackingEnable = False

        self.thread = Thread(target=self.start)
        self.thread.daemon = True
        self.thread.start()

    # 初始化屏幕窗口
    def screenLabel(self, MainWindow):
        self.screen_label = QtWidgets.QLabel(MainWindow)  # 绑定
        self.screen_label.setFixedSize(970, 768)  # 初始大小
        self.screen_label.setAutoFillBackground(False)

    def setupUi(self, MainWindow):
        # self.mouseMoveTimer = QtCore.QTimer()
        # self.mouseMoveTimer.start(500)
        # self.mouseMoveTimer.timeout.connect(self.mouseMoveSend)
        self.screenLabel(MainWindow)

    def mouseMoveSend(self):
        self.setMouseTrackingEnable = not self.setMouseTrackingEnable
        self.setMouseTracking(self.setMouseTrackingEnable)

    def resizeEvent(self, a0: typing.Optional[QtGui.QResizeEvent]) -> None:
        width, height = a0.size().width(), a0.size().height()
        self.windowSize = [width, height]
        self.screen_label.setFixedSize(width, height)

    async def receiveImage(self):
        start = time.time()
        lenb = await self.reader.read(5)  # 获取类型和长度
        datatype, length = struct.unpack('>BI', lenb)
        encoded = b''
        while length > const.MAX_BYTES:
            byte = await self.reader.read(const.MAX_BYTES)
            encoded += byte
            length -= len(byte)
        while length > 0:
            byte = await self.reader.read(length)
            encoded += byte
            length -= len(byte)

        imgdata = np.frombuffer(encoded, dtype=np.uint8)  # 转为数据类型
        image = cv2.imdecode(imgdata, cv2.IMREAD_COLOR)
        # print("接收：", time.time() - start)
        return datatype, image

    def updateScreen(self, image):
        # 根据窗口调整大小
        width, height = self.windowSize
        image = cv2.resize(image, (width, height))
        # image = cv2.cvtColor(image, cv2.COLOR_RGBA2BGR)
        canvas = QtGui.QImage(image.data, width, height, width * 3, QtGui.QImage.Format_RGB888)
        self.screen_label.setPixmap(QtGui.QPixmap.fromImage(canvas))

    async def sendAction(self, typ, code, x, y):
        data = struct.pack('>BBHH', typ, code, x, y)
        self.writer.write(data)
        await self.writer.drain()

    def mouseAction(self, mouse: typing.Optional[QtGui.QMouseEvent]):
        width, height = self.windowSize
        x, y = [mouse.x() * 100 / width, mouse.y() * 100 / height]
        # print(int(x), int(y))
        typ = mouse.button()  #cmd0 0,move; 1,left; 2,right; 4,middle
        act = mouse.type()  # 2, down; 3, release; 5 move
        asyncio.run(self.sendAction(typ, act, int(x), int(y)))

    def wheelAction(self, mouse: typing.Optional[QtGui.QWheelEvent]):
        # left-1, right+1；up-1, down+1
        typ = mouse.type()  # 31 滚轮
        x, y = mouse.angleDelta().x(), mouse.angleDelta().y()
        print(x, y)
        act = 255
        if y > 0:
            act = 0  # down
        elif y < 0:
            y = -y
            act = 1  # up
        elif x > 0:
            act = 2  # right
        elif x < 0:
            x = -x
            act = 3  # left
        asyncio.run(self.sendAction(typ, act, x, y))

    def mouseMoveEvent(self, a0: typing.Optional[QtGui.QMouseEvent]) -> None:
        if not self.isConnected():
            return
        self.mouseAction(a0)

    def mousePressEvent(self, a0: typing.Optional[QtGui.QMouseEvent]) -> None:
        if not self.isConnected():
            return
        # print(a0.button())  # left 1，right 2
        self.mouseAction(a0)

    def mouseReleaseEvent(self, a0: typing.Optional[QtGui.QMouseEvent]) -> None:
        if not self.isConnected():
            return
        # print(a0.type())  # left 1，right 2
        self.mouseAction(a0)

    def wheelEvent(self, a0: typing.Optional[QtGui.QWheelEvent]) -> None:
        if not self.isConnected():
            return
        # print(a0.type())
        self.wheelAction(a0)

    def keyPressEvent(self, a0: typing.Optional[QtGui.QKeyEvent]) -> None:
        print(a0.key(), a0.text().encode(), a0.nativeScanCode())
        # asyncio.run(self.sendAction(5, a0.key(), 0, 0))

    def isConnected(self):
        if not self.reader or not self.writer:
            return False
        return True

    async def connect(self, ip=None, port=None):
        # '10.10.1.191'
        self.reader, self.writer = await asyncio.open_connection('10.211.55.3', const.SERVER_PORT)

        # 系统类型，以便服务器正确操作鼠标、键盘
        self.writer.write(const.PLATFORM)
        await self.writer.drain()

        typ, prevImage = await self.receiveImage()
        h, w, _ = prevImage.shape  # 原图片大小
        self.updateScreen(prevImage)
        pre_time = 0

        while True:
            start = time.time()

            typ, image = await self.receiveImage()
            if typ == const.TRANSPORT_IMAGE:
                prevImage = image
            else:
                prevImage ^= image
            self.updateScreen(prevImage)
            # print("一循环", time.time() - start + pre_time)
            pre_time = 0

    def start(self):
        asyncio.run(self.connect())


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    client = ClientGUI()
    client.show()
    sys.exit(app.exec_())
