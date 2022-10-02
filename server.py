import logging
import socket as sock
import argparse

import jim

import server_settings as sett
import server_log_config


class Server:
    """
    Chat server class
    """
    def __init__(self, address: str = None, port: str = None):
        self._address = address if address else sett.DEFAULT_LISTEN_ADDRESS
        self._port = int(port) if port else sett.DEFAULT_PORT
        log.critical("Чат-сервер ожидает подключений по адресу %s:%d",
                     self._address if self._address else '(все интерфейсы)', self._port)
        # Create and bind socket and listed to connections
        self._listening = False
        try:
            self._socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self._socket.bind((self._address, self._port))
            self._socket.listen()
            self._listening = True
        except OSError as e:
            log.critical("Не удалось инициализировать порт для входящих подключений: %s", e)
        except Exception as e:
            log.critical("Непредвиденная ошибка при инициализации порта для входящих подключений: %s", e)

    @property
    def listening(self):
        return self._listening

    def accept(self):
        """
        Process client messages
        :return: None
        """
        if not self._listening:
            log.critical("Обработка соединений невозможна - не инициализирован порт для входящих подключений")
            return
        try:
            connected = False
            connection, address = self._socket.accept()
            connected = True
            connection.settimeout(sett.CONNECTION_TIMEOUT)
            log.info("Клиент %s:%d: Входящее соединение установлено", *address)
            while True:                 # Loop through incoming messages
                data = connection.recv(jim.MAX_JIM_LEN).decode(sett.DEFAULT_ENCODING)
                if not data:
                    log.info("Клиент %s:%d: Соединение закрыто клиентом", *address)
                    break
                try:
                    message = jim.Message.from_str(data)
                except ValueError as e:
                    log.error("Клиент %s:%d: Получены некорректные данные: %s", *address, data)
                    response = jim.Response(**jim.Responses.BAD_REQUEST.response).json
                else:
                    log.debug("Клиент %s:%d: Получено сообщение: %s", *address, message.json)
                    if message.action == jim.Actions.PRESENCE:
                        log.debug("Клиент %s:%d: Формирование ответа на сообщение присутствия", *address)
                        response = jim.Response(**jim.Responses.OK.response).json
                    else:
                        log.error("Клиент %s:%d: Неподдерживаемый тип сообщения, формирование ответа", *address)
                        response = jim.Response(**jim.Responses.BAD_REQUEST.response).json
                log.debug("Клиент %s:%d: Отправка ответа: %s", *address, response)
                connection.send(response.encode(sett.DEFAULT_ENCODING))
        except TimeoutError:
            log.info("Клиент %s:%d: Соединение закрыто по таймауту", *address)
        except ValueError as e:             # Can happen when creating response
            log.critical("Клиент %s:%d: Непредвиденная ошибка данных: %s", e)
        finally:
            if connected:
                log.debug("Клиент %s:%d: Завершение соединения на стороне сервера", *address)
                connection.close()

    def shutdown(self):
        if self._listening:
            log.critical("Завершение работы чат-сервера")
            self._socket.close()
            self._listening = False


if __name__ == "__main__":
    # Initialize logger
    log = logging.getLogger(sett.LOG_NAME)
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-address', required=False)
    parser.add_argument('-port', required=False)
    args = parser.parse_args()
    # Initialize server
    log.debug("Инициализация сервера для приема соединений по адресу (%s:%s)", args.address, args.port)
    server = Server(args.address, args.port)
    if not server.listening:
        log.critical("Не удалось инициализировать сервер, приложение завершается")
        exit(-1)
    # Process chat connections
    try:
        while True:
            server.accept()
    except KeyboardInterrupt:
        log.critical("Обработка входящих соединений прервана по команде с клавиатуры")
    except Exception as e:
        log.critical("Непредвиденная ошибка при обработке входящего соединения: %s", e)
    # Shut down server
    server.shutdown()
    log.debug("Приложение завершило работу")
