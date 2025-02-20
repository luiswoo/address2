#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import math
import json
import urllib.request
import urllib.error
import urllib.parse
import ssl
import logging
import os
import time  # Импортируем модуль time

# Настраиваем логирование
logging.basicConfig(filename='address2.log', level=logging.DEBUG, encoding='utf-8')

# Получаем путь к директории плагина
plugin_dir = os.path.dirname(os.path.abspath(__file__))
# Добавляем директорию плагина в sys.path
sys.path.insert(0, plugin_dir)

from OsmData import OsmData, LON, LAT, TAG


class Client:
    def __init__(self, proxy=None, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'): #Измененный User-Agent
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPRedirectHandler(),
            urllib.request.HTTPHandler()
        )
        if proxy:
            self.opener.add_handler(urllib.request.ProxyHandler(proxy))
        self.opener.addheaders = [('User-agent', user_agent), ('Referer', 'https://pkk.rosreestr.ru/')]

    def request(self, url, params={}, timeout=5):
        logging.debug(f"Выполняется запрос к URL: {url} с параметрами: {params}")
        try:
            # Создаем контекст SSL, который не проверяет сертификаты
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            if params:
                data = urllib.parse.urlencode(params).encode('utf-8')
                with urllib.request.urlopen(url, data=data, timeout=timeout, context=context) as response:
                    logging.debug(f"Запрос успешно выполнен. Код ответа: {response.status}")
                    return response.read().decode('utf-8')
            else:
                with urllib.request.urlopen(url, timeout=timeout, context=context) as response:
                    logging.debug(f"Запрос успешно выполнен. Код ответа: {response.status}")
                    return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            logging.error(f"Ошибка сети при запросе к {url}: {e.reason}")
            return None
        except Exception as e:
            logging.exception(f"Неизвестная ошибка при запросе к {url}")
            return None


def main():
    logging.debug("Начало выполнения main()")
    if len(sys.argv) != 2:
        print("Необходимо указать координаты в формате 'долгота,широта'")
        return 1

    try:
        coords = sys.argv[1].split(',')
        lon = float(coords[0])
        lat = float(coords[1])
        logging.debug(f"Координаты: долгота={lon}, широта={lat}")
    except (ValueError, IndexError):
        print("Неверный формат координат. Используйте 'долгота,широта'")
        logging.error("Неверный формат координат")
        return 1

    tData = OsmData()
    httpc = Client()

    try:
        url_features = 'https://pkk.rosreestr.ru/api/features/1?text=' + coords[1] + '%20' + coords[0] + '&tolerance=4&limit=11'
        text = httpc.request(url_features)
        if text is None:
            tData.addcomment("Ошибка при запросе к API (features)")
            logging.error("Ошибка при запросе к API (features)")
            tData.write(sys.stdout)
            return 1
        data = json.loads(text)
        logging.debug(f"Данные features получены: {data}")

        if 'features' in data:
            ids = []
            for result in data['features']:
                try:
                    ids.append(result['attrs']['id'])
                except KeyError:
                    logging.debug("KeyError при получении id из features")
                    continue

            if len(ids) > 0:
                addresses = []
                for id in ids:
                    time.sleep(1) # Добавляем задержку в 1 секунду
                    url_feature = 'https://pkk.rosreestr.ru/api/features/1/' + id
                    text = httpc.request(url_feature)
                    if text is None:
                        tData.addcomment(f"Ошибка при запросе к API (feature ID: {id})")
                        logging.error(f"Ошибка при запросе к API (feature ID: {id})")
                        continue

                    data = json.loads(text)
                    logging.debug(f"Данные feature {id} получены: {data}")

                    if 'feature' in data:
                        address = {}
                        try:
                            s = data['feature']['attrs']['address'].split(',')
                            address['addr:housenumber'] = s.pop().strip()
                            address['addr:street'] = s.pop().strip()
                            address['addr:full'] = data['feature']['attrs']['address']
                            address['fixme'] = 'yes'
                        except KeyError:
                            logging.debug(f"KeyError при разборе адреса для ID: {id}")
                            continue
                        except IndexError:
                            tData.addcomment(f"Ошибка разбора адреса для ID: {id}")
                            logging.error(f"Ошибка разбора адреса для ID: {id}")
                            continue
                        try:
                            address['utilization'] = data['feature']['attrs']['util_by_doc']
                        except KeyError:
                            pass
                        addresses.append(address)
                    else:
                        tData.addcomment(f"Feature is empty for ID: {id}")
                        logging.warning(f"Feature is empty for ID: {id}")
                        continue

                count = len(addresses)
                if count == 1:
                    nodeid = tData.addnode()
                    tData.nodes[nodeid][LON] = lon
                    tData.nodes[nodeid][LAT] = lat
                    tData.nodes[nodeid][TAG] = addresses[0]
                    comment = addresses[0]['addr:street'] + ', ' + addresses[0]['addr:housenumber']
                    if addresses[0].get('utilization'):
                        comment += ' - ' + addresses[0]['utilization']
                    tData.addcomment(comment)
                    logging.info(f"Создан узел с адресом: {comment}")
                else:
                    for i in range(count):
                        angle = 2 * math.pi * i / count
                        x = lon + 0.00001 * math.cos(angle)
                        y = lat + 0.00001 * math.sin(angle)
                        nodeid = tData.addnode()
                        tData.nodes[nodeid][LON] = x
                        tData.nodes[nodeid][LAT] = y
                        tData.nodes[nodeid][TAG] = addresses[i]
                        comment = addresses[i]['addr:street'] + ', ' + addresses[i]['addr:housenumber']
                        if addresses[i].get('utilization'):
                            comment += ' - ' + addresses[i]['utilization']
                        tData.addcomment(comment)
                        logging.info(f"Создан узел с адресом: {comment} (множественный результат)")
            else:
                tData.addcomment('No feature IDs found')
                logging.warning('No feature IDs found')
        else:
            tData.addcomment('Features array is empty')
            logging.warning('Features array is empty')

    except json.JSONDecodeError as e:
        tData.addcomment(f"Ошибка разбора JSON: {e}")
        logging.exception(f"Ошибка разбора JSON: {e}")
    except Exception as e:
        tData.addcomment(f"Произошла неизвестная ошибка: {e}")
        logging.exception(f"Произошла неизвестная ошибка: {e}")

    #Добавляем комментарий, если нет данных
    if not tData.nodes and not tData.ways and not tData.relations and not tData.comments:
        tData.addcomment("No data to write - empty result")
        logging.info("Нет данных для записи - пустой результат")

    logging.debug("Запись данных в sys.stdout")
    tData.write(sys.stdout)
    logging.debug("Завершение выполнения main()")
    return 0


if __name__ == '__main__':
    sys.exit(main())
