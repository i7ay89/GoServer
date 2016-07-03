from django.http import HttpResponse
from hashlib import md5
import random
import json
import socket
import os
import subprocess
import re
import time

cookie_length = 25
secret = 'So2>QmjNktdi^u{}ujxAo3^dN'
IMAGE_PATH = '/home/user/Pictures/'    # TODO: change path


def rand_cookie():
    random.seed()
    valid_char = False
    cookie = ''

    for i in xrange(cookie_length):
        while not valid_char:
            character = random.randint(33, 126)
            if not (character in xrange(44, 48) or character in [39, 58, 59, 96]):
                valid_char = True
        valid_char = False

        cookie += chr(character)

    return cookie


def get_password_hash(username, password):
    hash_creator = md5()
    hash_creator.update(username)
    hash_creator.update(password)
    hash_creator.update(secret)
    return hash_creator.hexdigest()


def to_json(json_data_dictionary):
    return json.dumps(json_data_dictionary, indent=4, separators=(',', ': '))


def return_success():
    return HttpResponse(to_json({'Success': 1}))


def get_self_address():
    test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_socket.connect(('8.8.8.8', 80))

    self_address = test_socket.getsockname()[0]

    test_socket.close()

    return self_address


class HttpResponseServerError(HttpResponse):
    status_code = 500


def validate_mac_format(mac_address):
    mac_pattern = '(([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2})'
    return re.match(mac_pattern, mac_address)

def get_macs_on_nat():
    nmap_execution = 'nmap -sP {}/24 > /dev/null'.format(get_self_address())
    os.system(nmap_execution)
    arp_command = subprocess.Popen(['arp', '-a'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)
    output = arp_command.communicate()[0]
    mac_pattern = '(([0-9a-f]{2}:){5}[0-9a-f]{2})'
    results = re.findall(mac_pattern, output, re.I)
    macs = [result[0] for result in results]
    return macs
