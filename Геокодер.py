import sys
import datetime

import requests
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random

vk_session = vk_api.VkApi(
    token='31766326fece1fce5e54498ae853dc59b2d87e1daa26b91927ee5c0c273d1ff565d169c31862ce1468924')

longpoll = VkBotLongPoll(vk_session, '195389413')
vk = vk_session.get_api()


def map_type():
    return "Choose type of map"


def help():
    return "Type the place your want to see"


def get_coords(toponym_to_find):
    geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"

    geocoder_params = {
        "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
        "geocode": toponym_to_find,
        "format": "json"}

    response = requests.get(geocoder_api_server, params=geocoder_params)

    if response:
        json_response = response.json()
        toponym = json_response["response"]["GeoObjectCollection"][
            "featureMember"][0]["GeoObject"]
        toponym_coodrinates = toponym["Point"]["pos"]
        return toponym_coodrinates.split(" ")
    else:
        return None, None


def get_map(lon_lat, type, delta="0.005", point=None):
    if point is None:
        map_params = {
            "ll": lon_lat,
            "spn": ",".join([delta, delta]),
            "l": type
        }
    else:
        map_params = {
            "ll": lon_lat,
            "spn": ",".join([delta, delta]),
            "l": type,
            "pt": point
        }

    map_api_server = "http://static-maps.yandex.ru/1.x/"
    return requests.get(map_api_server, params=map_params).content


def save_geo(toponim, map_type, filename):
    try:
        lat, lon = get_coords(toponim)
        lon_lat = "{},{}".format(lat, lon)
        content = get_map(lon_lat, map_type, point=lon_lat)
        try:
            with open('static/img/photo.png', 'wb') as file:
                file.write(content)
            return filename
        except IOError as ex:
            print("Ошибка записи временного файла:", ex)
            sys.exit(2)
    except Exception as e:
        return 'No data' + str(e)


def upload_picture(album_id, group_id, filename):
    login, password = '89644685480', 'degira2020'
    vk_session = vk_api.VkApi(login, password)
    try:
        vk_session.auth(token_only=True)
    except vk_api.AuthError as error_msg:
        print(error_msg)
        return ''

    upload = vk_api.VkUpload(vk_session)
    photo = upload.photo(
        'static/img/photo.png',
        album_id='274839317',
        group_id='195389413'
    )
    vk_photo_id = "photo{}_{}".format(photo[0]['owner_id'], photo[0]['id'])
    return vk_photo_id

def main():
    flag_data, flag_help, flag_type = False, True, False
    place = ''
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW and flag_help:
            flag_data = not flag_data
            flag_help = not flag_help
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message=help(),
                             random_id=random.randint(0, 2 ** 64))

        elif event.type == VkBotEventType.MESSAGE_NEW and flag_data:
            flag_data = not flag_data
            flag_type = not flag_type
            place = event.obj.message['text']
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message=map_type(),
                             keyboard=open("keyboard.json", "r", encoding="utf-8").read(),
                             random_id=random.randint(0, 2 ** 64))
        elif event.type == VkBotEventType.MESSAGE_NEW and flag_type:
            flag_data = not flag_data
            flag_type = not flag_type
            map = event.obj.message['text']
            album_id = '195389413'
            pic_name = upload_picture(album_id, -event.obj.message['from_id'], save_geo(place, map, 'map.png'))
            vk.messages.send(user_id=event.obj.message['from_id'],
                             message='That`s {}.\n{}'.format(place, help()),
                             attachment=pic_name,
                             random_id=random.randint(0, 2 ** 64))


if __name__ == '__main__':
    main()