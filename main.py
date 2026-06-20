import os
import py7zr
import socket
import smtplib
import subprocess
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def date():
    current_date = datetime.now()
    return current_date.strftime('%Y%m%d')


def unzip(encrypted_archive, password):
    try:
        with py7zr.SevenZipFile(encrypted_archive+'.7z', mode='r', password=password) as archive:
            archive.extractall()
    except FileNotFoundError:
        print('Ошибка! Файл не найден.')
        exit()
    except Exception as e:
        print('Неизвестная ошибка: ', e)
        exit()


def file_processing(file_name):
    try:
        with open(file_name+'.txt', 'r', encoding='utf-8-sig') as file:
            lines = file.readlines()
    except Exception as e:
        print('Неудачная попытка открыть txt-файл с данными. Ошибка: ', e)
        exit()
    if file_name != 'settings_passwords':
        os.remove(file_name+'.txt')

    for i in range(len(lines)):
        lines[i] = lines[i].strip()
        lines[i] = lines[i].replace(' ', '')
        lines[i] = tuple(lines[i].split(':', 1))

    data_in_dict = {}
    result_marker_string = ''
    for key, value in lines:
        if key == 'БД':
            temp = value.split(',')
            value = ''
            for i in range(len(temp)):
                value += f'-DB {temp[i]} '

        if 'Маркер' in key:
            temp = value.split(',')
            value = ''
            for i in range(len(temp)):
                if temp[i] == '_':
                    value += f'-M{int(key[6:])} " " '
                else:
                    value += f"-M{int(key[6:])} {temp[i]} "
            result_marker_string += value
            continue
        data_in_dict.setdefault(key, value)
    data_in_dict.setdefault('Маркеры', result_marker_string)

    return data_in_dict


def find_key_in_file(file_name, search_key):
    try:
        with open(file_name+'.txt', 'r', encoding='utf-8-sig') as file:
            for line in file:
                line = line.strip()
                if line.startswith(search_key+':'):
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        return parts[1].strip()
    except Exception as e:
        print('Неудачная попытка открыть txt-файл с данными. Ошибка: ', e)
        exit()
    return None


def check_string(str_run):
    if 'None' in str_run:
        print('bat-файл не может быть сформирован. Пропущено какое-то значение.')
        print(str_run)
        exit()


def write_in_bat(str_run, run_bat):
    try:
        with open(run_bat, "w", encoding="utf-8") as file:
            file.write(str_run)
        print(f'Файл {run_bat} сформирован успешно')
    except Exception as e:
        print('Неудачная попытка открыть файл bat-файл для записи. Ошибка: ', e)
        exit()


def remove_substring_from_file(file_name, substring):
    try:
        with open(file_name, 'r', encoding='ansi') as file:
            content = file.read()
    except Exception as e:
        print('Неудачная попытка открыть log-файл. Ошибка: ', e)
    update_content = content.replace(substring, '')
    update_content = update_content.replace(substring.upper(), '')
    try:
        with open(file_name, 'w', encoding='ansi') as file:
            file.write(update_content)
    except Exception as e:
        print('Неудачная попытка перезаписать данные log-файла. Ошибка: ', e)


def send_email(from_email, to_email, path_to_the_files, smtp_server, smtp_port, smtp_user, smtp_password):
    # Настройки письма
    from_email = from_email
    subject = ''
    body = ''

    # Создание объекта сообщения
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    # Добавление текста в письмо
    msg.attach(MIMEText(body, 'plain'))
    file_path = path_to_the_files + f'NLB_r{date()}.log'

    # Читаем и прикрепляем файл к письму
    with open(file_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename=NLB_r{date()}.log',
        )
        msg.attach(part)

    server = None
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())
        print(f'Письмо отправлено успешно на почту {to_email}')
    except Exception as e:
        print(f'Ошибка при отправке письма: {e}')
    finally:
        if server:
            server.quit()


if __name__ == '__main__':
    # Выгрузка из АБИС

    # пароль для ABIS
    password_for_ABIS = find_key_in_file('settings_passwords', 'password_for_ABIS')

    # Вызов функции для распаковки архива
    file_from_ABIS = 'data_for_downloading_from_ABIS'
    unzip(file_from_ABIS, password_for_ABIS)

    # Вызов функции для преобразования данных из файла в словарь
    data_in_dict_for_dowl_from_ABIS = file_processing(file_from_ABIS)

    # Корневая папка
    path_to_the_files = data_in_dict_for_dowl_from_ABIS.get('Корневаяпапка')

    # Создание строки для выгрузки из АБИС
    str_run1 = (
        fr"abstract_utility.exe --user={data_in_dict_for_dowl_from_ABIS.get('Логин')} "
        fr"--password=******* --host={data_in_dict_for_dowl_from_ABIS.get('Названиебд')} "
        fr"--output={path_to_the_files}output_{date()}.mrc "
        fr"--log={path_to_the_files}process.log"
    )

    # проверка на правильное формирование строки
    check_string(str_run1)
    print(str_run1)

    # запись в bat-файл строку str_num
    run_bat = path_to_the_files + 'backup1.bat'
    write_in_bat(str_run1, run_bat)

    process = subprocess.Popen(run_bat, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW)
    process.wait()
    if process.returncode == 0:
        print('Бат файл выгрузки успешно завершился')
    else:
        print(f'Ошибка бат файла выгрузки. Код завершения: {process.returncode}')
    os.remove(run_bat)

    file_path = path_to_the_files + f'NLB_r{date()}.log'
    substring1 = 'testexample'
    remove_substring_from_file(file_path, substring1)

    # Загрузка в СЭК

    # Пароль для SEC
    password_for_SEC = find_key_in_file('settings_passwords', 'password_for_SEC')

    # Вызов функции для распаковки архива
    file_to_SEC = 'data_for_loading_to_SEC'
    unzip(file_to_SEC, password_for_SEC)

    # Вызов функции для преобразования данных из файла в словарь
    data_in_dict_for_load_to_SEC = file_processing(file_to_SEC)

    # Корневая папка
    path_to_the_files = data_in_dict_for_load_to_SEC.get('Корневаяпапка')

    # Создание строки для загрузки в СЭК
    str_run2 = (
        fr"abstract_utility.exe --user={data_in_dict_for_load_to_SEC.get('Логин')} "
        fr"--password=******* --host={data_in_dict_for_load_to_SEC.get('Названиебд')} "
        fr"--output={path_to_the_files}output_{date()}.mrc "
        fr"--log={path_to_the_files}process.log"
    )

    # проверка на правильное формирование строки
    check_string(str_run2)

    # запись в bat-файл строку str_num
    run_bat = path_to_the_files + 'backup2.bat'
    write_in_bat(str_run2, run_bat)

    process = subprocess.Popen(run_bat, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW)
    process.wait()
    if process.returncode == 0:
        print('Бат файл загрузки успешно завершился')
    else:
        print(f'Ошибка бат файла загрузки. Код завершения: {process.returncode}')
    os.remove(run_bat)

    # Пароль и логин для удаления из log-файла
    file_path = path_to_the_files + f'NLB_r{date()}.log'
    substring2 = 'testexample'
    remove_substring_from_file(file_path, substring2)


    # Отправка письма

    # Вызов функции для сохранения всех паролей в архив
    data_in_dict_for_send_email = file_processing('settings_passwords')

    # Настройка прокси-сервера
    proxy_host = '://example.com'
    proxy_port = '://example.com'
    proxy_type = socks.HTTP
    proxy_user = data_in_dict_for_send_email.get('proxy_user')
    proxy_password = data_in_dict_for_send_email.get('proxy_password')

    # Настройки для SMTP-сервера
    server = '://example.com'
    port = '://example.com'
    user = data_in_dict_for_send_email.get('your_email')
    password = data_in_dict_for_send_email.get('email_password')

    # Настройка прокси для socket
    try:
        socks.setdefaultproxy(proxy_type, proxy_host, proxy_port, username=proxy_user, password=proxy_password)
        socket.socket = socks.socksocket
        print('HTTP прокси настроен успешно')
    except Exception as e:
        print(f'Ошибка настройки прокси: {e}')

    try:
        with open('mails_to_send.txt', 'r') as file:
            emails = file.readlines()
            for email in emails:
                clear_email = email.strip()
                if clear_email:
                    send_email(user, clear_email, path_to_the_files, server, port, user, password)
    except Exception as e:
        print(f'Ошибка при чтении файла: {e}')
