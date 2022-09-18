# Задание 1
print("\nЗадание 1")
development = "разработка"
socket = "сокет"
decorator = "декоратор"
print(type(development), development)
print(type(socket), socket)
print(type(decorator), decorator)
# Преобразовано с помощью https://www.branah.com/unicode-converter в кодировку UTF-16
development_unicode = "\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430"
socket_unicode = "\u0441\u043e\u043a\u0435\u0442"
decorator_unicode = "\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440"
print(type(development_unicode), development_unicode)
print(type(socket_unicode), socket_unicode)
print(type(decorator_unicode), decorator_unicode)

# Задание 2
print("\nЗадание 2")
class_bytes = b"class"
function_bytes = b"function"
method_bytes = b"method"
print(type(class_bytes), len(class_bytes), class_bytes)
print(type(function_bytes), len(function_bytes), function_bytes)
print(type(method_bytes), len(method_bytes), method_bytes)

# Задание 3
print("\nЗадание 3")
attribute_bytes = b"attribute"
print(type(attribute_bytes), len(attribute_bytes), attribute_bytes)
# Невозможно записать в байтовом типе: SyntaxError: bytes can only contain ASCII literal characters
# class_bytes = b"класс"
# Невозможно записать в байтовом типе: SyntaxError: bytes can only contain ASCII literal characters
# function_bytes = b"функция"
type_bytes = b"type"
print(type(type_bytes), len(type_bytes), type_bytes)

# Задание 4
print("\nЗадание 4")
development = "разработка"
administration = "администрирование"
protocol = "protocol"
standard = "standard"
print(development.encode('utf8'), development.encode('utf8').decode('utf8'))
print(administration.encode('utf8'), administration.encode('utf8').decode('utf8'))
print(protocol.encode('utf8'), protocol.encode('utf8').decode('utf8'))
print(standard.encode('utf8'), standard.encode('utf8').decode('utf8'))

# Задание 5
print("\nЗадание 5")
import subprocess
for site in ['yandex.ru', 'youtube.com']:
    args = ['ping', site]
    with subprocess.Popen(args, stdout=subprocess.PIPE) as subprocess_ping:
        for index, line in enumerate(subprocess_ping.stdout):
            print(line.decode('cp1251'), end='')
            if index >= 5:
                break

# Задание 6
print("\nЗадание 6")
import locale
print(locale.getpreferredencoding())
with open('test_file.txt', encoding='utf-8') as text_file:
    for line in text_file:
        print(line, end='')

