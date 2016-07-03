import socket
import sqlite3
import datetime
import struct
import sys

BUFFER_SIZE = 1024
FIXED_PACKET_SIZE = 6


class AlertsListener(object):
    def __init__(self, listening_port=9898, db_name='../db.sqlite3'):
        self.__port = listening_port
        self.__db_name = db_name
        self._get_self_address()

        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__sock.bind((self.__server_address, self.__port))

        self.__db_connection = sqlite3.connect(self.__db_name)
        self.__cursor = self.__db_connection.cursor()
        self.__verify_armed_table()
        self.__verify_code_table()

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
            if data:
                data = struct.unpack('B' * FIXED_PACKET_SIZE, data)
                alert_type = data[0]
                uid = data[1]
                code = data[2:]
                self.__handle_alert(alert_type, uid, code)

    def __handle_alert(self, alert_type, uid, code):
        is_armed = self.__cursor.execute('SELECT armed FROM app_armed').fetchone()[0]
        timestamp = datetime.datetime.now()
        event_insertion_line = 'INSERT INTO app_events VALUES (?, ?, ?, ?, ?)'
        arms_log_insertion_line = 'INSERT INTO app_armslog VALUES (?, ?, ?, ?)'
        if alert_type == 0:
            self.__cursor.execute('UPDATE app_armed SET armed=0')
            self.__cursor.execute(arms_log_insertion_line, (None, 'Unarmed', timestamp, uid))
        elif alert_type == 1 and is_armed:
            self.__cursor.execute(event_insertion_line, (None, 'Breach', 'Asset has been opened while alarm was armed',
                                  timestamp, 'Critical'))
            last_inserted_id = self.__cursor.lastrowid
            # TODO: create take_snapshot method
            # take_snapshot(last_inserted_id)
            self.__mark_last_event_as_unerad()
        elif alert_type == 2 and is_armed:
            self.__cursor.execute(event_insertion_line, (None, 'Door knock',
                                  'Vibrations on the door had been detected while alarm was armed', timestamp,
                                                         'Information'))
            last_inserted_id = self.__cursor.lastrowid()
            # take_snapshot(last_inserted_id)
            self.__mark_last_event_as_unerad()
        elif alert_type == 3 and is_armed:
            inserted_code = self.__assemble_code(code)
            disarm_code = self.__cursor.execute('SELECT code FROM app_code').fetchone()[0]
            if inserted_code == disarm_code:
                self.__cursor.execute('UPDATE app_armed SET armed=0')
                self.__cursor.execute(arms_log_insertion_line, (None, 'Unarmed', timestamp, 0))
        elif alert_type == 100:
            self.__cursor.execute('UPDATE app_armed SET armed=1')
            self.__cursor.execute(arms_log_insertion_line, (None, 'Armed', timestamp, uid))

        self.__db_connection.commit()

    def __assemble_code(self, code_keystrokes_list):
        code = 0
        i = 0
        for key in code_keystrokes_list:
            code += key * (10 ** (3 - i))
            i += 1
        return code

    def __mark_last_event_as_unerad(self):
        last_event_id = self.__cursor.execute('SELECT id FROM app_events ORDER BY id DESC LIMIT 1').fetchone()[0]
        users_list = self.__cursor.execute('SELECT UID FROM app_appusers').fetchall()

        for user in users_list:
            self.__cursor.execute('INSERT INTO app_unreadevents VALUES (?, ?, ?)', (None, last_event_id, user[0]))

    def __verify_armed_table(self):
        count = self.__cursor.execute('SELECT COUNT(*) FROM app_armed').fetchone()[0]
        if count < 1:
            self.__cursor.execute('INSERT INTO app_armed VALUES(?, ?)', (None, 0))
            self.__db_connection.commit()
        elif count > 1:
            while count != 1:
                self.__cursor.execute('DELETE FROM app_armed WHERE id=(SELECT MAX(id) FROM app_armed)')
                self.__db_connection.commit()
                count = self.__cursor.execute('SELECT COUNT(*) FROM app_armed')[0]

    def __verify_code_table(self):
        count = self.__cursor.execute('SELECT COUNT(*) FROM app_code').fetchone()[0]
        if count < 1:
            self.__cursor.execute('INSERT INTO app_code VALUES(?, ?)', (None, 1234))
            self.__db_connection.commit()
        elif count > 1:
            while count != 1:
                self.__cursor.execute('DELETE FROM app_code WHERE id=(SELECT MAX(id) FROM app_code)')
                self.__db_connection.commit()
                count = self.__cursor.execute('SELECT COUNT(*) FROM app_code')[0]


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

listener = AlertsListener(listening_port=port, db_name=db_path)

listener.run_server()
