import socket
import sqlite3
import datetime
import struct
import sys

BUFFER_SIZE = 1024
IS_ARMED = True


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
            print data
            if data:
                data = struct.unpack('BB', data)
                alert_type = data[0]
                uid = data[1]
                self.__handle_alert(alert_type, uid)

    def __handle_alert(self, alert_type, uid):
        global IS_ARMED
        timestamp = datetime.datetime.now()
        # TODO: Fix arms log insertion
        event_insertion_line = 'INSERT INTO app_events VALUES (?, ?, ?, ?, ?)'
        arms_log_insertion_line = 'INSERT INTO app_armslog VALUES (?, ?, ?, ?)'
        if alert_type == 0:
            IS_ARMED = False
            self.__cursor.execute(arms_log_insertion_line, (None, 'Unarmed', timestamp, uid))
        elif alert_type == 1 and IS_ARMED:
            self.__cursor.execute(event_insertion_line, (None, 'Breach', 'Asset has been opened while alarm was armed',
                                  timestamp, 'Critical'))
            last_inserted_id = self.__cursor.lastrowid
            # TODO: create take_snapshot method
            # take_snapshot(last_inserted_id)
            self.__mark_last_event_as_unerad()
        elif alert_type == 2 and IS_ARMED:
            self.__cursor.execute(event_insertion_line, (None, 'Door knock',
                                  'Vibrations on the door had been detected while alarm was armed', timestamp,
                                                         'Information'))
            last_inserted_id = self.__cursor.lastrowid()
            # take_snapshot(last_inserted_id)
            self.__mark_last_event_as_unerad()
        elif alert_type == 100:
            IS_ARMED = True
            self.__cursor.execute(arms_log_insertion_line, (None, 'Armed', timestamp, uid))

        self.__db_connection.commit()

    def __mark_last_event_as_unerad(self):
        last_event_id = self.__cursor.execute('SELECT id FROM app_events ORDER BY id DESC LIMIT 1').fetchone()[0]
        users_list = self.__cursor.execute('SELECT UID FROM app_appusers').fetchall()

        for user in users_list:
            self.__cursor.execute('INSERT INTO app_unreadevents VALUES (?, ?, ?)', (None, last_event_id, user[0]))


def parse_configuration_file():
    try:
        conf_file = open('./sync.conf', 'rb')
    except:
        print 'sync.conf is missing'
        sys.exit(-1)

    configuration = conf_file.read().split('\n')
    conf_file.close()
    configuration_fields = {}

    for line in configuration:
        if not line:
            pass
        key = line.split('=')[0]
        value = line.split('=')[1]
        configuration_fields[key] = value
    return configuration_fields

configuration = parse_configuration_file()

port = int(configuration.get('PORT', '9898'))
db_path = configuration.get('DB_PATH', '../db.sqlite3')
images_path = configuration.get('IMAGES_PATH', '/home/user/GoServer/images/')

listener = ArduinoListener(listening_port=port, db_name=db_path)

listener.run_server()
