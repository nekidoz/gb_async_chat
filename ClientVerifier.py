import socket as sock
import dis
from collections.abc import Iterator, Iterable
from dis import Instruction


class ClientVerifier(type):

    @staticmethod
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

    @staticmethod
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

    def __init__(self, clsname, bases, clsdict):
        uses_tcp_sockets = False        # пока не нашли использование сокетов для работы по TCP
        for key, value in clsdict.items():
            print("Object name: ", key)
            # Ищем недопустимый атрибут класса типа socket
            if isinstance(value, sock.socket):
                raise TypeError("Недопустимый аттрибут %s - сокет не может быть атрибутом класса" % key)

            elif hasattr(value, "__code__"):

                # дизассемблируем байт-код в набор инструкций
                instruction_list = list(dis.get_instructions(getattr(value, "__code__")))

                # Ищем вызовы запрещенных методов
                forbidden_methods = ['accept', 'listen']
                instructions = iter(instruction_list)
                if self.exist_method_calls(instructions, forbidden_methods):
                    raise TypeError("Недопустимо использовать вызовы %s", forbidden_methods)

                # Ищем использование сокетов для работы по TCP
                instructions = iter(instruction_list)
                if not uses_tcp_sockets:
                    arguments = self.get_method_attributes(instructions, 'socket')
                    if arguments is not None and 'AF_INET' in arguments and 'SOCK_STREAM' in arguments:
                        uses_tcp_sockets = True

        if not uses_tcp_sockets:
            raise TypeError("Необходимо использовать сокеты для работы по TCP")

        type.__init__(self, clsname, bases, clsdict)
