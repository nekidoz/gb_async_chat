import ipaddress
import subprocess
import tabulate

# Константы справедливы для Mac OS. Замените, если реализация не работает на вашей ОС.
COMMAND_PING = "ping"           # Команда ping
OPTION_PING_COUNT = "-c 1"      # Количество пингов для команды ping
FILE_NULL = "/dev/null"         # Файл null


def ping(address: str) -> bool:
    return subprocess.call([COMMAND_PING, OPTION_PING_COUNT, address],
                           stdout=open(FILE_NULL), stderr=open(FILE_NULL)) == 0


def host_ping(host_list: list[str]):
    """
    Пингует хосты из переданного списка;
    пингует только корректные ipv4-адреса, доменные имена в адреса не преобразует,
    любые некорректные строки отбрасывает.
    :param host_list: список произвольных строк для обработки.
    :return: None
    """
    print("\nhost_ping()\n__________")
    for host in host_list:
        print(host, end="\t")
        try:
            ip_address = ipaddress.ip_address(host)
        except ValueError as e:
            print("Ошибка проверки ip-адреса: ", e)
        else:
            print("Узел доступен" if ping(str(ip_address)) else "Узел недоступен")


def host_range_ping(start_address: str, count: int, silent: bool = False) -> dict:
    """
    Пингует count хостов, начиная с начального адреса start_address, но не более,
    чем осталось от указанного начального адреса до конца сети, считая, что сеть - /24,
    не включая адрес сети (.0) и широковещательный (broadcast) адрес (.255)
    :param silent: если флаг имеет значение True, функция не будет выводить сообщения на экран.
    :param count: количество адресов для пинга.
    :param start_address: начальный адрес диапазона.
    :return: словарь формата {ip-адрес : <{True|False} (результат пинга)>, ...}
    """
    if not silent: print("\nhost_range_ping()\n__________")
    result = {}
    try:
        # Проверяем, адрес ли это
        ip_address = ipaddress.ip_address(start_address)
        if not silent: print("Передан ip-адрес:", ip_address)
        # Делаем сеть класса C
        ip_network = ipaddress.ip_network(str(ip_address) + "/24", strict=False)
        if not silent: print("Он принадлежит сети /24:", ip_network)
        # Выбираем все адреса после стартового
        hosts = [host for host in ip_network.hosts() if host >= ip_address]
        # Ограничиваем количество
        hosts = hosts[:count]
        if not silent: print(f"Будем пинговать {len(hosts)} адресов из {count} запрошенных")
    except ValueError as e:
        if not silent: print(f"Ошибка проверки ip-адреса ({start_address}): ", e)
    else:
        for host in hosts:
            if not silent: print(host, end="\t")
            host_result = ping(str(host))
            if not silent: print("Узел доступен" if host_result else "Узел недоступен")
            result[host] = host_result
    return result


def host_range_ping_tab(start_address: str, count: int, progress: bool = False):
    """
    Выводит результаты работы функции host_range_ping() в табличном формате.
    :param start_address: аналогично host_range_ping()
    :param count: аналогично host_range_ping()
    :param progress: True - выводу на экран данной функции будет предшествовать вывод на экран функции
    host_range_ping(silent=False); False - будет выведен только результат данной функции.
    :return:
    """
    if not progress: print("\nhost_range_ping_tab()\n__________")

    result = host_range_ping(start_address, count, not progress)
    result_dict = {"Reachable": [host for host in result.keys() if result[host]],
                   "Unreachable": [host for host in result.keys() if not result[host]]}

    if progress:
        print("\nhost_range_ping_tab()\n__________")

    print(tabulate.tabulate(result_dict, headers='keys', tablefmt='grid'))


if __name__ == "__main__":
    host_list = ["some", "www.ru", "192.168.1", "456.135.67.987", "10.10.10.1", "192.168.0.1", "127.0.0.1"]
    host_ping(host_list)
    host_range_ping("127.0.0.1", 2)
    host_range_ping_tab("127.0.0.1", 3)
