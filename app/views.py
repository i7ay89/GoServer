from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from .models import AppUsers, Permissions, MacToUser, UnreadEvents, Events, Armed
import struct
from utils import *


def login(request):
    if not is_android_client(request):
        return HttpResponseForbidden('Not an android client')
    if not request.method == 'POST':
        return HttpResponseBadRequest('Not a POST-login-form')

    username = request.POST.get('name', None)
    password = request.POST.get('password', None)

    if not username or not password:
        return HttpResponseBadRequest('Username or password is missing')

    password_hash = get_password_hash(username, password)
    user = AppUsers.objects.get(name=username)
    if password_hash != user.password_hash:
        return HttpResponseForbidden('Invalid username or password')

    cookie = rand_cookie()
    user.cookie = cookie
    user.save()

    user_id = user.UID
    permission = Permissions.objects.get(user=user).user_type

    raw_json = {'Access Granted': 'True', 'uid': user_id, 'user_type': permission}
    response = HttpResponse(to_json(raw_json))

    response.set_cookie('auth', cookie, expires=60*60*24*30)  # Cookie expires after a month

    return response


def create_new_user(request):
    valid, response = is_request_valid(request, method='POST')
    if not valid:
        return response

    cookie = request.COOKIES.get('auth', None)
    user_object = AppUsers.objects.filter(cookie=cookie)[0]
    permission_object = Permissions.objects.filter(user=user_object)[0]

    user_type = permission_object.user_type
    if user_type == 'Admin':
        if add_user(request):
            return return_success()
        return HttpResponseBadRequest('One of the fields is missing')
    return HttpResponseForbidden('User "{}" is not authorized to add new users'.format(user_object.name))


def add_user(request):
    username = request.POST.get('name', None)
    password = request.POST.get('password', None)
    permission = request.POST.get('permission', None)

    if username and password and permission:
        uids = sorted(AppUsers.objects.values_list('UID', flat=True).all())
        new_uid = uids[-1] + 1
        new_user = AppUsers(UID=new_uid, name=username, password_hash=get_password_hash(username, password))
        new_user.save()

        Permissions(user=new_user, user_type=permission).save()
        return True
    return False


def remove_user(request):
    valid, response = is_request_valid(request, method='POST')
    if not valid:
        return response

    cookie = request.COOKIES.get('auth', None)
    user_object = AppUsers.objects.filter(cookie=cookie)[0]
    permission_object = Permissions.objects.filter(user=user_object)[0]

    user_type = permission_object.user_type

    uid_to_delete = int(request.POST.get('uid', None))

    if user_type != 'Admin':
        return HttpResponseForbidden('User "{}" is not authorized to add new users'.format(user_object.name))

    user_object_to_remove = AppUsers.objects.filter(UID=uid_to_delete)
    if user_object_to_remove:
        user_object_to_remove = user_object_to_remove[0]
    else:
        return HttpResponseBadRequest('No such UID')
    user_object_to_remove.delete()
    return_success()


def get_all_users(request):
    valid, response = is_request_valid(request, method='GET')
    if not valid:
        return response

    users_list = []
    user_object_list = AppUsers.objects.all()
    for user_object in user_object_list:
        users_list.append({'UID': user_object.UID, 'Name': user_object.name})

    response = to_json({'Users': users_list})
    return HttpResponse(response)


def get_my_permission(request):
    valid, response = is_request_valid(request, method='GET')
    if not valid:
        return response

    cookie = request.COOKIES.get('auth', None)
    user_object = AppUsers.objects.filter(cookie=cookie)[0]
    permission_object = Permissions.objects.filter(user=user_object)[0]

    user_type = permission_object.user_type
    response = to_json({'UID': user_object.UID, 'Permission': user_type})
    return HttpResponse(response)


def register_mac(request):
    valid, response = is_request_valid(request, method='POST')
    if not valid:
        return response

    cookie = request.COOKIES.get('auth', None)

    mac_address = request.POST.get('mac', None)
    if not validate_mac_format(mac_address):
        return HttpResponseBadRequest('Incorrect MAC format')
    user = AppUsers.objects.filter(cookie=cookie)[0]
    entry, created = MacToUser.objects.update_or_create(user=user,
                                                        defaults={'mac-address': mac_address.lower(),
                                                                  'user': user})
    entry.save()
    return return_success()


def sync(request):
    valid, response = is_request_valid(request, method='GET')
    if not valid:
        return response

    cookie = request.COOKIES.get('auth', None)
    user_object = AppUsers.objects.filter(cookie=cookie)[0]

    event_objects = UnreadEvents.objects.filter(user=user_object)
    json_response = []
    for single_event in event_objects:
        json_response.append(create_event_response(single_event.event))

    event_objects.delete()
    return HttpResponse(to_json({'events': json_response}))


def get_recent_events(request):
    valid, response = is_request_valid(request, method='GET')
    if not valid:
        return response

    events = Events.objects.all()
    if len(events) > 10:
        events = events[-10:]

    json_response = []
    for event in events:
        json_response.append(create_event_response(event))

    return HttpResponse(to_json({'events': json_response}))


def get_snapshot(request, image_id):
    valid, response = is_request_valid(request, method='GET')
    if not valid:
        return response

    try:
        img_file = open(IMAGE_PATH + image_id + '.png', 'rb')
        img = img_file.read()
        img_file.close()
        response = HttpResponse(img, content_type='image/jpeg')
    except:
        response = HttpResponseBadRequest()
    finally:
        return response


def arm(request):
    valid, response = is_request_valid(request, method='POST')
    if not valid:
        return response

    cookie = request.COOKIES.get('auth', None)
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


def disarm(request):
    valid, response = is_request_valid(request, method='POST')
    if not valid:
        return response

    cookie = request.COOKIES.get('auth', None)
    uid = AppUsers.objects.filter(cookie=cookie)[0].UID
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
    valid, response = is_request_valid(request)
    if not valid:
        return response

    status = Armed.objects.last().armed
    if status:
        response = to_json({'status': 'Armed'})
    else:
        response = to_json({'status': 'Unarmed'})
    return HttpResponse(response)


def whos_home(request):
    valid, response = is_request_valid(request)
    if not valid:
        return response
    macs_at_home = get_macs_on_nat()
    all_mac_table_objects = MacToUser.objects.all()
    users_at_home = []
    for mac_object in all_mac_table_objects:
        if mac_object.mac_address in macs_at_home:
            users_at_home.append({'Name': mac_object.user.name, 'UID': mac_object.user.UID})

    return HttpResponse(to_json({'Users': users_at_home}))


def is_android_client(request):
    return 'android' in request.META['HTTP_USER_AGENT'].lower()


def check_user_authentication(cookie):
    if not cookie:
        return False, 'No cookie set'

    cookies_exists = AppUsers.objects.filter(cookie=cookie)[0]

    if cookies_exists:
        return True, ''

    return False, 'Cookie is either invalid or expired'


def create_event_response(event_object):
    date_struct = {'year': event_object.timestamp.year, 'month': event_object.timestamp.month,
                   'day': event_object.timestamp.day, 'hour': event_object.timestamp.hour,
                   'minute': event_object.timestamp.minute, 'second': event_object.timestamp.second}
    raw_json = {'id': event_object.id, 'type': event_object.event_type, 'description': event_object.description,
                'timestamp': date_struct, 'severity': event_object.severity}

    return raw_json


def is_request_valid(request, method='GET'):
    #if not is_android_client(request):
    #    return False, HttpResponseForbidden('Not an android client')
    if method == 'GET' and not request.method == 'GET':
        return False, HttpResponseBadRequest('Not a GET request')
    elif method == 'POST' and not request.method == 'POST':
        return False, HttpResponseBadRequest('Not a POST form')
    cookie = request.COOKIES.get('auth', None)
    user_is_authenticated, reason = check_user_authentication(cookie)
    if not user_is_authenticated:
        return False, HttpResponseForbidden(reason)
    return True, None
