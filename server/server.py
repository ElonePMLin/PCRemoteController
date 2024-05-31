import const
from serverThread import ImageThread, ControllerThread
import socket


def handle_client(conn):
    # print(type(conn))
    plat = b''
    while True:
        plat += conn.recv(3 - len(plat))
        if len(plat) == 3:
            break
    print(f'connected platform: {plat.decode()}')
    imageVideo = ImageThread(conn)
    recController = ControllerThread(conn, plat.decode())
    imageVideo.daemon = True
    recController.daemon = True
    imageVideo.start()
    recController.start()


def main():
    sock = socket.socket(socket.AF_INET, socket.AI_PASSIVE)
    sock.bind((const.SERVER_IPV4, const.SERVER_PORT))
    sock.listen(1)
    print(f"IPV4 server start, listening port {const.SERVER_PORT}")
    while True:
        conn, addr = sock.accept()
        handle_client(conn)


main()
