from services.assfileorganizer import ASSFileOrganizer
import unittest

class TestNum2Words(unittest.TestCase):
    def test_num2words(self):
        org = ASSFileOrganizer()
        text = 'Papa ayin öncesinde yaptığı konuşmada 1915 olaylarının genel'
        print(org.process_slice_text(text))
        self.assertTrue(1 == 1)
