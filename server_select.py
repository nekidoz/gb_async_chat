import logging
import socket as sock
import select
import argparse
from dataclasses import dataclass

import jim

import server_settings as sett
import server_log_config


@dataclass
class Connection:
    __slots__ = ('connection', 'address', 'nickname')       # Optimize memory usage with slots
    connection: sock.socket         # connection instance
    address: (str, int)             # client address
    nickname: str                   # client nickname used to send messages to

    def fileno(self):
        """ Return file descriptor to use with select.select() """
        return self.connection.fileno()


class Server:
    """
    Chat server class
    """
    def __init__(self, address: str = None, port: str = None):
        """
        Initialize server - open port for listening
        :param address: server IP address
        :param port: server port
        Attributes:
        _address - server IP address
        _port - server port
        _connections - client connections dictionary
        """
        self._address = address if address else sett.DEFAULT_LISTEN_ADDRESS
        self._port = int(port) if port else sett.DEFAULT_PORT
        log.critical("Чат-сервер ожидает подключений по адресу %s:%d",
                     self._address if self._address else '(все интерфейсы)', self._port)
        # Create and bind socket and listed to connections
        self._listening = False
        try:
            self._socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
            self._socket.bind((self._address, self._port))
            self._socket.listen(5)          # размер буфера входящих соединений - в соответствии с описанием в лекции
            self._socket.setblocking(True)  # blocking mode - will wait for data during send() and recv()
            self._socket.settimeout(sett.SOCKET_TIMEOUT)    # set timeout for waiting for incoming connections
            self._listening = True
        except OSError as e:
            log.critical("Не удалось инициализировать порт для входящих подключений: %s", e)
        except Exception as e:
            log.critical("Непредвиденная ошибка при инициализации порта для входящих подключений: %s", e)
        # Initialize empty client connections dictionary
        self._connections = {}

    @property
    def listening(self):
        return self._listening

    def _accept_connection(self) -> bool:
        """
        Accept a pending connection if any, if maximum number of connection has not been reached.
        Add a new connection to the _connections dictionary.
        :return: True if a new connection accepted, False if timeout or maximum number of connections reached
        """
        if not self._listening:
            log.critical("Обработка соединений невозможна - не инициализирован порт для входящих подключений")
            return False
        try:
            connection, address = self._socket.accept()
        except TimeoutError:
            log.debug("Нет новых запросов на соединение")
            return False
        if len(self._connections) >= sett.MAX_CONNECTIONS:
            log.warning("Клиент %s:%d: Превышено количество допустимых соединений - %d, "
                        "входящее соединение отклоняется", *address, sett.MAX_CONNECTIONS)
            try:
                response = jim.Response(**jim.Responses.SERVER_ERROR.response).json
                log.debug("Клиент %s:%d: Отправка сообщения об ошибке сервера: %s", *address, response)
                connection.send(response.encode(sett.DEFAULT_ENCODING))
            except Exception as e:
                log.critical("Клиент %s:%d: Непредвиденная ошибка при отправке сообщения об ошибке: %s", *address, e)
            log.debug("Клиент %s:%d: Завершение соединения на стороне сервера", *address)
            connection.close()
            return False
        connection.settimeout(sett.CLIENT_CONNECTION_TIMEOUT)
        log.info("Клиент %s:%d: Входящее соединение установлено", *address)
        self._connections[connection] = Connection(
            connection=connection,
            address=address,
            nickname=""
        )
        return True


    def _check_nickname(self, connection: Connection, nickname: str) -> bool:
        """
        Check if nickname exists for connection;
        if not, assign the given nickname and return True;
        if exists, check is the given nickname matches the assigned one;
        if not, return False, else return True
        :param connection: connection to check
        :param nickname: nickname to check
        :return: check status
        """
        if connection.nickname is None or connection.nickname == "":
            connection.nickname = nickname
            log.debug("Клиент %s:%d: Установлено имя (%s) для соединения", *connection.address, connection.nickname)
            return True
        # Report nickname change is invalid if nickname mismatch
        elif connection.nickname != nickname:
            log.debug("Клиент %s:%d: Несовпадение имени отправителя (%s) с именем пользователя (%s) для соединения",
                      *connection.address, nickname, connection.nickname)
            return False
        else:
            return True

    def _process_message(self, connection: Connection) -> bool:
        """
        For the specified connection, receive a peer's message, process it and reply to it if needed
        :return: True if message exchange succeeded, False if failed for some reason
        """
        try:
            data_bytes = connection.connection.recv(jim.MAX_JIM_LEN)
            data = data_bytes.decode(sett.DEFAULT_ENCODING)
            forward_message = False         # for chat messages
            if not data:
                log.info("Клиент %s:%d: Соединение закрыто клиентом", *connection.address)
                return False
            try:
                message = jim.Message.from_str(data)
            except ValueError as e:
                log.error("Клиент %s:%d: Получены некорректные данные: %s", *connection.address, data)
                response = jim.Response(**jim.Responses.BAD_REQUEST.response).json
            else:
                log.debug("Клиент %s:%d: Получено сообщение: %s", *connection.address, message.json)

                # ************ PRESENCE ***************
                if message.action == jim.Actions.PRESENCE:
                    sender_nickname = message.kwargs[jim.MessageFields.USER][jim.MessageFields.ACCOUNT_NAME]
                    log.debug("Клиент %s:%d: Формирование ответа на сообщение присутствия", *connection.address)
                    if not self._check_nickname(connection, sender_nickname):
                        response = jim.Response(**jim.Responses.BAD_LOGIN.response).json
                    else:
                        response = jim.Response(**jim.Responses.OK.response).json

                # ************ MESSAGE ***************
                elif message.action == jim.Actions.MESSAGE:
                    sender_nickname = message.kwargs[jim.MessageFields.FROM]
                    if not self._check_nickname(connection, sender_nickname):
                        log.debug("Клиент %s:%d: Формирование сообщения об ошибке аутентификации", *connection.address)
                        response = jim.Response(**jim.Responses.BAD_LOGIN.response).json
                    else:
                        target_nickname = message.kwargs[jim.MessageFields.TO]

                        # Forward message to all users
                        if target_nickname == jim.BROADCAST_MESSAGE_ADDRESS:

                            # Send the message
                            log.debug("Клиент %s:%d: Пересылка сообщения всем клиентам", *connection.address)
                            for other_connection in self._connections:
                                if other_connection.fileno() != connection.connection.fileno():
                                    log.debug("Клиент %s:%d: Пересылка сообщения клиенту %s:%d",
                                              *connection.address, *other_connection.getpeername())
                                    other_connection.send(data_bytes)

                            # Confirm regardless of whether there were any other users
                            log.debug("Клиент %s:%d: Формирование подтверждения отправки", *connection.address)
                            response = jim.Response(**jim.Responses.OK.response).json

                        # Send message to particular user(-s if multiple connections for the same nickname)
                        # (chats not processed)
                        else:

                            # filter connections by nickname, excluding sender
                            forward_destinations = [destination for destination in self._connections.values()
                                                    if destination.nickname == target_nickname and
                                                    destination.connection.fileno() != connection.fileno()]

                            # if no users found, error
                            if not forward_destinations:
                                log.debug("Клиент %s:%d: Формирование сообщения 'адресат %s не найден' для отправителя",
                                          *connection.address, target_nickname)
                                response = jim.Response(**jim.Responses.NOT_FOUND.response).json

                            # is destination(s) found, send message
                            else:
                                log.debug("Клиент %s:%d: Пересылка сообщения клиенту(-ам) с именем %s",
                                          *connection.address, target_nickname)
                                for other_connection in forward_destinations:
                                    log.debug("Клиент %s:%d: Пересылка сообщения клиенту %s:%d",
                                              *connection.address, *other_connection.connection.getpeername())
                                    other_connection.connection.send(data_bytes)
                                log.debug("Клиент %s:%d: Формирование подтверждения отправки", *connection.address)
                                response = jim.Response(**jim.Responses.OK.response).json

                # ************ UNKNOWN ***************
                else:
                    log.error("Клиент %s:%d: Неподдерживаемый тип сообщения, формирование ответа", *connection.address)
                    response = jim.Response(**jim.Responses.BAD_REQUEST.response).json
        except ValueError as e:  # Can happen when creating response
            log.critical("Клиент %s:%d: Непредвиденная ошибка данных: %s", e)
            return False
        except TimeoutError:
            log.warning("Клиент %s:%d: Соединение закрывается по таймауту.", *connection.address)
            return False
        except ConnectionResetError:
            log.info("Клиент %s:%d: Соединение закрыто клиентом.", *connection.address)
            return False

        # Send response to client
        try:
            if not response:
                log.critical("Клиент %s:%d: Формирование сообщения об ошибке сервера по умолчанию", *connection.address)
                response = jim.Response(**jim.Responses.SERVER_ERROR.response).json
            log.debug("Клиент %s:%d: Отправка ответа: %s", *connection.address, response)
            connection.connection.send(response.encode(sett.DEFAULT_ENCODING))
        except ValueError as e:  # Can happen when creating response
            log.critical("Клиент %s:%d: Непредвиденная ошибка данных: %s", e)
            return False
        except TimeoutError:
            log.warning("Клиент %s:%d: Соединение закрывается по таймауту.", *connection.address)
            return False
        except ConnectionResetError:
            log.info("Клиент %s:%d: Соединение закрыто клиентом.", *connection.address)
            return False

        return True

    def _process_messages(self) -> bool:
        """
        Process all the connections ready to communicate.
        If message exchange with a given connection fails, close it and remove from the connections list.
        :return: False if exception occurs, True otherwise
        """
        try:
            read_ready, _, _ = select.select(self._connections, [], [], sett.SELECT_TIMEOUT)
            if not read_ready:
                log.debug("Нет новых запросов от существующих соединений.")
            else:
                for connection in read_ready:
                    if not self._process_message(self._connections[connection]):
                        connection.close()
                        del self._connections[connection]
        except select.error as e:
            log.critical("Непредвиденная ошибка select(): %s", e)
            return False
        except Exception as e:
            log.critical("Непредвиденная ошибка при обработке сообщений клиентов: %s", e)
            return False
        return True

    def service_connections(self):
        """ Accept connections and process client messages """
        while True:
            log.debug("Старт цикла обслуживания соединений.")
            print("Существующие соединения: ", end="")
            print([(connection.address, connection.nickname) for connection in self._connections.values()])
            # Accept all pending connections
            while self._accept_connection():
                pass
            self._process_messages()

    def shutdown(self):
        if self._listening:
            log.critical("Завершение работы чат-сервера")
            self._socket.close()
            self._listening = False


def main() -> bool:
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
        return False
    # Process chat connections
    try:
        server.service_connections()
    except KeyboardInterrupt:
        log.critical("Обработка входящих соединений прервана по команде с клавиатуры")
    except Exception as e:
        log.critical("Непредвиденная ошибка при обработке входящего соединения: %s", e)
        return False
    finally:
        # Shut down server
        server.shutdown()
    log.debug("Приложение завершило работу")


if __name__ == "__main__":
    # Initialize logger
    log = logging.getLogger(sett.LOG_NAME)
    exit(0 if main() else -1)
