from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from .models import AppUsers, Permissions, MacToUser, UnreadEvents, Events, Armed
from hashlib import md5
import socket
import struct
from utils import secret, rand_cookie, to_json, return_success, IMAGE_PATH, get_self_address, HttpResponseServerError


def login(request):
    #if not is_android_client(request):
    #   return HttpResponseForbidden('Not an android client')
    if not request.method == 'POST':
        return HttpResponseBadRequest('Not a POST-login-form')

    username = request.POST.get('name', None)
    password = request.POST.get('password', None)

    if not username or not password:
        return HttpResponseBadRequest('Username or password is missing')

    hash_creator = md5()
    hash_creator.update(username)
    hash_creator.update(password)
    hash_creator.update(secret)

    password_hash = hash_creator.hexdigest()
    user = AppUsers.objects.get(name=username)
    if password_hash != user.password_hash:
        return HttpResponseForbidden('Invalid username or password\nhash: {}\ndb_hash: {}'.format(password_hash,
                                                                                                  user.password_hash))

    cookie = rand_cookie()
    user.cookie = cookie
    user.save()

    user_id = user.UID
    permission = Permissions.objects.get(user=user).user_type

    #if not request.session.test_cookie_worked():
    #    return HttpResponseBadRequest('Test cookie did not work. Please enable cookies')
    #request.session.delete_test_cookie()

    raw_json = {'Access Granted': 'True', 'uid': user_id, 'user_type': permission}
    response = HttpResponse(to_json(raw_json))

    response.set_cookie('auth', cookie, expires=60*60*24*30)  # Cookie expires after a month

    return response


def create_new_user(request):
    if not is_android_client(request):
        return HttpResponseForbidden('Not an android client')
    if not request.method == 'POST':
        return HttpResponseBadRequest('Not a POST-login-form')

    cookie = request.COOKIES['auth']
    user_is_authenticated, reason = check_user_authentication(cookie)
    if not user_is_authenticated:
        return HttpResponseForbidden(reason)

    user_object = AppUsers.objects.filter(cookie=cookie)[0]
    permission_object = Permissions.filter(user=user_object)[0]

    user_type = permission_object.user_type
    if user_type == 'Admin':
        if add_user(request):
            return return_success()
        return HttpResponseBadRequest('One of the fileds is missing')
    return HttpResponseForbidden('User "{}" is not authorized to add new users'.format(user_object.name))


def add_user(request):
    if not is_android_client(request):
        return HttpResponseForbidden('Not an android client')
    username = request.POST.get('name', None)
    password = request.POST.get('password', None)
    permission = request.POST.get('permission', None)

    if username and password and permission:
        uids = sorted(AppUsers.objects.values_list('UID', flat=True).all())
        new_uid = uids[-1] + 1
        new_user = AppUsers(UID=new_uid, name=username, password=password)
        new_user.save()

        Permissions(user=new_user, user_type=permission).save()
        return True
    return False


def register_mac(request):
    if not is_android_client(request):
        return HttpResponseForbidden('Not an android client')
    if not request.method == 'POST':
        return HttpResponseBadRequest('Not a POST-login-form')
    cookie = request.COOKIES['auth']
    user_is_authenticated, reason = check_user_authentication(cookie)
    if not user_is_authenticated:
        return HttpResponseForbidden(reason)

    mac_address = request.POST.get('mac', None)
    user = AppUsers.objects.filter(cookie=cookie)[0]
    entry, created = MacToUser.objects.update_or_create(user=user,
                                                        defaults={'mac-address': mac_address.upper(),
                                                                  'user': user})
    entry.save()
    return return_success()


def sync(request):
    #if not is_android_client(request):
    #   return HttpResponseForbidden('Not an android client')
    if not request.method == 'GET':
        return HttpResponseBadRequest('Not a GET-sync-request')
  #  cookie = '4#2HU^Ke~x^88Y)gukF*v#&Z('           #  User for debug. delete afterwards
    cookie = request.COOKIES.get('auth', None)
    user_is_authenticated, reason = check_user_authentication(cookie)
    if not user_is_authenticated:
        return HttpResponseForbidden(reason)

    user_object = AppUsers.objects.filter(cookie=cookie)[0]

    event_objects = UnreadEvents.objects.filter(user=user_object)
    json_response = []
    for single_event in event_objects:
        json_response.append(create_event_response(single_event.event))

    event_objects.delete()
    return HttpResponse(to_json({'events': json_response}))


def get_last_events(request):
    '''
    if not is_android_client(request):
        return HttpResponseForbidden('Not an android client')
    if not request.method == 'GET':
        return HttpResponseBadRequest('Not a GET-sync-request')
        #  cookie = '4#2HU^Ke~x^88Y)gukF*v#&Z('           #  User for debug. delete afterwards
    cookie = request.COOKIES.get('auth', None)
    user_is_authenticated, reason = check_user_authentication(cookie)
    if not user_is_authenticated:
        return HttpResponseForbidden(reason)
    '''
    events = Events.objects.all()
    if len(events) > 10:
        events = events[-10:]

    json_response = []
    for event in events:
        json_response.append(create_event_response(event))

    return HttpResponse(to_json({'events': json_response}))


def get_snapshot(request, image_id):
    '''
    if not is_android_client(request):
        return HttpResponseForbidden('Not an android client')
    if not request.method == 'GET':
        return HttpResponseBadRequest('Not a GET-sync-request')
        #  cookie = '4#2HU^Ke~x^88Y)gukF*v#&Z('           #  User for debug. delete afterwards
    cookie = request.COOKIES.get('auth', None)
    user_is_authenticated, reason = check_user_authentication(cookie)
    if not user_is_authenticated:
        return HttpResponseForbidden(reason)
    '''
    try:
        img_file = open(IMAGE_PATH + image_id + '.png', 'rb')
        img = img_file.read()
        img_file.close()
        response = HttpResponse(img, content_type='image/jpeg')
    except:
        response = HttpResponseBadRequest()
    finally:
        return response


def is_android_client(request):
    return 'android' in request.META['HTTP_USER_AGENT']


def check_user_authentication(cookie):
    if not cookie:
        return False, 'No cookie set'

    cookies_exists = AppUsers.objects.filter(cookie=cookie)[0]

    if cookies_exists:
        return True, ''

    return False, 'Cookie is either invalid or expired'


def arm(request):
    '''
    if not is_android_client(request):
        return HttpResponseForbidden('Not an android client')
    '''
    if not request.method == 'POST':
        return HttpResponseBadRequest('Not a POST request')

    cookie = request.COOKIES['auth']
    user_is_authenticated, reason = check_user_authentication(cookie)
    if not user_is_authenticated:
        return HttpResponseForbidden(reason)

    uid = AppUsers.objects.filter(cookie=cookie)[0].UID
    try:
        sync_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sync_address = (get_self_address(), 9898)

        data_to_send = struct.pack('BB', 100, uid)

        sync_socket.sendto(data_to_send, sync_address)
        sync_socket.close()
    except Exception as e:
        return HttpResponseServerError()
    return return_success()


def unarm(request):
    if not is_android_client(request):
        return HttpResponseForbidden('Not an android client')
    if not request.method == 'POST':
        return HttpResponseBadRequest('Not a POST request')

    cookie = request.COOKIES['auth']
    user_is_authenticated, reason = check_user_authentication(cookie)
    if not user_is_authenticated:
        return HttpResponseForbidden(reason)

    uid = AppUsers.objects.filter(cookie=cookie)[0]
    try:
        sync_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sync_address = (get_self_address(), 9898)

        data_to_send = struct.pack('BB', 0, uid)

        sync_socket.sendto(data_to_send, sync_address)
        sync_socket.close()
    except:
        return HttpResponseServerError()
    return return_success()


def get_status(request):
#    if not is_android_client(request):
#        return HttpResponseForbidden('Not an android client')
    if not request.method == 'GET':
        return HttpResponseBadRequest('Not a GET request')
    status = Armed.objects.last().armed
    if status:
        response = to_json({'status': 'Armed'})
    else:
        response = to_json({'status': 'Unarmed'})
    return HttpResponse(response)


def create_event_response(event_object):
    date_struct = {'year': event_object.timestamp.year, 'month': event_object.timestamp.month,
                   'day': event_object.timestamp.day, 'hour': event_object.timestamp.hour,
                   'minute': event_object.timestamp.minute, 'second': event_object.timestamp.second}
    raw_json = {'id': event_object.id, 'type': event_object.event_type, 'description': event_object.description,
                'timestamp': date_struct, 'severity': event_object.severity}

    return raw_json
