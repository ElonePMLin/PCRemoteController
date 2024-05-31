from threading import Thread
from imageCap import ImageCapture
from receiveController import ReceiveController


class ImageThread(Thread):

    def __init__(self, conn):
        super(ImageThread, self).__init__()
        self.cap = ImageCapture(conn)

    def run(self) -> None:
        self.cap.server()


class ControllerThread(Thread):

    def __init__(self, conn, plat):
        super(ControllerThread, self).__init__()
        self.controller = ReceiveController(conn, plat)

    def run(self) -> None:
        self.controller.control()
