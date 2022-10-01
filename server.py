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
        self._socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
        self._socket.bind((self._address, self._port))
        self._socket.listen()
        self._listening = True

    @property
    def listening(self):
        return self._listening

    def __call__(self):
        """
        Process client messages
        :return: None
        """
        if not self._listening:
            log.error("Обработка соединений невозможна - не установлено прослушивание порта сервера")
            return
        while True:
            connection, address = self._socket.accept()
            message = jim.Message.from_str(connection.recv(jim.MAX_JIM_LEN).decode(sett.DEFAULT_ENCODING))
            log.debug("Сообщение от %s: %s", address, message.json)
            if message.action == jim.Actions.PRESENCE:
                response = jim.Response(**jim.Responses.OK.response).json
            else:
                response = jim.Response(**jim.Responses.BAD_REQUEST.response).json
            connection.send(response.encode(sett.DEFAULT_ENCODING))
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
    server()
    # Shut down server
    server.shutdown()
    log.debug("Приложение завершило работу")
