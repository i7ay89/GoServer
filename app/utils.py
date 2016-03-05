__author__ = 'user'

from django.http import HttpResponse
import random
import json


cookie_length = 25
secret = 'So2>QmjNktdi^u{}ujxAo3^dN'

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
