import unittest
from data_export import serialize_csv

class CsvExportTests(unittest.TestCase):
    def test_quote_and_newline(self):
        self.assertEqual(serialize_csv([('one,"two"','first\nsecond')], ['name','note']),
                         '"name","note"\r\n"one,""two""","first\nsecond"\r\n')
    def test_formula_injection(self):
        for value in ('=1+1','+cmd','-cmd','@external','  =1+1'):
            with self.subTest(value=value):
                self.assertIn('"\'' + value + '"', serialize_csv([(value,)], ['value']))
    def test_null_and_empty(self):
        self.assertEqual(serialize_csv([(None,)], ['value']),
                         '"value"\r\n""\r\n')
