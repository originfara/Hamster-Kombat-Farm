import requests as req
import json
import time
import random
import os
import platform
import threading

auto_clicker_enabled = False  # Флаг автокликера
main_thread_running = False  # Флаг основного процесса
collect_time_range = (3600, 10800)  # Диапазон времени сбора по умолчанию (1-3 часа)

# Событие для синхронизации вывода
print_lock = threading.Lock()

def read_auth_token(file_path='token.txt'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            auth = file.read().strip()
            if auth:
                return auth
    auth = input("Введите Init токен: ")
    with open(file_path, 'w') as file:
        file.write(auth)
    return auth

def clear_console():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def get_proxies(file_path='proxy.txt'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = file.read().strip().split(':')
            if len(data) == 5:
                protocol, ip, port, user, password = data
                if protocol.lower() == "https":
                    return {
                        "http": f"http://{user}:{password}@{ip}:{port}",
                        "https": f"https://{user}:{password}@{ip}:{port}"
                    }
                elif protocol.lower() == "socks5":
                    return {
                        "http": f"socks5://{user}:{password}@{ip}:{port}",
                        "https": f"socks5://{user}:{password}@{ip}:{port}"
                    }
    return {}

def save_proxies(protocol, ip, port, user, password, file_path='proxy.txt'):
    with open(file_path, 'w') as file:
        file.write(f"{protocol}:{ip}:{port}:{user}:{password}")

def verify_proxy(proxies):
    try:
        response = req.get('https://httpbin.org/ip', proxies=proxies)
        with print_lock:
            print(f"\033[92mПроверка прокси:\033[0m")
            print(f"Ваш IP адрес: {response.json()['origin']}")
    except req.exceptions.ProxyError as e:
        with print_lock:
            print(f"\033[91mПроблема с подключением через прокси:\033[0m {e}")
    except req.exceptions.SSLError as e:
        with print_lock:
            print(f"\033[91mSSL ошибка:\033[0m {e}")
    except Exception as e:
        with print_lock:
            print(f"\033[91mОшибка:\033[0m {e}")

def auto_clicker(auth, proxies):
    head = {
        'Authorization': auth,
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.156 Mobile Safari/537.36'
    }
    while auto_clicker_enabled:
        try:
            post_id = req.post('https://api.hamsterkombat.io/clicker/tap', headers=head, proxies=proxies, json={
                "availableTaps": 7994, "count": 1, "timestamp": 1718457917})
            post_id.raise_for_status()
            with print_lock:
                print("\033[94mКлик + 1\033[0m")
            time.sleep(5)
        except req.exceptions.RequestException as e:
            with print_lock:
                print(f"\033[91mОшибка запроса автокликера:\033[0m {e}")

def main(auth, proxies):
    global main_thread_running
    if main_thread_running:
        with print_lock:
            print("\033[93mОсновной процесс уже запущен.\033[0m")
        return

    main_thread_running = True
    head = {
        'Authorization': auth.encode('utf-8'),
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 9; SM-G960F Build/PPR1.180610.011) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.156 Mobile Safari/537.36'
    }
    try:
        verify_proxy(proxies)
        resp = req.post('https://api.hamsterkombat.io/auth/me-telegram', headers=head, proxies=proxies)
        resp.raise_for_status()
        data = resp.json()
        username = data.get('telegramUser', {}).get('firstName', 0)

        balanceGet = req.post('https://api.hamsterkombatgame.io/interlude/sync', headers=head, proxies=proxies, json={
            "availableTaps": 7994, "count": 1, "timestamp": 1718457917})
        balanceGet.raise_for_status()
        dataBalance = balanceGet.json()
        balance = dataBalance.get('interludeUser', {}).get('balanceDiamonds', 0)
        with print_lock:
            print(f"\033[96m{username}\033[0m")
            print(f"\033[92mБаланс:\033[0m {balance}")

        time.sleep(2)
        with print_lock:
            print("\033[92mЗапущено...\033[0m")

        while main_thread_running:
            try:
                post_id = req.post('https://api.hamsterkombatgame.io/interlude/sync', headers=head, proxies=proxies)
                post_id.raise_for_status()
                collect = post_id.json()
                claim = collect.get('interludeUser', {}).get('balanceDiamonds', 0)
                with print_lock:
                    print(f"\033[92mБаланс:\033[0m {claim:.2f}")

                sleep_time = random.randint(*collect_time_range)  # Используем выбранный диапазон времени
                start_time = time.time()
                while time.time() - start_time < sleep_time:
                    remaining_time = sleep_time - (time.time() - start_time)
                    hours, remainder = divmod(int(remaining_time), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    with print_lock:
                        print(f"\r\033[93mСледующий сбор через {hours} часов, {minutes} минут, {seconds} секунд.\033[0m     ", end='')
                    time.sleep(1)  # Обновление каждую секунду

                # После завершения ожидания удалить строку с информацией о следующем сборе
                with print_lock:
                    print("\r" + " " * 60 + "\r", end='')

            except req.exceptions.RequestException as e:
                with print_lock:
                    print(f"\033[91mОшибка запроса:\033[0m {e}")

    except req.exceptions.ProxyError as e:
        with print_lock:
            print(f"\033[91mПроблема с подключением через прокси:\033[0m {e}")
    except req.exceptions.SSLError as e:
        with print_lock:
            print(f"\033[91mSSL ошибка:\033[0m {e}")
    except req.exceptions.RequestException as e:
        with print_lock:
            print(f"\033[91mОшибка запроса:\033[0m {e}")
    finally:
        main_thread_running = False

def settings():
    with print_lock:
        print("\033[94mВведите данные прокси:\033[0m")
    protocol = input("Протокол (https/socks5): ").strip()
    ip = input("IP: ").strip()
    port = input("Port: ").strip()
    user = input("Username: ").strip()
    password = input("Password: ").strip()
    save_proxies(protocol, ip, port, user, password)
    with print_lock:
        print("\033[92mНастройки прокси сохранены.\033[0m")

def toggle_auto_clicker():
    global auto_clicker_enabled
    auto_clicker_enabled = not auto_clicker_enabled
    status = "включён" if auto_clicker_enabled else "выключен"
    with print_lock:
        print(f"\033[94mАвтокликер {status}\033[0m")

def set_collect_time_range():
    global collect_time_range
    print("\033[94mВыберите диапазон времени сбора:\033[0m")
    print("1. От 1 часа до 3 часов")
    print("2. От 30 минут до 1,5 часов")
    print("3. От 15 минут до 30 минут")
    choice = input("Введите номер опции: ")
    if choice == '1':
        collect_time_range = (3600, 10800)  # 1 час = 3600 секунд, 3 часа = 10800 секунд
    elif choice == '2':
        collect_time_range = (1800, 5400)   # 30 минут = 1800 секунд, 1,5 часа = 5400 секунд
    elif choice == '3':
        collect_time_range = (900, 1800)    # 15 минут = 900 секунд, 30 минут = 1800 секунд
    else:
        print("\033[91mНеверный выбор. Установлен диапазон по умолчанию (1-3 часа).\033[0m")
        collect_time_range = (3600, 10800)

def menu():
    proxies = get_proxies()
    auth = read_auth_token()

    while True:
        clear_console()
        print("\033[95mКанал разработчика новый софт и обновления: https://t.me/tapsoftof\033[0m")
        print("\033[96mver 0.1Beta\033[0m")
        print("\033[93mМеню:\033[0m")
        print("1. \033[92mСтарт\033[0m")
        print(f"2. Автокликер (Не работает!) \033[94m{'включён' if auto_clicker_enabled else 'выключен'}\033[0m")
        print("3. \033[94mПрокси\033[0m")
        print("4. \033[94mУстановить диапазон времени сбора\033[0m")
        print("5. \033[91mВыход\033[0m")
        choice = input("Выберите опцию: ")

        if choice == '1':
            threading.Thread(target=main, args=(auth, proxies)).start()
            if auto_clicker_enabled:
                threading.Thread(target=auto_clicker, args=(auth, proxies)).start()
        elif choice == '2':
            toggle_auto_clicker()
            input("Нажмите Enter для возврата в меню...")
        elif choice == '3':
            settings()
            proxies = get_proxies()
            input("Нажмите Enter для возврата в меню...")
        elif choice == '4':
            set_collect_time_range()
            input("Нажмите Enter для возврата в меню...")
        elif choice == '5':
            print("Выход...")
            os._exit(0)
        else:
            print("\033[91mНеверный выбор. Пожалуйста, выберите снова.\033[0m")

def get_user_agent():
    response = req.get('https://httpbin.org/user-agent')
    return response.json()['user-agent']

if __name__ == '__main__':
    menu()
