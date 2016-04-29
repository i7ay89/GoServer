import socket
import sqlite3
import datetime
import struct

BUFFER_SIZE = 1024


class ArduinoListener(object):
    def __init__(self, listening_port=9898, db_name='../db.sqlite3'):
        self.__port = listening_port
        self.__db_name = db_name
        self._get_self_address()

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind((self.__server_address, self.__port))

        self.__db_connection = sqlite3.connect(self.__db_name)
        self.__cursor = self.__db_connection.cursor()

    def __del__(self):
        try:
            self.__sock.close()
        except:
            pass

    def _get_self_address(self):
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        test_socket.connect(('8.8.8.8', 80))

        self.__server_address = test_socket.getsockname()[0]

        test_socket.close()

    def run_server(self):
        while True:
            data, address = self.__sock.recvfrom(BUFFER_SIZE)
            data = struct.unpack('B', data)[0]
            if data:
                self._handle_alert(data)

    def _handle_alert(self, data):
        timestamp = datetime.datetime.now()
        insertion_line = 'INSERT INTO Events VALUES (?, ?, ?, ?)'
        if data == 1:
            print 'updating 1'
            self.__cursor.execute(insertion_line, 'Breach', 'Asset has been opened while alarm was armed', timestamp,
                                  'Critical')
        elif data == 2:
            print 'updating 2'
            self.__cursor.execute(insertion_line, 'Door knock',
                                  'Vibrations on the door had been detected while alarm was armed', timestamp,
                                  'Information')
        self.__db_connection.commit()

listener = ArduinoListener()
listener.run_server()