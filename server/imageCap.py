from PIL import ImageGrab, Image
import cv2
import struct
from socket import socket
import numpy as np
import time
import const
import mss
from threading import Thread
from queue import Queue


class ImageCapture(object):

    def __init__(self, conn: socket):
        self.conn = conn
        self.prevImage = None  # 压缩过的图片数据（图片）
        self.prevEncoded = None  # 图片编码后的数据（数据）
        self.frame = Queue(const.FPS * const.PRE_LOAD_SIZE)
        self.capThread = Thread(target=self.capImage)
        self.capThread.daemon = True

    def encode(self, image, encode_type: str, quality=None):
        """
        压缩图片质量
        :param image:
        :param encode_type:
        :param quality:
            [cv2.IMWRITE_JPEG_QUALITY, IMQUALITY=50]
            .jpg -> IMQUALITY (1 ~ 100) 越大压缩得越大
        :return:
        """
        imgdata = np.asarray(image)  # 转为数组
        if not quality:
            encoded = cv2.imencode(encode_type, imgdata)[1]
        else:
            encoded = cv2.imencode(encode_type, imgdata, quality)[1]
        return encoded

    def decode(self, encoded):
        """
        返回的图片是经过压缩后的质量
        :param encoded:
        :return:
        """
        imgdata = np.asarray(encoded, np.uint8)
        image = cv2.imdecode(imgdata, cv2.IMREAD_COLOR)
        return image

    def getImgInfo(self, image, encoded):
        w, h, _ = image.shape
        # print(f"size: {len(encoded) / 1024 / 1024}, width: {w}, height: {h}")

    def write2client(self, encode_image, length, transport_type):
        try:
            lenb = struct.pack(">BI", transport_type, length)
            self.conn.sendall(lenb)
            self.conn.sendall(encode_image.tostring())
        except Exception as e:
            print(e)
            self.conn = None

    def server(self):
        # 获取起始的图片数据
        imgOrg = ImageGrab.grab()
        # self.getImgInfo(np.asarray(imgOrg))
        if not isinstance(self.prevEncoded, np.ndarray):
            self.prevEncoded = self.encode(imgOrg, '.jpg', [cv2.IMWRITE_JPEG_QUALITY, 50])
            # self.encoded = self.encode(imgOrg, '.png')
            self.prevImage = self.decode(self.prevEncoded)

        self.getImgInfo(self.prevImage, self.prevEncoded)

        self.capThread.start()
        # await self.write2client(self.prevEncoded, len(self.prevEncoded), const.TRANSPORT_IMAGE)
        self.write2client(self.prevEncoded, len(self.prevEncoded), const.TRANSPORT_IMAGE)
        pre_time = 0
        # 发送屏幕信息
        cnt = 0
        while True:  # 发一次
            # cnt += 1
            start = time.time()
            time.sleep(const.DELAY)  # 0.05
            # imgOrg = ImageGrab.grab()
            if self.frame.qsize() == 0:
                pre_time += time.time() - start
                continue
            # imgOrg = self.frame.get(block=True, timeout=None)
            image, encoded, changeImg, frameEncoded = self.frame.get(block=True, timeout=None)
            self.frame.task_done()  # -1

            # 状态更新
            self.getImgInfo(image, encoded)
            self.prevEncoded = encoded
            self.prevImage = image

            # 无损压缩（帧处理）
            # _, frameEncoded = cv2.imencode('.png', changeImg)
            encodedSize = len(encoded)  # 原截屏大小
            frameSize = len(frameEncoded)  # 帧大小
            if encodedSize > frameSize:
                # await self.write2client(frameEncoded, frameSize, const.TRANSPORT_FRAME)
                self.write2client(frameEncoded, frameSize, const.TRANSPORT_FRAME)
            else:
                # 如果帧比原图片都大，传原图片即可
                # await self.write2client(encoded, encodedSize, const.TRANSPORT_IMAGE)
                self.write2client(encoded, encodedSize, const.TRANSPORT_IMAGE)

            # print(f"使用帧：", time.time() - start + pre_time)
            pre_time = 0

    def capImage(self):
        with mss.mss() as sct:
            print(sct.monitors)
            while True:
                if not self.conn:
                    break
                if not isinstance(self.prevImage, np.ndarray):
                    continue
                start = time.time()
                image = sct.grab(sct.monitors[1])
                imgOrg = Image.frombytes(mode='RGB', size=image.size, data=image.rgb)
                # self.frame.put(imgOrg, block=True, timeout=None)

                encoded = self.encode(imgOrg, '.jpg', [cv2.IMWRITE_JPEG_QUALITY, 100])
                image = self.decode(encoded)

                changeImg = image ^ self.prevImage

                if (changeImg == 0).all():  # 没有帧变化
                    continue

                # 无损压缩（帧处理）
                _, frameEncoded = cv2.imencode('.png', changeImg)
                self.frame.put((image, encoded, changeImg, frameEncoded), block=True, timeout=None)

                # 状态更新
                # print(f"保存帧：", time.time() - start)
