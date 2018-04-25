# -*- coding: utf-8 -*- 
# Нам понадобятся следующие модули
from bs4 import BeautifulSoup as bs
from urllib import request as req
from urllib.parse import urlparse
import re
from datetime import datetime


# Декоратор для вывода информации о затраченном времени
def time_was_spent(func):
# Обязательно пишем *args, давая понять что у декорируемой функции есть передаваемые аргументы
    def wrapper(*args):
# Запоминаем время старта функции
        start = datetime.now()
# Выполняем функцию
        func(*args)
# Выводим результат:
        print('Времени затрачено: ' + str(datetime.now() - start))

    return wrapper


# Основная функция модуля в которую передаем ссылку на сайт.
def main(url):
# Обращаемся к функции сборка всех ссылок на разделы
    all_links = get_all_links(url, 'a', 'list-group-item')
# Сохраняем домен сайта (для относительных ссылок)
    domain_url = index_url(url)
# Перебираем все ссылки на подразделы сайта
    for link in all_links:
        print(all_links[link]) #Для контроля выводим на экран относительную ссылку обрабатываемую в данный момент
        url_goods = domain_url + all_links[link] # Получаем полную ссылку на раздел каталога
        goods = get_goods(url_goods, 'div','panel-default' , 'goods.csv') # По ссылке получаем все товары подраздела

    # get_goods возвращает 0 при успешном выполнении, его мы и вернем по итогу выполнения main
    return goods

# Функция сборка товаров по ссылке
@time_was_spent
def get_goods(url, tag, prop, file):
# Сохраняем домен сайта (для относительных ссылок)
    index_urls = index_url(url)
# Создаем новый список ссылок и добавляем в него полученную ссылку
    url_list = [url]
# Создаем список в который будем передавать "тело" документа с товарами
    goods_body = []

# Проверяем есть ли в разделе пагинация
    try:
# Если есть то получаем этот элемент для разбора
        pagination = get_html_doc(url, 'ul' , 'pagination')[0].find_all('li')
    except:
        pagination = []

# Перебираем полученные элементы, ищем и добавляем ссылки на другие страницы этого  раздела
    for i in range(1,len(pagination)):
        url_list.append(index_urls + pagination[i].find('a')['href'])

# Добавляем элементы с полученных страниц раздела в список
    for url_item in url_list:
        goods_body.append(get_html_doc(url_item, tag, prop))

# Открываем файл для редактирования
    with open(file, 'a') as f:
# Вписываем строку заголовков столбцов
        f.write(str('Артикул;Наименование;Цена;Количество;\n'))
# Перебираем страницы подраздела
        for goods in goods_body:
# Получаем товары, берем нужную нам информацию
            for good in goods:
                name = good.find_all('a', class_='cat_title')[0].text
                price = good.find_all('span', class_='item_price')[0].text
                label = re.findall(r'\d+',str(good.find_all('span', class_='label-primary')[0].text))[0]
                try:
                    volume = re.findall(r'\d+', str(good.find_all('div', class_='item_property')[-1].text))[0]
                except:
                    volume = ''
# Пишем информацию в файл
                f.write(str(label + ";" + name + ";" + price + ";" + volume + ";\n"))



    return 0

# Функция сбора всех ссылок на разделы каталога
def get_all_links(url, tag, prop):
    new_links = {}
    # Вычленяем из ссылки имя домена
    url_main = index_url(url)
    # Получаем все ссылки на разделы (подразделы первого уровня)
    # Этот сайт отдает в меню только все ссылки на первый уровень и ссылки подраздела в котором находишься.
    main_links = get_catalog_links(url, tag, prop)

    # Получаем ссылки подразделов каждого раздела
    for n in main_links:
        new_links.update(get_catalog_links(url_main + main_links[n], tag, prop))

    # убираем из полного списка ссылки на разделы первого уровня
    for key in main_links:
        del(new_links[key])

    # Возвращаем полученный список
    return new_links

# Функция сбора списка разделов
def get_catalog_links(url, tag, prop):
    links = {}
    # Получаем "тело" документа содержащее ссылки на разделы (подразделы)
    all_links = get_html_doc(url, tag, prop)
    # Перебираем ссылки и добавляем только новые
    for link in all_links:
        is_in_links(link['href'], links)

    # возвращаем ссылки
    return links

# Функция добавления уникальных ссылок
def is_in_links(link, links):
    in_list = False
    # Генерируем хэш по строке ссылки, он будет ключом словаря ссылок
    hash_arg = hash(str(link))
    # Если ключ не найден в словаре тогда добавляем ссылку с этим ключом
    if hash_arg not in links:
        in_list = False
        links[hash_arg] = link
    else:
        in_list = True

    return in_list

# Функция получения доменного имени (на сайте ссылки относительные)
def index_url(url):
    url_data = urlparse(url)

    return url_data.scheme + "://" + url_data.netloc

# Функция получения "тела" документа для последующего разбора (с указанием тэга и его свойства)
def get_html_doc(url, tag, prop):
    html = req.urlopen(url)
    soup = bs(html, 'lxml')

    return soup.find_all(str(tag), class_=str(prop))
