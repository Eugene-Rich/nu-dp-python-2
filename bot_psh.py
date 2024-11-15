from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import InlineKeyboardMarkup, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, InputFile, InlineQueryResultPhoto
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth  # or HTTPDigestAuth, or OAuth1, etc.
from requests import Session
from zeep import Client
from zeep.transports import Transport

import xml.etree.ElementTree as ET
import os
import time
import random
import sqlite3

# Блок процедур

def formtxzp(dict_zapr):  # Формирование текста запроса для WEB-сервиса. Не хочет работать через async
   
   # Функция составляет запрос для WEB-сервиса

   #lszapr = ['<Map xmlns="http://v8.1c.ru/8.1/data/core" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">',
   #         ' <pair>',
   #         '  <Key xsi:type="xs:string">ParmOtb</Key>',
   #         '  <Value xsi:type="xs:string">' + vibvidzapr + '</Value>',
   #         ' </pair>',
   #         ' <pair>',
   #         '  <Key xsi:type="xs:string">Shop</Key>',
   #         '  <Value xsi:type="xs:string">' + uinzapr + '</Value>',
   #         ' </pair>',
   #         ' <pair>',
   #         '  <Key xsi:type="xs:string">Size</Key>',
   #         '  <Value xsi:type="xs:string">' + razmshinstr + '</Value>',
   #         ' </pair>',
   #         ' <pair>',
   #         '  <Key xsi:type="xs:string">Quantity</Key>',
   #         '  <Value xsi:type="xs:string">' + kolvoshin + '</Value>',
   #         ' </pair>',
   #         ' <pair>',
   #         '  <Key xsi:type="xs:string">seazon</Key>',
   #         '  <Value xsi:type="xs:string">' + vibsezon + '</Value>',
   #         ' </pair>',
   #         '</Map>']
   
    lszapr = ['<Map xmlns="http://v8.1c.ru/8.1/data/core" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">']

    for key in dict_zapr:
        lszapr.append(' <pair>')
        lszapr.append('  <Key xsi:type="xs:string">'   + key            + '</Key>')
        lszapr.append('  <Value xsi:type="xs:string">' + dict_zapr[key] + '</Value>')
        lszapr.append(' </pair>')

    lszapr.append('</Map>')

    txtzapr = ' '.join(lszapr) 

    return(txtzapr)

def izvl_xml(xml_result): # Извлечение информации из ответа WEB-сервиса. Тоже не хочет работать через async

   # Функция возвращает два значения :
   # 1 - список реквизитов,
   # 2 - список, в котором каждый элемент, в свою очередь, также список.
   #     Это структурированный ответ WEB - сервиса. 

   strt_1C_mtd = "{http://v8.1c.ru/8.1/data/core}"
   
   rt1 = ET.fromstring(xml_result)
   
   listrekv = []

   for elem in rt1.findall(strt_1C_mtd+"column"):
      for mtd in elem:
         nametagcolomn = str.replace(mtd.tag, strt_1C_mtd, '')

         if nametagcolomn == "Name":
            if not mtd.text in listrekv:
               listrekv.append(mtd.text)

# Сбор таблицы значений реквизитов в массив

   listznr = []

   for elem in rt1.findall(strt_1C_mtd+"row"):
      teklistzn = []

      for mtd in elem:
         nametagcolomn = str.replace(mtd.tag, strt_1C_mtd, '')
         teklistzn.append(mtd.text)
   
      listznr.append(teklistzn)   

   return(listrekv, listznr)

def db_write_01(user_id, listzntov): # Запись в базу ответа сервера по товарам
        
    milliseconds = int(round(time.time() * 1000))
    uin_rec = random.randint(0, 1000000000)

    directory_path = os.path.dirname(os.path.abspath(__file__))
    dir_db = os.path.join(directory_path, "db", "bot_01.db")
    connection = sqlite3.connect(dir_db)
    cursor = connection.cursor()

    cursor.execute('INSERT INTO ServerResponse (userid, timereg, uinrequest, kolvotovaweb, nkgalle) VALUES (?, ?, ?, ?, ?)', (user_id, milliseconds, uin_rec, len(listzntov), 0))

    vsp_nomstr = 0
    for tekrec in listzntov:

        cursor.execute('INSERT INTO MultilinePart (userid, timereg, uinrequest, nomstr, naimtov, uintov, uinmag, uingor, ostatok, cena, glvnfoto, opisanie) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                       (user_id, milliseconds, uin_rec, vsp_nomstr, tekrec[0], tekrec[1], tekrec[2], tekrec[3], tekrec[4], tekrec[5], tekrec[6], tekrec[7]))
        vsp_nomstr = vsp_nomstr + 1

    connection.commit()
    connection.close()

def db_write_02(user_id, cmnd, zncom, vibuin): # Запись в базу состояния диалога
        
    milliseconds = int(round(time.time() * 1000))

    directory_path = os.path.dirname(os.path.abspath(__file__))
    dir_db = os.path.join(directory_path, "db", "bot_01.db")
    connection = sqlite3.connect(dir_db)
    cursor = connection.cursor()

    cursor.execute('INSERT INTO Users (userid, timereg, vcommand, vibzn, vib_uin) VALUES (?, ?, ?, ?, ?)', (user_id, milliseconds, cmnd, zncom, vibuin))

    connection.commit()
    connection.close()

def db_read_01(user_id): # Получение состояния пагинации и массива товаров последнего запроса

    directory_path = os.path.dirname(os.path.abspath(__file__))
    dir_db = os.path.join(directory_path, "db", "bot_01.db")

    connection = sqlite3.connect(dir_db)
    cursor = connection.cursor()

    # Выбираем запросом историю пользователя с сортировкой по убыванию времени

    cursor.execute('SELECT timereg, uinrequest, kolvotovaweb, nkgalle FROM ServerResponse WHERE userid = ? ORDER BY timereg DESC LIMIT 1', (user_id, )) 
    t_sr = cursor.fetchall()[0]

    timreg = t_sr[0]
    uinreq = t_sr[1]
    kolvotovaweb = t_sr[2]
    tekgalle = t_sr[3]

    cursor.execute('SELECT naimtov, uintov, uinmag, uingor, ostatok, cena, glvnfoto, opisanie FROM MultilinePart WHERE userid = ? AND timereg = ? AND uinrequest = ? ' +
                   ' ORDER BY timereg DESC',
                    (user_id, timreg, uinreq, )) 

    r_st = cursor.fetchall()
    
    connection.close()

    return r_st, kolvotovaweb, tekgalle, timreg, uinreq  # Массив товаров, количество товаров, текущий индекс пагинции, время и идентификатор запроса

def db_read_02(user_id): # Получение истории команд пользователя

    directory_path = os.path.dirname(os.path.abspath(__file__))
    dir_db = os.path.join(directory_path, "db", "bot_01.db")

    connection = sqlite3.connect(dir_db)
    cursor = connection.cursor()

    # Выбираем запросом историю пользователя с сортировкой по убыванию времени

    cursor.execute('SELECT timereg, vcommand, vibzn, vib_uin FROM Users WHERE userid = ? ORDER BY timereg DESC', (user_id, )) 
    u_spc = cursor.fetchall()

    connection.close()

    return u_spc

def db_read_03(user_id): # Получение телефона и имени пользователя из базы

    directory_path = os.path.dirname(os.path.abspath(__file__))
    dir_db = os.path.join(directory_path, "db", "bot_01.db")

    connection = sqlite3.connect(dir_db)
    cursor = connection.cursor()

    # Выбираем запросом историю пользователя с сортировкой по убыванию времени

    cursor.execute('SELECT timereg, vcommand, vibzn, vib_uin FROM Users WHERE userid = ? and vcommand = ? ORDER BY timereg DESC LIMIT 1', (user_id, 'Телефон',)) 
    u_tel = cursor.fetchall()

    connection.close()

    print(u_tel)

    if len(u_tel) == 0:
        return('')
    else:
        return(u_tel[2])


def db_update_01(user_id, timreg, uinreq, nkgalle):

    directory_path = os.path.dirname(os.path.abspath(__file__))
    dir_db = os.path.join(directory_path, "db", "bot_01.db")

    connection = sqlite3.connect(dir_db)
    cursor = connection.cursor()

    cursor.execute('UPDATE ServerResponse SET nkgalle = ? WHERE userid = ? AND timereg = ? AND uinrequest = ? ', (nkgalle, user_id, timreg, uinreq))
    
    connection.commit()
    connection.close()

def vivinfpg(masstov, kolvotovaweb, nkgalle, txtrnko):

    tektov = masstov[nkgalle]
    coo_tov = tektov[0] + '\n' + str(tektov[5]) + 'р. за 1 шт.'
    foto_tov = tektov[6]
    if foto_tov == '' or foto_tov == None or foto_tov == "Null":
        foto_tov = 'C:/project_bots/Pokupka_shin_bot/Gallery/nofoto.jpg'

    txtleft = "<--"
    collbleft = "pgn_left"
    txtrigth = "-->"
    collbrigth = "pgn_right"

    if nkgalle == 0:
        txtleft = " "
        collbleft = " "

    if nkgalle == kolvotovaweb - 1:
        txtrigth = " "
        collbrigth = " "

    if txtrnko == 'Картинка':
        kbka = "pic_"
    else:
        kbka = "inf_"

    inline_frame_galle = [[InlineKeyboardButton(txtleft, callback_data=collbleft), InlineKeyboardButton(str(nkgalle+1) + "/" + str(kolvotovaweb), callback_data="no"), InlineKeyboardButton(txtrigth, callback_data=collbrigth)],
                          [InlineKeyboardButton(txtrnko, callback_data=kbka+tektov[1]), InlineKeyboardButton("Купить", callback_data="sal_"+tektov[1])]
                         ]

    keyboard_galle = InlineKeyboardMarkup(inline_frame_galle)

    return(keyboard_galle, foto_tov, coo_tov)

async def button(update: Update, context): # функция-обработчик нажатий на кнопки

    user_id = update.callback_query.from_user.id
    befo_updt = dc_befo_updt.get(user_id)

    # получаем callback query из update
    query = update.callback_query
    zndata = query.data
 
    # всплывающее уведомление
    await query.answer("Выбран: " + zndata)

    print(zndata)

    name_glcom = zndata[0:4]
    print(name_glcom)

    name_comm = zndata[4:]
    print(name_comm)

    if name_glcom == 'pgn_': # Команды пагинации

        masstov, kolvotovaweb, nkgalle, timreg, uinreq, = db_read_01(user_id)

        if name_comm == 'right': # Нажата кнопка "вправо"
            if nkgalle < kolvotovaweb - 1:
                nkgalle = nkgalle + 1

        if name_comm == 'left': # Нажата кнопка "влево"
            if nkgalle > 0:
                nkgalle = nkgalle - 1

        db_update_01(user_id, timreg, uinreq, nkgalle)   # Сохраним текущее состояние пагинации     

        await query.delete_message()

        keyboard_galle, foto_tov, coo_tov = vivinfpg(masstov, kolvotovaweb, nkgalle, 'Описание')

        await befo_updt.message.reply_photo(foto_tov, caption=coo_tov, reply_markup=keyboard_galle)  


    elif name_glcom == 'gor_':  # Выбран город 

        gorod = name_comm
        gorod_uin = ''

        for tekgor in ls_city:
            if tekgor[0] == gorod:
                gorod_uin = tekgor[1]    

        db_write_02(user_id, "Город", gorod, gorod_uin)                

        # Определение инлайн клавиатуры для сезона

        inline_frame_sezon = [[InlineKeyboardButton("Лето", callback_data="sez_Лето"), InlineKeyboardButton("Зима", callback_data="sez_Зима")]]
        keyboard_sezon = InlineKeyboardMarkup(inline_frame_sezon)

        await context.bot.send_message(chat_id=update.effective_chat.id, text = 'На какой сезон вам нужны шины ?', reply_markup=keyboard_sezon)

    # Выбран сезон
    
    elif name_glcom == 'sez_':

        sezon = name_comm

        db_write_02(user_id, "Сезон", sezon, '')                

        # Определение инлайн клавиатуры для количества

        inline_frame_kolvo = [[InlineKeyboardButton("1", callback_data="ksh_1"), InlineKeyboardButton("2",  callback_data="ksh_2"),InlineKeyboardButton("3", callback_data="ksh_3"), InlineKeyboardButton("4",  callback_data="ksh_4"), InlineKeyboardButton("5", callback_data="ksh_5")]]
        keyboard_kolvo = InlineKeyboardMarkup(inline_frame_kolvo)

        await context.bot.send_message(chat_id=update.effective_chat.id, text = 'Сколько вам нужно шин ?', reply_markup=keyboard_kolvo)


    # Выбрано количество шин

    elif name_glcom == 'ksh_':
        
        kolvo = name_comm

        db_write_02(user_id, "Количество", kolvo, '')                

        await context.bot.send_photo(chat_id=update.effective_chat.id, photo='http://img.eplus54.ru/mpls/sh_razme.jpg', caption='')

    elif name_glcom == 'inf_':

        await query.delete_message()

        masstov, kolvotovaweb, nkgalle, timreg, uinreq, = db_read_01(user_id)
        
        keyboard_galle, foto_tov, coo_tov = vivinfpg(masstov, kolvotovaweb, nkgalle, 'Картинка')

        txt_tek_tov = masstov[nkgalle][7] 
        if txt_tek_tov == '' or txt_tek_tov == None:
            txt_tek_tov = 'Нет описания товара.'

        await befo_updt.message.reply_text(txt_tek_tov,  reply_markup=keyboard_galle)  

    
    elif name_glcom == 'pic_':

        await query.delete_message()

        masstov, kolvotovaweb, nkgalle, timreg, uinreq, = db_read_01(user_id)
        
        keyboard_galle, foto_tov, coo_tov = vivinfpg(masstov, kolvotovaweb, nkgalle, 'Описание')

        await befo_updt.message.reply_photo(foto_tov, caption=coo_tov, reply_markup=keyboard_galle)  

    elif name_glcom == 'sal_': # Оформление заказа в 1С. 

        # Для оформления заказа проверим, есть ли телефон и имя. Если нет, то тогда запросим

        user_tel = db_read_03(user_id)

        if user_tel == '':

            await befo_updt.message.reply_text('Сообщите свой контактный телефон') 










async def start(update: Update, _): # функция-обработчик команды /start

    await update.message.reply_text('В каком городе вы хотите купить шины:', reply_markup=keyboard_city)   #inline_keyboard

async def help(update, context): # функция-обработчик команды /help

    await update.message.reply_text("Отвечайте на вопросы вводя нужные цифры и нажимая нужные кнопки.")

async def text(update, context): # функция-обработчик текстовых сообщений

    user_id = update.message.from_user.id
    befo_updt = dc_befo_updt.get(user_id)
    if befo_updt == None:
        befo_updt = update

    # Обработка размера

    txtsoo = update.message.text
    txtsoo = txtsoo.replace('R', ' ')
    txtsoo = txtsoo.replace('/', ' ')
    txtsoo = txtsoo.replace('  ', ' ')

    db_write_02(user_id, "Размер", txtsoo, '')  

    # Подготовка запроса

    u_spc = db_read_02(user_id)

    gorod = ''
    gorod_uin = ''
    sezon = ''
    kolvo = ''
    razmer = ''

    fl_gorod = True
    fl_sezon = True
    fl_kolvo = True
    fl_razmer = True

    for tekcom in u_spc:

        if tekcom[1] == 'Город' and fl_gorod:
            gorod = tekcom[2]
            gorod_uin = tekcom[3]
            fl_gorod = False
        elif tekcom[1] == 'Сезон' and fl_sezon:
            sezon = tekcom[2]
            fl_sezon = False
        elif tekcom[1] == 'Количество' and fl_kolvo:
            kolvo = tekcom[2]
            fl_kolvo = False
        elif tekcom[1] == 'Размер' and fl_razmer:
            razmer = tekcom[2]
            fl_razmer = False

        if fl_gorod == False and fl_sezon == False and fl_kolvo == False and fl_razmer == False:
            break           


    flagws = True

    if gorod == '':
        flagws = False

    if gorod_uin == '':
        flagws = False

    if sezon == '':
        flagws = False

    if kolvo == '':
        flagws = False

    if razmer == '':
        flagws = False

    if flagws:
        await update.message.reply_text('Ожидайте. Мы подбираем нужные товары.')
    else:
        await update.message.reply_text('Заполнены не все параметры. Начните с начала.')

    # Обращение к WEB - сервису

    url = '' # тестовый урл
    ## url = ''      # 'это продуктивный url

    session = Session()
    session.auth = HTTPBasicAuth('Логин пользователя 1С', 'Пароль пользователя 1С')
    client = Client(url, transport=Transport(session=session))

    # Получаем список товаров

    vibvidzapr = 'city'
    masrazm = razmer.split()
    razmshinstr = masrazm[2] + '/' +  masrazm[0] + '/' +  masrazm[1]  #'16/195/75'
    print(razmshinstr)
    kolvoshin = str(kolvo) #'4'
    if sezon == "Лето":
        vibsezon = 'summer'
    else:
        vibsezon = 'winter'

    dict_zapr = {'ParmOtb'  : vibvidzapr,
                 'Shop'     : gorod_uin,
                 'Size'     : razmshinstr,
                 'Quantity' : kolvoshin,
                 'Seazon'   : vibsezon}
    
    txt_zapr = formtxzp(dict_zapr)

    xml_result = client.service.SeekSizeLsh(txt_zapr)

    listretov, listzntov = izvl_xml(xml_result)

    if len(listzntov) == 0: 
        await update.message.reply_text('К сожалению, такого товара нет.')
    else:

        await update.message.reply_text('Найдено товаров - ' + str(len(listzntov)))
        db_write_01(update.message.from_user.id, listzntov)
        masstov, kolvotovaweb, tekgalle, timreg, uinreq = db_read_01(user_id)
        keyboard_galle, foto_tov, coo_tov = vivinfpg(masstov, kolvotovaweb, 0, 'Описание')

        dc_befo_updt[user_id] = update

        await update.message.reply_photo(foto_tov, caption=coo_tov, reply_markup=keyboard_galle)  

def main(): # Основная процедура

    # создаем приложение и передаем в него токен
    application = Application.builder().token(TOKEN).build()
    print('Бот запущен...')

    # добавляем CallbackQueryHandler (только для inline кнопок)
    application.add_handler(CallbackQueryHandler(button))

    # добавляем обработчик команды /help
    application.add_handler(CommandHandler("help", help))

    # добавляем обработчик команды /start
    application.add_handler(CommandHandler("start", start))

    # добавляем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT, text))

    # запускаем бота (нажать Ctrl-C для остановки бота)
    application.run_polling()
    print('Бот остановлен')

# Конец блока процедур

# Основная часть ------------------------------------------------------------------------------------------------
# Подгружаем переменные окружения

load_dotenv()

TOKEN = os.getenv('TG_TOKEN') # Токен бота

##url = '' # тестовый урл
url = ''      # 'это продуктивный url

name_user_1C = ''     # Вставить имя пользователя 1С
parole_user_1C = ''   # Вставить пароль пользователя 1С

# Пока нет решения для персистентного хранения предыдущих апlейтов. Предыдущие апдейты пока храним в словаре, где ключ - user_id, а значение предыдущий апдейт.

dc_befo_updt = {}

# Запрос списка городов и магазинов

session = Session()
session.auth = HTTPBasicAuth(name_user_1C, parole_user_1C)  # bot 357753
client = Client(url, transport=Transport(session=session))

xml_result = client.service.SendCityShop('')

lsgrekv, lsgznrekv =  izvl_xml(xml_result)

ls_city = []    # Список городов - каждый элемент в свою очередь список с элементами [Город, УИН города, колво магазинов в городе, [Список магазинов]]
                # Список магазинов в свою очередь состоит из четырех списков [Наименования магазинов], [УИН магазинов], [Адреса магазинов] , [Телефоны магазинов]

# Распределяем ответ WEB-сервиса в список городов

## На первом проходе формируем вспомогательный список городов

ls_vsp = []

for tekrekv in lsgznrekv:

    tek_gor = tekrekv[3]

    if not tek_gor in ls_vsp:
        ls_vsp.append(tek_gor)


print(ls_vsp)

## На втором проходе - все остальное

for v_gor in ls_vsp:

    ls_gu = ''
    ls_vma = []
    ls_vmau = []
    ls_am = []
    ls_at = []

    for tekrekv in lsgznrekv:

        tek_gor = tekrekv[3]
        if tek_gor == v_gor:

            tek_uinmag = tekrekv[0]
            tek_mag = tekrekv[1]
            tek_uingor = tekrekv[2]  
            tek_adr = tekrekv[4]  
            tek_tel = tekrekv[5]  

            ls_gu = tek_uingor
            ls_vma.append(tek_mag)
            ls_vmau.append(tek_uinmag)
            ls_am.append(tek_adr)
            ls_at.append(tek_tel)

    ls_odn = []
    ls_odn.append(v_gor)        
    ls_odn.append(ls_gu)   
    ls_odn.append(len(ls_vma))   
    ls_odn.append(ls_vma)   
    ls_odn.append(ls_vmau)  
    ls_odn.append(ls_am)  
    ls_odn.append(ls_at)  

    ls_city.append(ls_odn) 

print(ls_city)


# Первый запрос пользователю - " В каком городе ... ?"
# Определение инлайн клавиатуры

inline_frame_city = []

for ig in ls_city:
    m1g = []
    kolmag = ig[2]
    
    nkolmag = 'магазинов'
    if kolmag == 1:
        nkolmag = 'магазин'    
    else:    
        if kolmag == 2 or kolmag == 3 or kolmag == 4:
            nkolmag = 'магазина'

    naimgor = ig[0] + ' (' + str(kolmag) + ' ' + nkolmag + ')'
    naimcolb = 'gor_'+ig[0]
    m1g.append(InlineKeyboardButton(naimgor, callback_data=naimcolb))
    inline_frame_city.append(m1g)

keyboard_city = InlineKeyboardMarkup(inline_frame_city)


if __name__ == "__main__":
    main()