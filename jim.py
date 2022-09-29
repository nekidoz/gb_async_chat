import enum
import time
import json

MAX_JIM_LEN = 640                       # Max JSON instant message length

"""
MESSAGE FORMATS:
# присутствие - извещения от клиента серверу о присутствии клиента online
{
    "action": "presence",                   # 15 characters max
    "time": <unix timestamp>, 
    ["type": "status",] 
    "user": {
        "account_name": "C0deMaver1ck",     # 25 characters max (chat names begin with '#' char)
        "status": "Yep, I am here!"
    }
}
# проверка присутствия - запрос от сервера клиенту для проверки присутствии клиента online
{
    "action": "probe", 
    "time": <unix timestamp>, 
}
# сообщение пользователю или в чат
{
    "action": "msg",
    "time": <unix timestamp>, 
    "to": {"account_name"|"#room_name"}, 
    "from": "account_name", 
    ["encoding": "ascii",]                  # default - 'ascii'
    "message": "message"                    # 500 characters max
}
# отключение от сервера
{
    "action": "quit"
}
# аутентификация на сервере
{
    "action": "authenticate", 
    "time": <unix timestamp>,
    "user": {
        "account_name": "C0deMaver1ck",
        "password": "CorrectHorseBatterStaple"
    } 
}
# присоединиться к чату / покинуть чат
{
    "action": {"join"|"leave"}, 
    "time": <unix timestamp>, 
    "room": "#room_name"
}
RESPONSE FORMATS:
{
    "response": <код ответа>,               # 3 digits
    "time": <unix timestamp>,
    [{"alert"|"error"}: <текст ответа>]     # status codes 1xx-2xx - "alert", others - "error"
}
"""


# Max 15 characters
class Actions(str, enum.Enum):
    """
    Possible message actions
    """
    PRESENCE = "presence"
    PROBE = "probe"
    MESSAGE = "msg"
    QUIT = "quit"
    AUTHENTICATE = "authenticate"
    JOIN = "join"
    LEAVE = "leave"


# ************* MESSAGE CHECKING START *********************

class MessageSettings(str, enum.Enum):
    """
    Enum of message settings fields for message descriptions (see FIELDS below).
    Fields which are not marked as required are optional.
    """
    TYPE = "type"                   # (REQUIRED) Message field type
    REQUIRED = "required"           # (REQUIRED) Field required flag
    # If a field is required, this optional field can contain a tuple of actions for which this field is REQUIRED,
    #  while for the others it is considered OPTIONAL
    # If a field is optional, this optional field can contain a tuple of actions for which this field is PERMITTED,
    #  while for the others it is considered INVALID
    FOR_ACTIONS = "for actions"     # List of Actions for which this field is required/permitted
    VALUES = "values"               # List of permitted field values
    MAX_LENGTH = "max length"       # Maximum string length
    STARTS_WITH = "starts with"     # String starts with substring


class MessageFields(str, enum.Enum):
    """
    Enum of all the possible message fields
    """
    ACTION = "action"
    TIME = "time"
    TYPE = "type"
    USER = "user"
    USER_ACCOUNT_NAME = "user/account_name"     # nested field names should begin with the enclosing field name
    USER_PASSWORD = "user/password"
    USER_STATUS = "user/status"
    TO = "to"
    FROM = "from"
    ENCODING = "encoding"
    MESSAGE = "message"
    ROOM = "room"


ACCOUNT_NAME_MAX_LENGTH = 25
MESSAGE_FIELD_MAX_LENGTH = 500
OTHER_FIELDS_MAX_LENGTH = 25

ROOM_PREFIX = "#"

FIELDS = {
    MessageFields.ACTION:   {MessageSettings.TYPE: Actions,
                             MessageSettings.REQUIRED: True,
                             },
    MessageFields.TIME:     {MessageSettings.TYPE: int,
                             MessageSettings.REQUIRED: False,
                             },
    MessageFields.TYPE:     {MessageSettings.TYPE: str,
                             MessageSettings.REQUIRED: False,
                             MessageSettings.FOR_ACTIONS: (Actions.PRESENCE, ),
                             MessageSettings.VALUES: ("status", )
                             },
    MessageFields.USER:     {MessageSettings.TYPE: dict,
                             MessageSettings.REQUIRED: True,
                             MessageSettings.FOR_ACTIONS: (Actions.PRESENCE, Actions.AUTHENTICATE)
                             },
    MessageFields.USER_ACCOUNT_NAME:    {MessageSettings.TYPE: str,
                                         MessageSettings.REQUIRED: True,
                                         MessageSettings.FOR_ACTIONS: (Actions.PRESENCE, Actions.AUTHENTICATE),
                                         MessageSettings.MAX_LENGTH: ACCOUNT_NAME_MAX_LENGTH
                                         },
    MessageFields.USER_PASSWORD:        {MessageSettings.TYPE: str,
                                         MessageSettings.REQUIRED: True,
                                         MessageSettings.FOR_ACTIONS: (Actions.AUTHENTICATE, ),
                                         MessageSettings.MAX_LENGTH: OTHER_FIELDS_MAX_LENGTH
                                         },
    MessageFields.USER_STATUS:          {MessageSettings.TYPE: str,
                                         MessageSettings.REQUIRED: True,
                                         MessageSettings.FOR_ACTIONS: (Actions.PRESENCE, ),
                                         MessageSettings.MAX_LENGTH: OTHER_FIELDS_MAX_LENGTH
                                         },
    MessageFields.TO:       {MessageSettings.TYPE: str,
                             MessageSettings.REQUIRED: True,
                             MessageSettings.FOR_ACTIONS: (Actions.MESSAGE, ),
                             MessageSettings.MAX_LENGTH: ACCOUNT_NAME_MAX_LENGTH
                             },
    MessageFields.FROM:     {MessageSettings.TYPE: str,
                             MessageSettings.REQUIRED: True,
                             MessageSettings.FOR_ACTIONS: (Actions.MESSAGE, ),
                             MessageSettings.MAX_LENGTH: ACCOUNT_NAME_MAX_LENGTH
                             },
    MessageFields.ENCODING: {MessageSettings.TYPE: str,
                             MessageSettings.REQUIRED: False,
                             MessageSettings.FOR_ACTIONS: (Actions.MESSAGE, ),
                             MessageSettings.MAX_LENGTH: OTHER_FIELDS_MAX_LENGTH
                             },
    MessageFields.MESSAGE:  {MessageSettings.TYPE: str,
                             MessageSettings.REQUIRED: True,
                             MessageSettings.FOR_ACTIONS: (Actions.MESSAGE, ),
                             MessageSettings.MAX_LENGTH: MESSAGE_FIELD_MAX_LENGTH
                             },
    MessageFields.ROOM:     {MessageSettings.TYPE: str,
                             MessageSettings.REQUIRED: True,
                             MessageSettings.FOR_ACTIONS: (Actions.JOIN, Actions.LEAVE),
                             MessageSettings.MAX_LENGTH: ACCOUNT_NAME_MAX_LENGTH,
                             MessageSettings.STARTS_WITH: ROOM_PREFIX
                             },
    }


def get_child_field_name(field_name: str) -> str:
    return field_name[field_name.rfind("/") + 1:]


def check_message(message: dict, action: Actions = None, parent: str = None) -> bool:
    """
    Validate message fields, recursively validating nested structures in dict fields.
    Only known message fields are checked, unknown fields are ignored.
    :param message: message presented as dict
    :param action: action id for recursive calls; should NOT be specified at initial call
    :param parent: parent field(s) string for recursive calls; should NOT be specified at initial call
    :return: True if message OK, ValueError exception otherwise
    Raises: ValueError
    """

    # If this field is not present, FOR_ACTIONS MessageSettings key will not work as expected
    action = message.get(MessageFields.ACTION) if not action else action
    # Append slash to parent or make it blank if no parent specified (at initial call)
    parent = "" if not parent else parent + "/"
    # Filter fields by parent prefix (e.g. 'user/' in 'user/name') if specified, or
    #  filter out nested fields (containing slash) if no parent
    fields = {key: value for key, value in FIELDS.items() if key.find("/") == -1} if not parent \
        else {key: value for key, value in FIELDS.items() if key.startswith(parent)}

    for field, settings in fields.items():

        # get optional applicable actions field
        for_actions = settings.get(MessageSettings.FOR_ACTIONS)

        # Check if message field exists
        try:
            # remove parent prefix if specified to get the real field name without parent prefix
            value = message[get_child_field_name(field)]
        except KeyError as e:
            # check if field is required for all or certain actions
            if settings[MessageSettings.REQUIRED] and (not for_actions or action in for_actions):
                raise ValueError(f"Action '{action}': required message field '{field}' does not exist")
            else:
                continue            # Go to next parameter if this one is optional

        # Field exists - check if it can be supplied for this action
        if for_actions and action not in for_actions:
            raise ValueError(f"Action '{action}': unexpected message field '{field}'")

        # Check field value type
        if settings[MessageSettings.TYPE] == dict:
            # Nested structure field - RECURSIVELY CALL MYSELF passing value as message
            if type(value) != dict:
                raise ValueError(f"Action '{action}': message field '{field}' should be of type 'dict'")
            check_message(value, action, field if not parent else "/".join([parent, field]))
            continue                # Don't have to do any further checking
        else:                       # Ordinary field - check value type
            try:
                typed_value = settings[MessageSettings.TYPE](value)
            except ValueError as e:     # Wrong field value type
                raise ValueError(f"Action '{action}': wrong message field '{field}' value type: '{value}'")

        # If list of permitted values specified, check if value in the list
        try:
            if typed_value not in settings[MessageSettings.VALUES]:
                raise ValueError(f"Action '{action}': wrong message field '{field}' value: '{typed_value}'")
        except KeyError as e:
            pass

        # If maximum length of value specified, check
        try:
            max_length = settings[MessageSettings.MAX_LENGTH]
            if len(typed_value) > max_length:
                raise ValueError(f"Action '{action}': message field '{field}' value exceeds {max_length} characters:"
                                 f" '{typed_value}'")
        except KeyError as e:
            pass

        # If starting substring of value specified, check
        try:
            starts_with = settings[MessageSettings.STARTS_WITH]
            if not str(typed_value).startswith(starts_with):
                raise ValueError(f"Action '{action}': message field '{field}' value should start with '{starts_with}', "
                                 f"got: '{typed_value}'")
        except KeyError as e:
            pass

    return True

# ************* MESSAGE CHECKING END *********************


class Responses(enum.IntEnum):
    # 1xx — информационные сообщения:
    NOTIFY_BASIC = 100          # базовое уведомление
    NOTIFY_IMPORTANT = 101      # важное уведомление
    # 2xx — успешное завершение:
    OK = 200                    # OK
    CREATED = 201               # объект создан
    ACCEPTED = 202              # подтверждение
    # 4xx — ошибка на стороне клиента:
    BAD_REQUEST = 400           # неправильный запрос / JSON - объект
    LOGIN_REQUIRED = 401        # не авторизован
    BAD_LOGIN = 402             # неправильный логин / пароль
    FORBIDDEN = 403             # пользователь заблокирован
    NOT_FOUND = 404             # пользователь / чат отсутствует на сервере
    CONFLICT = 409              # уже имеется подключение с указанным логином
    GONE = 410                  # адресат существует, но недоступен(offline)
    # 5xx — ошибка на стороне сервера:
    SERVER_ERROR = 500          # ошибка сервера

    @property
    def response(self):
        messages = {
            self.NOTIFY_BASIC: {"alert": "Базовое уведомление"},
            self.NOTIFY_IMPORTANT: {"alert": "Важное уведомление"},
            self.OK: {"alert": "OK"},
            self.CREATED: {"alert": "Объект создан"},
            self.ACCEPTED: {"alert": "Подтверждение"},
            self.BAD_REQUEST: {"error": "Неправильный запрос / JSON - объект"},
            self.LOGIN_REQUIRED: {"error": "Не авторизован"},
            self.BAD_LOGIN: {"error": "Неправильный логин / пароль"},
            self.FORBIDDEN: {"error": "Пользователь заблокирован"},
            self.NOT_FOUND: {"error": "Пользователь / чат отсутствует на сервере"},
            self.CONFLICT: {"error": "Уже имеется подключение с указанным логином"},
            self.GONE: {"error": "Адресат существует, но недоступен (offline)"},
            self.SERVER_ERROR: {"error": "Ошибка сервера"}
        }

        message = {
            "response": self.value,
        }
        message.update(messages.get(self.value, {"error": "Неизвестный код ответа"}))
        return message


class Message:
    """
    ATTRIBUTES:
    _action - message action
    _time - UNIX timestamp passed to initializer or timestamp of the moment the Message object was created
    _kwargs - other arguments dictionary
    """
    def __init__(self, action: Actions, **kwargs):
        self.action = Actions(action)
        self.time = kwargs.pop("time", time.time_ns())
        self.kwargs = kwargs

    @classmethod
    def from_str(cls, json_str: str):
        """
        Class object constructor from JSON string
        :param json_str: JSON string to parse as Message object
        :return: Message object if OK, raises ValueError in case of message format error
        """
        if len(json_str) > MAX_JIM_LEN:
            raise ValueError(f"Maximum JIM message length of {MAX_JIM_LEN} characters exceeded: {len(json_str)}")
        message = json.loads(json_str)
        check_message(message)          # Check message format, raises ValueError if error
        return cls(**message)

    # return JSON string with the message
    @property
    def json(self) -> str:
        message = {
            "action": self.action,
            "time": self.time
        }
        message.update(**self.kwargs)
        return json.dumps(message)


class Response:
    """
    ATTRIBUTES:
    _action - message action
    _time - UNIX timestamp passed to initializer or timestamp of the moment the Message object was created
    _kwargs - other arguments dictionary
    """
    def __init__(self, response: Responses, **kwargs):
        self.response = Responses(response)
        self.time = int(kwargs.pop("time", time.time_ns()))
        self.kwargs = kwargs

    # class object constructor from JSON string
    @classmethod
    def from_str(cls, json_str: str):
        if len(json_str) > MAX_JIM_LEN:
            raise ValueError(f"Maximum JIM response length of {MAX_JIM_LEN} characters exceeded: {len(json_str)}")
        response = json.loads(json_str)
        return cls(**response)

    # return JSON string with the response
    @property
    def json(self) -> str:
        response = {
            "response": self.response,
            "time": self.time
        }
        response.update(**self.kwargs)
        return json.dumps(response)
