import unittest

# Necessary to import from parent directory
import sys
sys.path.insert(0, '..')

import jim


class TestMessage(unittest.TestCase):
    def setUp(self) -> None:
        pass

    def tearDown(self) -> None:
        pass

    def testBadString(self):
        message_str = '{"action": "presense", "time": 1653130045655173000, "type": "status", ' \
                      '"user": {"account_name": "test", "status": "Online"}}'
        with self.assertRaises(ValueError):
            jim.Message.from_str(message_str)

    def testGoodString(self):
        message_str = '{"action": "presence", "time": 1653130045655173000, "type": "status", ' \
                      '"user": {"account_name": "test", "status": "Online"}}'
        raised = False
        try:
            jim.Message.from_str(message_str)
        except:
            raised = True
        self.assertFalse(raised, msg="Good Message init string raised an exception")


class TestResponse(unittest.TestCase):
    def testBadString(self):
        response_str = '{"response": 234, "time": 1653128454136720000, "alert": "OK"}'
        with self.assertRaises(ValueError):
            jim.Response.from_str(response_str)

    def testGoodString(self):
        response_str = '{"response": 200, "time": 1653128454136720000, "alert": "OK"}'
        raised = False
        try:
            jim.Response.from_str(response_str)
        except:
            raised = True
        self.assertFalse(raised, msg="Good Response init string raised an exception")


if __name__ == "__main__":
    unittest.main()
