from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from .models import AppUsers, Permissions, MacToUser
from hashlib import md5
from utils import secret
from utils import rand_cookie
from utils import to_json


def login(request):
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
        return HttpResponseForbidden('Invalid username or password\nhash: {}\ndb_hash: {}'.format(password_hash, user.password_hash))

    cookie = rand_cookie()
    user.cookie = cookie
    user.save()

    user_id = user.UID
    permission = Permissions.objects.get(user=user).user_type

    if not request.session.test_cookie_worked():
        return HttpResponseBadRequest('Test cookie did not work. Please enable cookies')
    request.session.delete_test_cookie()

    raw_json = {'Access Granted': 'True', 'uid': user_id, 'user_type': permission}
    response = HttpResponse(to_json(raw_json))

    response.set_cookie('auth', cookie, expires=60*60*24*30)  # Cookie expires after a month

    return response


def register_mac(request, mac_address):
    # TODO: Check authentication first
    cookie = request.COOKIES['auth']
    user = AppUsers.objects.get(cookie=cookie)
    entry, created = MacToUser.objects.update_or_create(user=user,
                                                        defaults={'mac-address': mac_address,
                                                                  'user': user})
    entry.save()

