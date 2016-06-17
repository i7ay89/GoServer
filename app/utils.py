from django.http import HttpResponse
import random
import json
import socket


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
