import unittest
from secondmate.utils import sanitize_for_serialization

class TestUtils(unittest.TestCase):
    def test_sanitize_primitives(self):
        self.assertEqual(sanitize_for_serialization(1), 1)
        self.assertEqual(sanitize_for_serialization(1.5), 1.5)
        self.assertEqual(sanitize_for_serialization("string"), "string")
        self.assertEqual(sanitize_for_serialization(True), True)
        self.assertEqual(sanitize_for_serialization(None), None)

    def test_sanitize_dictionary(self):
        input_dict = {1: "one", "two": 2}
        expected_dict = {"1": "one", "two": 2}
        self.assertEqual(sanitize_for_serialization(input_dict), expected_dict)

    def test_sanitize_list_and_tuple(self):
        input_list = [1, "two", 3.0]
        self.assertEqual(sanitize_for_serialization(input_list), input_list)

        input_tuple = (1, "two", 3.0)
        self.assertEqual(sanitize_for_serialization(input_tuple), input_tuple)

    def test_sanitize_bytes(self):
        # Valid utf-8
        valid_bytes = b"hello"
        self.assertEqual(sanitize_for_serialization(valid_bytes), "hello")

        # Invalid utf-8 (0xFF is not a valid start byte)
        invalid_bytes = b"\xff\xfe"
        # Should be base64 encoded string
        import base64
        expected_b64 = base64.b64encode(invalid_bytes).decode('utf-8')
        self.assertEqual(sanitize_for_serialization(invalid_bytes), expected_b64)

        # Bytearray
        valid_bytearray = bytearray(b"world")
        self.assertEqual(sanitize_for_serialization(valid_bytearray), "world")

        invalid_bytearray = bytearray(b"\xff\xfe")
        self.assertEqual(sanitize_for_serialization(invalid_bytearray), expected_b64)

    def test_sanitize_nested_structures(self):
        import base64
        invalid_bytes = b"\xff\xfe"
        expected_b64 = base64.b64encode(invalid_bytes).decode('utf-8')

        input_nested = {
            1: [b"hello", invalid_bytes],
            "tuple": (1, {2: "val"}),
            "nested_dict": {"inner": b"world"}
        }

        expected_nested = {
            "1": ["hello", expected_b64],
            "tuple": (1, {"2": "val"}),
            "nested_dict": {"inner": "world"}
        }

        self.assertEqual(sanitize_for_serialization(input_nested), expected_nested)

if __name__ == "__main__":
    unittest.main()
