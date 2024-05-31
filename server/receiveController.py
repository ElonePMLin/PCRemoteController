import mss
import const
import struct
from _controler import getControllerMapping
from socket import socket
import pyautogui


class ReceiveController(object):

    def __init__(self, conn: socket, plat):
        self.conn = conn
        with mss.mss() as sct:
            self.windowSize = [sct.monitors[1]['width'], sct.monitors[1]['height']]
        # self.controllerMap = getControllerMapping(plat)
        self.crtlenb = const.CONTROL_LENGTH
        pyautogui.FAILSAFE = False

    def action(self, typ, act, x, y):
        width, height = self.windowSize
        ox, oy = (x / 100) * width, (y / 100) * height
        # print(x / 100 * width, y / 100 * height)
        # typ: 0, move; 1, left; 2, right; 4, middle; 31, roll
        if typ == 0:
            # pyautogui.move(ox, oy)
            pass
        elif typ == 1:
            if act == 2:
                pyautogui.mouseDown(ox, oy, button=pyautogui.LEFT)
            elif act == 3:
                pyautogui.mouseUp(ox, oy, button=pyautogui.LEFT)
        elif typ == 2:
            if act == 2:
                pyautogui.mouseDown(ox, oy, button=pyautogui.RIGHT)
            elif act == 3:
                pyautogui.mouseUp(ox, oy, button=pyautogui.RIGHT)
        elif typ == 31:
            if act == 0:
                pyautogui.hscroll(const.MOUSE_SCROLL)
            elif act == 1:
                pyautogui.hscroll(-const.MOUSE_SCROLL)
            elif act == 2:
                pyautogui.vscroll(const.MOUSE_SCROLL)
            elif act == 3:
                pyautogui.scroll(-const.MOUSE_SCROLL)
        elif typ == 4:
            if act == 2:
                pyautogui.mouseDown(ox, oy, button=pyautogui.MIDDLE)
            elif act == 3:
                pyautogui.mouseUp(ox, oy, button=pyautogui.MIDDLE)
        elif typ == 5:  # keyboard

            print(chr(act))
            pass

    def control(self):
        print('controller')
        cnt = 0
        while True:  # 发一次
            # cnt += 1
            crt = b''
            rest = self.crtlenb
            while rest > 0:
                crt += self.conn.recv(rest)
                rest -= len(crt)
            typ = crt[0]
            act = crt[1]
            x = struct.unpack('>H', crt[2:4])[0]
            y = struct.unpack('>H', crt[4:6])[0]
            self.action(typ, act, x, y)
            # print(typ, act, x, y)
