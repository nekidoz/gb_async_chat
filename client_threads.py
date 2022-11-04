import logging
import socket as sock
import select
import sys
import argparse

import time
import threading
import queue

import jim

import client_settings as sett
import client_log_config


class Client:
    """
    Chat client class
    """

    def socket_reader(self):
        # def _receive_from_server(self) -> (bool, str):
        if not self._connected:
            log.error("Прием сообщений невозможен - не установлено соединение с сервером")
            self._reader_queue.put(None)
            return
        log.info("Прием сообщений от сервера стартовал")
        while True:
            message = None
            try:
                self._socket_lock.acquire(True)
                message = self._socket.recv(jim.MAX_JIM_LEN)
            except sock.timeout as e:
                continue
            except BrokenPipeError as e:
                log.critical("Нет соединения с сервером: %s", e)
                self._connected = False
                self._reader_queue.put(None)
                return
            except Exception as e:
                log.critical("Непредвиденная ошибка при приеме сообщения: %s", e)
                self._reader_queue.put(None)
                return
            finally:
                self._socket_lock.release()
            if message:
                log.debug(f"Получено сообщение от сервера: {message}")
                self._reader_queue.put(message)
                log.debug(f"Размер очереди входящих сообщений: {self._reader_queue.qsize()}")
            else:
                log.critical("Соединение закрыто сервером.")
                self._connected = False
                self._reader_queue.put(None)
                return

    def message_processor(self):
        log.info("Обработка принятых сообщений стартовала")
        while True:
            # get message from queue
            message_bytes = self._reader_queue.get()
            if not message_bytes:
                log.info("Обработка принятых сообщений закончена - обнаружен признак конца очереди")
                return
            # process message
            log.debug(f"Получено сообщение для обработки: {message_bytes}")
            try:

                # decode message to string
                try:
                    message_str = message_bytes.decode(sett.DEFAULT_ENCODING)
                except ValueError as e:
                    log.error("Ошибка декодирования байтовой строки сообщения: %s", e)
                    continue

                # try to interpret message as user message
                try:
                    message = jim.Message.from_str(message_str)
                except ValueError as e:

                    # not a user message - try to interpret it as server response
                    try:
                        response = jim.Response.from_str(message_str)
                    except ValueError as e:

                        # not a message nor a response - report and drop
                        log.error("Некорректный формат сообщения: %s", e)
                        continue

                    # SUCCESS: it's a response - QUEUE IT for processing
                    else:
                        self._response_queue.put(response)
                        log.debug("Получен ответ от сервера - поставлен в очередь (всего %d ответов в очереди)",
                                  self._response_queue.qsize())

                # it's a message - interpret it
                else:
                    if message.action != jim.Actions.MESSAGE:
                        # message type not supported - report and drop
                        log.error("Ожидается сообщения чата, получен неподдерживаемый тип сообщения")
                        continue

                    # SUCCESS: it's a chat message - PRINT IT
                    else:
                        sender = message.kwargs[jim.MessageFields.FROM]
                        target = message.kwargs[jim.MessageFields.TO]
                        text = message.kwargs[jim.MessageFields.MESSAGE]
                        log.debug("Получено сообщение от '%s' для '%s': '%s'", sender, target, text)
                        print(f"({sender}->{target}): {text}")

            # unexpected exception - report and drop
            except Exception as e:
                log.critical("Непредвиденная ошибка при декодировании ответа: %s", e)
                continue

            # report success to log and queue
            log.debug("Обработка сообщения прошла успешно")
            self._reader_queue.task_done()
            log.debug(f"Размер очереди входящих сообщений: {self._reader_queue.qsize()}")

    def socket_writer(self):
        if not self._connected:
            log.error("Отправка сообщений невозможна - не установлено соединение с сервером")
            return
        log.info("Отправка сообщений на сервер стартовала")
        while True:
            message = self._writer_queue.get()
            try:
                log.debug(f"Получено сообщение для отправки на сервер: {message}")
                self._socket_lock.acquire(True)
                self._socket.send(message)
                log.debug("Полученное для отправки на сервер сообщение отправлено")
            except BrokenPipeError as e:
                log.critical("Нет соединения с сервером: %s", e)
                self._connected = False
                return
            except sock.timeout as e:  # в соответствии с описанием в лекции, не тестировалось
                log.critical("Превышено время ожидания посылки данных серверу: %s", e)
                return False
            except Exception as e:
                log.critical("Непредвиденная ошибка при отправке сообщения: %s", e)
                return
            finally:
                self._socket_lock.release()
            self._writer_queue.task_done()
            log.debug(f"Размер очереди исходящих сообщений: {self._writer_queue.qsize()}")

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
            # !!! Почему-то, даже если поставить 0,5 секунд, writer очень долго - несколько секунд -
            # захватывает контроль над lock. Оптимальное не слишком маленькое значение, при котором ожидание захвата
            # lock не более секунды - 0,1.
            self._socket.settimeout(0.1)                # timeout to use the socket to read and write simultaneously
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
        # MULTITHREADING INIT
        self._socket_lock = threading.Lock()        # socket lock
        self._reader = threading.Thread(target=self.socket_reader, daemon=True)         # socket reader
        self._processor = threading.Thread(target=self.message_processor, daemon=True)  # message processor
        self._writer = threading.Thread(target=self.socket_writer, daemon=True)       # message writer
        self._reader_queue = queue.Queue()          # read queue
        self._writer_queue = queue.Queue()          # writer queue
        self._response_queue = queue.Queue()        # server response queue

    @property
    def connected(self):
        return self._connected

    def _send_message_to_server(self, message: dict) -> bool:
        log.debug(f"Постановка сообщения в очередь на отправку: {message}")
        try:
            self._writer_queue.put(jim.Message(**message).json.encode(sett.DEFAULT_ENCODING))
        except ValueError as e:
            log.error("Ошибка формирования сообщения: %s", e)
            return False
        except Exception as e:
            log.critical("Непредвиденная ошибка при формировании сообщения: %s", e)
            return False

        log.debug(f"Ожидание подтверждения приемки сообщения от сервера")
        response = self._response_queue.get()
        if response.response == jim.Responses.BAD_LOGIN:
            log.error("Сервер сообщил об ошибке аутентификации: %s - %s",  response.response, response.message)
            return False
        elif response.response == jim.Responses.NOT_FOUND:
            log.warning("Сервер сообщил, что адресат не в сети: %s - %s",  response.response, response.message)
            return False
        elif response.response != jim.Responses.OK:
            log.critical("Ошибочный код возврата сервера: %s - %s",  response.response, response.message)
            return False
        else:
            log.debug("Сообщение подтверждено")
        return True

    def send_presence(self) -> bool:
        return self._send_message_to_server(
                {jim.MessageFields.ACTION: jim.Actions.PRESENCE,
                 jim.MessageFields.USER: {
                     jim.MessageFields.ACCOUNT_NAME: self._nickname,
                     jim.MessageFields.STATUS: "Online"
                 }
                })

    def send_chat_message(self, target_nickname: str, message_text: str) -> bool:
        return self._send_message_to_server(
                {jim.MessageFields.ACTION: jim.Actions.MESSAGE,
                 jim.MessageFields.TO: target_nickname,
                 jim.MessageFields.FROM: self._nickname,
                 jim.MessageFields.MESSAGE: message_text
                })

    def chat(self):
        self._reader.start()
        self._processor.start()
        self._writer.start()
        if not self.send_presence():
            return
        try:
            while True:
                print("Введите имя адресата/чата и сообщение через пробел: ", flush=True)
                # Input chat message from keyboard and send it
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
        except KeyboardInterrupt:
            return
        # if not self.send_presence():
        #     return
        # try:
        #     self.wait_for_messages()
        # except KeyboardInterrupt:
        #     return

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
