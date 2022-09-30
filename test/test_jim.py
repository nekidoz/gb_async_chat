import abc
import unittest
import json
import random
import string

# Necessary to import from parent directory
import sys
sys.path.insert(0, '..')

import jim


def random_string(length: int):
    return ''.join(random.choice(string.ascii_letters+string.digits) for i in range(length))


class BaseTestCases:
    """
    Wrap test base classes not to execute tests
    """
    class MessageTestCase(unittest.TestCase):
        """
        Base test class for message tests - implements common fields testing (action and time).
        setUp() should be overridden to define a correct message with at least action and time fields.
        The other functions can be used as is.
        """
        def setUp(self) -> None:
            """
            You should override this and define a correct message with at least action and time fields
            :return: None
            """
            self.message = {"time": 1653130045655173000,
                            }

        def tearDown(self) -> None:
            pass

        def printTestResult(self, message: str):
            print(f"{self.__class__.__name__} - {self.__dict__['_testMethodName']}: {message}")

        def testAction_Missing_ValueError(self):
            with self.assertRaises(ValueError) as cm:
                self.message.pop(jim.MessageFields.ACTION)
                jim.Message.from_str(json.dumps(self.message))
            self.printTestResult(cm.exception)

        def testAction_Invalid_ValueError(self):
            with self.assertRaises(ValueError) as cm:
                self.message[jim.MessageFields.ACTION] = "some invalid action"
                jim.Message.from_str(json.dumps(self.message))
            self.printTestResult(cm.exception)

        def testTime_Missing_OK(self):
            self.message.pop(jim.MessageFields.TIME)
            jim.Message.from_str(json.dumps(self.message))
            self.printTestResult("OK")

        def testTime_InvalidType_ValueError(self):
            with self.assertRaises(ValueError) as cm:
                self.message[jim.MessageFields.TIME] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
                jim.Message.from_str(json.dumps(self.message))
            self.printTestResult(cm.exception)

        def test_OK(self):
            jim.Message.from_str(json.dumps(self.message))
            self.printTestResult("OK")


class TestMessage_Presence(BaseTestCases.MessageTestCase):
    """
    Presence message test class.
    Tests only message-specific fields, common fields testing is done in the base class
    """
    def setUp(self) -> None:
        self.message = {"action": "presence",
                        "time": 1653130045655173000,
                        "type": "status",
                        "user": {
                            "account_name": "test",
                            "status": "Online"}
                        }

    def testType_Missing_OK(self):
        self.message.pop(jim.MessageFields.TYPE)
        jim.Message.from_str(json.dumps(self.message))
        self.printTestResult("OK")

    def testType_InvalidType_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.TYPE] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message.pop(jim.MessageFields.USER)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_InvalidType_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_AccountName_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER].pop(jim.get_child_field_name(jim.MessageFields.USER_ACCOUNT_NAME))
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_AccountName_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER][jim.get_child_field_name(jim.MessageFields.USER_ACCOUNT_NAME)] \
                = random_string(jim.ACCOUNT_NAME_MAX_LENGTH + 1)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_Status_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER].pop(jim.get_child_field_name(jim.MessageFields.USER_STATUS))
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_Status_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER][jim.get_child_field_name(jim.MessageFields.USER_STATUS)] \
                = random_string(jim.OTHER_FIELDS_MAX_LENGTH + 1)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testRoom_Unexpected_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.ROOM] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)


class TestMessage_Probe(BaseTestCases.MessageTestCase):
    """
    Probe message test class.
    Tests only message-specific fields, common fields testing is done in the base class
    """
    def setUp(self) -> None:
        self.message = {"action": "probe",
                        "time": 1653130045655173000,
                        }

    def testRoom_Unexpected_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.ROOM] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)


class TestMessage_Msg(BaseTestCases.MessageTestCase):
    """
    Msg message test class.
    Tests only message-specific fields, common fields testing is done in the base class
    """
    def setUp(self) -> None:
        self.message = {"action": "msg",
                        "time": 1653130045655173000,
                        "to": "destination",
                        "from": "source",
                        "encoding": "ascii",
                        "message": "Hi! It's me."
                        }

    def testTo_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message.pop(jim.MessageFields.TO)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testTo_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.TO] = random_string(jim.ACCOUNT_NAME_MAX_LENGTH + 1)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testFrom_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message.pop(jim.MessageFields.FROM)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testFrom_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.FROM] = random_string(jim.ACCOUNT_NAME_MAX_LENGTH + 1)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testEncoding_Missing_OK(self):
        self.message.pop(jim.MessageFields.ENCODING)
        jim.Message.from_str(json.dumps(self.message))
        self.printTestResult("OK")

    def testEncoding_InvalidType_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.ENCODING] = random_string(jim.OTHER_FIELDS_MAX_LENGTH + 1)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testMessage_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message.pop(jim.MessageFields.MESSAGE)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testMessage_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.MESSAGE] = random_string(jim.MESSAGE_FIELD_MAX_LENGTH + 1)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testRoom_Unexpected_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.ROOM] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)


class TestMessage_Quit(BaseTestCases.MessageTestCase):
    """
    Quit message test class.
    Tests only message-specific fields, common fields testing is done in the base class
    """

    def setUp(self) -> None:
        self.message = {"action": "quit",
                        "time": 1653130045655173000,
                        }

    def testRoom_Unexpected_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.ROOM] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)


class TestMessage_Authenticate(BaseTestCases.MessageTestCase):
    """
    Authenticate message test class.
    Tests only message-specific fields, common fields testing is done in the base class
    """
    def setUp(self) -> None:
        self.message = {"action": "authenticate",
                        "time": 1653130045655173000,
                        "user": {
                            "account_name": "test",
                            "password": "verysecret"}
                        }

    def testUser_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message.pop(jim.MessageFields.USER)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_InvalidType_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_AccountName_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER].pop(jim.get_child_field_name(jim.MessageFields.USER_ACCOUNT_NAME))
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_AccountName_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER][jim.get_child_field_name(jim.MessageFields.USER_ACCOUNT_NAME)] \
                = random_string(jim.ACCOUNT_NAME_MAX_LENGTH + 1)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_Password_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER].pop(jim.get_child_field_name(jim.MessageFields.USER_PASSWORD))
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testUser_Password_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.USER][jim.get_child_field_name(jim.MessageFields.USER_PASSWORD)] \
                = random_string(jim.OTHER_FIELDS_MAX_LENGTH + 1)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testRoom_Unexpected_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.ROOM] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)


class TestMessage_Join(BaseTestCases.MessageTestCase):
    """
    Join message test class.
    Tests only message-specific fields, common fields testing is done in the base class
    """

    def setUp(self) -> None:
        self.message = {"action": "join",
                        "time": 1653130045655173000,
                        "room": "#darkroom"
                        }

    def testRoom_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message.pop(jim.MessageFields.ROOM)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testRoom_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.ROOM] = random_string(jim.ACCOUNT_NAME_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testRoom_InvalidLength_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.ROOM] = random_string(jim.ACCOUNT_NAME_MAX_LENGTH + 1)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)

    def testFrom_Unexpected_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.message[jim.MessageFields.FROM] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Message.from_str(json.dumps(self.message))
        self.printTestResult(cm.exception)


class TestMessage_Leave(TestMessage_Join):
    """
    Leave message test class.
    Based on the twin message type Join, changes only the message
    """

    def setUp(self) -> None:
        self.message = {"action": "leave",
                        "time": 1653130045655173000,
                        "room": "#lightroom"
                        }


class TestResponse(unittest.TestCase):

    def setUp(self) -> None:
        self.response = {"response": 200,
                         "time": 1653128454136720000,
                         "alert": "OK"
                         }

    def tearDown(self) -> None:
        pass

    def printTestResult(self, message: str):
        print(f"{self.__class__.__name__} - {self.__dict__['_testMethodName']}: {message}")

    def testResponse_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.response.pop(jim.ResponseFields.RESPONSE)
            jim.Response.from_str(json.dumps(self.response))
        self.printTestResult(cm.exception)

    def testResponse_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.response[jim.ResponseFields.RESPONSE] = "some invalid response"
            jim.Response.from_str(json.dumps(self.response))
        self.printTestResult(cm.exception)

    def testTime_Missing_OK(self):
        self.response.pop(jim.ResponseFields.TIME)
        jim.Response.from_str(json.dumps(self.response))
        self.printTestResult("OK")

    def testTime_InvalidType_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.response[jim.ResponseFields.TIME] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Response.from_str(json.dumps(self.response))
        self.printTestResult(cm.exception)

    def testAlert_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.response.pop(jim.ResponseFields.ALERT)
            jim.Response.from_str(json.dumps(self.response))
        self.printTestResult(cm.exception)

    def testAlert_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.response[jim.ResponseFields.ALERT] = random_string(jim.MESSAGE_FIELD_MAX_LENGTH + 1)
            jim.Response.from_str(json.dumps(self.response))
        self.printTestResult(cm.exception)

    def testError_Unexpected_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.response[jim.ResponseFields.ERROR] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Response.from_str(json.dumps(self.response))
        self.printTestResult(cm.exception)

    def testError_Missing_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.response[jim.ResponseFields.RESPONSE] = jim.Responses.SERVER_ERROR
            self.response.pop(jim.ResponseFields.ALERT)
            jim.Response.from_str(json.dumps(self.response))
        self.printTestResult(cm.exception)

    def testError_Invalid_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.response[jim.ResponseFields.RESPONSE] = jim.Responses.SERVER_ERROR
            self.response.pop(jim.ResponseFields.ALERT)
            self.response[jim.ResponseFields.ERROR] = random_string(jim.MESSAGE_FIELD_MAX_LENGTH + 1)
            jim.Response.from_str(json.dumps(self.response))
        self.printTestResult(cm.exception)

    def testAlert_Unexpected_ValueError(self):
        with self.assertRaises(ValueError) as cm:
            self.response[jim.ResponseFields.RESPONSE] = jim.Responses.SERVER_ERROR
            self.response[jim.ResponseFields.ERROR] = random_string(jim.OTHER_FIELDS_MAX_LENGTH)
            jim.Response.from_str(json.dumps(self.response))
        self.printTestResult(cm.exception)

    def test_OK(self):
        jim.Response.from_str(json.dumps(self.response))
        self.printTestResult("OK")



if __name__ == "__main__":
    unittest.main()
