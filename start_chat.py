import time
import argparse
import subprocess

COMMAND_PYTHON = "python"
SCRIPT_SERVER = "server_select.py"
SCRIPT_CLIENT = ["client.py", "127.0.0.1", "7777"]
CLIENT_NAME_PREFIX = "client_"

if __name__ == "__main__":
    # По умолчанию запускается сервер и 2 клиента; можно указать количество клиентов
    parser = argparse.ArgumentParser()
    parser.add_argument('clients', nargs='?', default=2)
    args = parser.parse_args()
    # Старт сервера
    try:            # На Mac OS этот атрибут генерит ошибку
        server = subprocess.Popen([COMMAND_PYTHON, SCRIPT_SERVER], creationflags=subprocess.CREATE_NEW_CONSOLE)
        isWindows = True
    except AttributeError:
        isWindows = False
        server = subprocess.Popen([COMMAND_PYTHON, SCRIPT_SERVER])
    time.sleep(1.0)
    # Старт клиентов
    clients = []
    for count in range(args.clients):
        if isWindows:
            clients.append(subprocess.Popen([COMMAND_PYTHON, *SCRIPT_CLIENT, CLIENT_NAME_PREFIX + str(count+1)],
                                            creationflags=subprocess.CREATE_NEW_CONSOLE))
        else:
            clients.append(subprocess.Popen([COMMAND_PYTHON, *SCRIPT_CLIENT, CLIENT_NAME_PREFIX + str(count+1)]))
        time.sleep(1.0)
    # Ожидание прерывания для закрытия приложений
    print("Нажмите Control-C для закрытия приложений")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
    # Закрытие приложений
    #       - клиенты
    for client in clients:
        if client.poll() is None:
            client.kill()
    #       - сервер
    if server.poll() is None:
        server.kill()
    # Дело сделано
    print("Приложения завершены")
