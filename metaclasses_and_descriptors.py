import socket as sock
import dis
from collections.abc import Iterator, Iterable
from dis import Instruction


def exist_method_calls(instructions: Iterator[Instruction], methods: Iterable) -> bool:
    try:
        # ищем загрузку переданных методов
        while True:
            instruction = next(instructions)
            if instruction.opname == 'LOAD_METHOD' and instruction.argval in methods:
                return True
    except StopIteration as e:
        pass
    return False


def get_method_attributes(instructions: Iterator[Instruction], method: str) -> [str]:
    try:
        # ищем загрузку метода
        while True:
            instruction = next(instructions)
            if instruction.opname == 'LOAD_METHOD' and instruction.argval == method:
                break
        # сохраняем атрибуты, пока не произойдет вызов метода
        attributes = []
        while instruction.opname != "CALL_METHOD":
            instruction = next(instructions)
            if instruction.opname == 'LOAD_ATTR':
                attributes.append(instruction.argval)
        # возвращаем список атрибутов
        return attributes
    except StopIteration as e:
        pass
    return None


class ChatClassVerifier(type):

    def __init__(self, clsname, bases, clsdict, forbidden_methods=None):
        uses_tcp_sockets = False        # пока не нашли использование сокетов для работы по TCP
        for key, value in clsdict.items():
            if hasattr(value, "__code__"):

                # дизассемблируем байт-код в набор инструкций
                instruction_list = list(dis.get_instructions(getattr(value, "__code__")))

                # Ищем вызовы запрещенных методов
                if forbidden_methods:
                    instructions = iter(instruction_list)
                    if exist_method_calls(instructions, forbidden_methods):
                        raise TypeError("Недопустимо использовать вызовы [%s]" % ",".join(forbidden_methods))

                # Ищем использование сокетов для работы по TCP
                instructions = iter(instruction_list)
                if not uses_tcp_sockets:
                    arguments = get_method_attributes(instructions, 'socket')
                    if arguments is not None and 'AF_INET' in arguments and 'SOCK_STREAM' in arguments:
                        uses_tcp_sockets = True

        if not uses_tcp_sockets:
            raise TypeError("Необходимо использовать сокеты для работы по TCP")

        type.__init__(self, clsname, bases, clsdict)


class ClientVerifier(ChatClassVerifier):

    def __init__(self, clsname, bases, clsdict):
        # Ищем недопустимый атрибут класса типа socket
        for key, value in clsdict.items():
            if isinstance(value, sock.socket):
                raise TypeError("Недопустимый аттрибут %s - сокет не может быть атрибутом класса" % key)
        # Вызываем суперкласс для общих проверок
        super().__init__(clsname, bases, clsdict, forbidden_methods=('accept', 'listen'))


class ServerVerifier(ChatClassVerifier):

    def __init__(self, clsname, bases, clsdict):
        # Вызываем суперкласс для общих проверок
        super().__init__(clsname, bases, clsdict, forbidden_methods=('connect',))


class PortValue:
    def __init__(self, name):
        # Для данного подхода необходимо сформировать отдельное имя атрибута
        self.name = '_' + name
        self.default = 7777

    def __get__(self, instance, instance_type):
        print("PortValue.__get__")
        if instance is None:
            return self
        return getattr(instance, self.name, self.default)

    def __set__(self, instance, value):
        print("PortValue.__set__")
        if not isinstance(value, int):
            raise ValueError("Номер порта должен быть целым числом")
        elif value < 0:
            raise ValueError("Номер порта должен быть неотрицательным")
        setattr(instance, self.name, value)

# Реализовать дескриптор для класса серверного сокета, а в нем — проверку номера порта.
# Это должно быть целое число (>=0). Значение порта по умолчанию равняется 7777.
# Дескриптор надо создать в отдельном классе. Его экземпляр добавить в пределах класса серверного сокета.
# Номер порта передается в экземпляр дескриптора при запуске сервера.