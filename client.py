import logging
import socket as sock
import select
import sys
import argparse

import jim

import client_settings as sett
import client_log_config
from ClientVerifier import ClientVerifier


class Client(metaclass=ClientVerifier):
    # ClientVerifier - раскомментируйте следующую строку, чтобы получить ошибку - глобальный атрибут сокета
    # test = sock.socket()
    """
    Chat client class
    """
    def __init__(self, server_address: str = None, server_port: str = None, nickname: str = None):
        self._server_address = server_address if server_address else sett.DEFAULT_SERVER_ADDRESS
        self._server_port = int(server_port) if server_port else sett.DEFAULT_PORT
        self._nickname = nickname if nickname else "client"
        log.debug("Соединение с чат-сервером %s:%d",
                     self._server_address if self._server_address else '(broadcast)', self._server_port)
        self._connected = False
        try:
            self._socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self._socket.settimeout(sett.CONNECTION_TIMEOUT)            # timeout of connection to server
            self._socket.connect((self._server_address, self._server_port))
            self._socket.setblocking(True)              # blocking mode - will wait for data during send() and recv()
        except ConnectionRefusedError as e:
            log.critical("Соединение отклонено сервером: %s", e)
        except sock.timeout as e:               # в соответствии с описанием в лекции, не тестировалось
            log.critical("Превышено время ожидания соединения с сервером: %s", e)
        except sock.error as e:                 # в соответствии с описанием в лекции, не тестировалось
            log.critical("Ошибка соединения с сервером: %s", e)
        except Exception as e:
            log.critical("Непредвиденная ошибка при установлении соединения с сервером: %s", e)
        else:
            log.critical("Соединение с сервером %s:%d установлено с адреса %s:%d, имя пользователя %s",
                         self._server_address if self._server_address else '(broadcast)', self._server_port,
                         *self._socket.getsockname(),
                         self._nickname)
            self._connected = True

    @property
    def connected(self):
        return self._connected

    def _send_message_to_server(self, message: dict) -> bool:
        if not self._connected:
            log.error("Чат невозможен - не установлено соединение с сервером")
            return False
        log.debug(f"Посылка сообщения серверу: {message}")
        try:
            self._socket.send(jim.Message(**message).json.encode(sett.DEFAULT_ENCODING))
        except ValueError as e:
            log.error("Ошибка формирования сообщения: %s", e)
            return False
        except sock.timeout as e:       # в соответствии с описанием в лекции, не тестировалось
            log.critical("Превышено время ожидания посылки данных серверу: %s", e)
            return False
        except Exception as e:
            log.critical("Непредвиденная ошибка при формировании или посылке сообщения: %s", e)
            return False
        else:
            return True

    def _receive_from_server(self) -> (bool, str):
        if not self._connected:
            log.error("Чат невозможен - не установлено соединение с сервером")
            return False, ""
        log.debug("Прием сообщения от сервера")
        try:
            response_str = self._socket.recv(jim.MAX_JIM_LEN)
            if not response_str:
                log.critical("Соединение закрыто сервером.")
                self._connected = False
                return False, ""
            log.debug(f"Получено сообщение от сервера: {response_str}")
        except sock.timeout as e:       # в соответствии с описанием в лекции, не тестировалось
            log.critical("Превышено время ожидания приема данных от сервера: %s", e)
            return False, ""
        except BrokenPipeError as e:
            log.critical("Нет соединения с сервером: %s", e)
            # self._connected = False
            return False, ""
        except Exception as e:
            log.critical("Непредвиденная ошибка при приеме сообщения: %s", e)
            return False, ""
        return True, response_str

    def _receive_response_from_server(self) -> (bool, jim.Response):
        log.debug("Прием ответа (response) от сервера")
        try:
            success, response_str = self._receive_from_server()
            if not success:
                return False, None
            response = jim.Response.from_str(response_str.decode(sett.DEFAULT_ENCODING))
        except ValueError as e:
            log.error("Некорректный формат принятого ответа: %s", e)
            return False, None
        except Exception as e:
            log.critical("Непредвиденная ошибка при приеме или декодировании ответа: %s", e)
            return False, None
        log.debug("Ответ от сервера: %s", response.json)
        return True, response

    def _receive_message_from_server(self) -> (bool, jim.Message):
        log.debug("Прием сообщения (message) от сервера")
        try:
            success, message_str = self._receive_from_server()
            if not success:
                return False, None
            message = jim.Message.from_str(message_str.decode(sett.DEFAULT_ENCODING))
        except ValueError as e:
            log.error("Некорректный формат принятого сообщения: %s", e)
            return False, None
        except Exception as e:
            log.critical("Непредвиденная ошибка при приеме или декодировании сообщения: %s", e)
            return False, None
        log.debug("Сообщение от сервера: %s", message.json)
        return True, message

    def _send_message_and_wait_for_response(self, message: dict) -> bool:
        if not self._send_message_to_server(message):
            return False
        success, response = self._receive_response_from_server()
        if not success:
            return False
        if response.response == jim.Responses.BAD_LOGIN:
            log.error("Сервер сообщил об ошибке аутентификации: %s - %s",  response.response, response.message)
        elif response.response == jim.Responses.NOT_FOUND:
            log.warning("Сервер сообщил, что адресат не в сети: %s - %s",  response.response, response.message)
        elif response.response != jim.Responses.OK:
            log.critical("Ошибочный код возврата сервера: %s - %s",  response.response, response.message)
            return False
        else:
            log.debug("Сообщение подтверждено")
        return True

    def send_presence(self) -> bool:
        return self._send_message_and_wait_for_response(
                {jim.MessageFields.ACTION: jim.Actions.PRESENCE,
                 jim.MessageFields.USER: {
                     jim.MessageFields.ACCOUNT_NAME: self._nickname,
                     jim.MessageFields.STATUS: "Online"
                 }
                })

    def send_chat_message(self, target_nickname: str, message_text: str) -> bool:
        return self._send_message_and_wait_for_response(
                {jim.MessageFields.ACTION: jim.Actions.MESSAGE,
                 jim.MessageFields.TO: target_nickname,
                 jim.MessageFields.FROM: self._nickname,
                 jim.MessageFields.MESSAGE: message_text
                })

    def receive_chat_message(self) -> (bool, str, str, str):
        """
        Receives chat message from server
        :return: status, sender, addressee and message
        """
        success, message = self._receive_message_from_server()
        if not success:
            return False, "", "", ""
        try:
            if message.action != jim.Actions.MESSAGE:
                log.error("Ожидается сообщения чата, получено сообщение: %s", message.json)
                return False, "", "", ""
            else:
                return True, \
                       message.kwargs[jim.MessageFields.FROM], \
                       message.kwargs[jim.MessageFields.TO], \
                       message.kwargs[jim.MessageFields.MESSAGE]
        except KeyError as e:
            log.error("Неверный формат сообщения чата: %s", message.json)
            return False, "", "", ""

    def wait_for_messages(self):
        while True:                 # wait for data from stdin or server connection
            print("Введите имя адресата/чата и сообщение через пробел: ", end="", flush=True)
            try:
                read_ready, _, _ = select.select([sys.stdin, self._socket], [], [], sett.SELECT_TIMEOUT)
            except select.error as e:
                log.critical("Непредвиденная ошибка select(): %s", e)
                return
            if not read_ready:
                print("")
                log.debug("Нет новых сообщений")
            else:
                for connection in read_ready:
                    if connection.fileno() == sys.stdin.fileno():
                        # Input chat message from keyboard and send it to everyone else
                        message = input()
                        target_nickname = message.split(" ")[0]
                        message = message.removeprefix(target_nickname).strip()
                        if target_nickname is None or target_nickname == "":
                            print("Имя адресата/чата не может быть пустым")
                        elif message is None or message == "":
                            print("Сообщение не может быть пустым")
                        else:
                            log.debug("Отправка сообщения пользователю %s: %s", target_nickname, message)
                            if not self.send_chat_message(target_nickname, message):
                                return
                    else:
                        print("")
                        # Receive message sent by someone else
                        success, sender, addressee, text = self.receive_chat_message()
                        if not success:
                            return
                        log.info("Получено сообщение от '%s' для '%s': '%s'", sender, addressee, text)
                        print(f"({sender}->{addressee}): {text}")

    def chat(self):
        if not self.send_presence():
            return
        try:
            self.wait_for_messages()
        except KeyboardInterrupt:
            return

    def shutdown(self):
        if self._connected:
            log.critical("Завершение соединения с чат-сервером %s:%d с адреса %s:%d",
                         self._server_address if self._server_address else '(broadcast)', self._server_port,
                         *self._socket.getsockname())
            self._socket.close()
            self._connected = False


def main() -> bool:
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('address', nargs='?', default=None)
    parser.add_argument('port', nargs='?', default=None)
    parser.add_argument('name', nargs='?', default=None)
    args = parser.parse_args()
    # Initialize client
    log.debug("Инициализация клиента для соединения с сервером (%s:%s)", args.address, args.port)
    client = Client(args.address, args.port, args.name)
    if not client.connected:
        log.critical("Не удалось установить соединение с сервером, приложение завершается")
        return False
    # Chat
    client.chat()
    # Shut down client
    client.shutdown()
    log.debug("Приложение завершило работу")
    return True


if __name__ == "__main__":
    # Initialize logger
    log = logging.getLogger(sett.LOG_NAME)
    exit(0 if main() else -1)
