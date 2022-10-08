import logging
import socket as sock
import argparse

import jim

import client_settings as sett
import client_log_config


class Client:
    """
    Chat client class
    """
    def __init__(self, server_address: str = None, server_port: str = None):
        self._server_address = server_address if server_address else sett.DEFAULT_SERVER_ADDRESS
        self._server_port = int(server_port) if server_port else sett.DEFAULT_PORT
        log.critical("Соединение с чат-сервером %s:%d",
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
            self._connected = True

    @property
    def connected(self):
        return self._connected

    def __call__(self):
        if not self._connected:
            log.error("Чат невозможен - не установлено соединение с сервером")
            return
        log.debug("Посылка серверу сообщения присутствия (presence)")
        try:
            message = jim.Message(
                **{jim.MessageFields.ACTION: jim.Actions.PRESENCE,
                 jim.MessageFields.USER: {
                     jim.MessageFields.ACCOUNT_NAME: "test",
                     jim.MessageFields.STATUS: "Online"
                 }
                 })
            self._socket.send(message.json.encode(sett.DEFAULT_ENCODING))
        except ValueError as e:
            log.error("Ошибка формирования сообщения: %s", e)
            return
        except sock.timeout as e:       # в соответствии с описанием в лекции, не тестировалось
            log.critical("Превышено время ожидания посылки данных серверу: %s", e)
            return
        except Exception as e:
            log.critical("Непредвиденная ошибка при формировании или посылке сообщения: %s", e)
            return
        log.debug("Прием ответа от сервера")
        try:
            response = jim.Response.from_str(self._socket.recv(jim.MAX_JIM_LEN).decode(sett.DEFAULT_ENCODING))
        except ValueError as e:
            log.error("Некорректный формат принятого сообщения: %s", e)
            return
        except sock.timeout as e:       # в соответствии с описанием в лекции, не тестировалось
            log.critical("Превышено время ожидания приема данных от сервера: %s", e)
            return
        except Exception as e:
            log.critical("Непредвиденная ошибка при приеме сообщения: %s", e)
            return
        log.debug("Ответ от сервера: %s", response.json)
        if response.response == jim.Responses.OK:
            log.debug("Сообщение подтверждено")
        else:
            log.error("Ошибочный код возврата сервера: %s - %s",  response.response, response.message)

    def shutdown(self):
        if self._connected:
            log.critical("Завершение соединения с чат-сервером %s:%d",
                         self._server_address if self._server_address else '(broadcast)', self._server_port)
            self._socket.close()
            self._connected = False


if __name__ == "__main__":
    # Initialize logger
    log = logging.getLogger(sett.LOG_NAME)
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('address', nargs='?', default=None)
    parser.add_argument('port', nargs='?', default=None)
    args = parser.parse_args()
    # Initialize client
    log.debug("Инициализация клиента для соединения с сервером (%s:%s)", args.address, args.port)
    client = Client(args.address, args.port)
    if not client.connected:
        log.critical("Не удалось установить соединение с сервером, приложение завершается")
        exit(-1)
    # Chat
    client()
    # Shut down client
    client.shutdown()
    log.debug("Приложение завершило работу")
