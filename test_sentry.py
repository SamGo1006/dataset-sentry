import io
import json
import subprocess
import sys
import unittest
from sentry import audit

class AuditTests(unittest.TestCase):
    def check_csv(self, text, rules, **kw):
        return audit(io.StringIO(text), rules, **kw)
    def test_valid_quoted_data(self):
        self.assertTrue(self.check_csv('id,name\n1,"Sam, Jr"\n',
            {'id': {'type': 'integer', 'unique': True}, 'name': {'required': True}})['valid'])
    def test_typed_duplicates(self):
        r = self.check_csv('id\n1\n01\n', {'id': {'type': 'integer', 'unique': True}})
        self.assertEqual(r['issues'], [{'row': 3, 'column': 'id', 'code': 'duplicate'}])
    def test_nonfinite_and_range(self):
        r = self.check_csv('x\nNaN\nInfinity\n-1\n11\n', {'x': {'type':'number','min':0,'max':10}})
        self.assertEqual([i['code'] for i in r['issues']], ['type','type','min','max'])
    def test_dates_required_and_enum(self):
        r = self.check_csv('d,state\n2025-02-30,unknown\n,open\n',
            {'d': {'type':'date','required':True}, 'state': {'enum':['open','closed']}})
        self.assertEqual(r['issue_count'], 3)
    def test_shape_and_truncation(self):
        r = self.check_csv('a,b\nx\ny,z,extra\n', {'b': {'required': True}}, max_issues=1)
        self.assertEqual(r['issue_count'], 3)
        self.assertTrue(r['truncated'])
        self.assertEqual(len(r['issues']), 1)
    def test_bad_header(self):
        for text in ('a,a\n1,2\n','', 'b\n1\n'):
            with self.assertRaises(ValueError): self.check_csv(text, {'a': {}})
    def test_bad_schema(self):
        for schema in ([], {}, {'a':{'type':'magic'}}, {'a':{'min':2}}, {'a':{'required':'yes'}}):
            with self.assertRaises(ValueError): self.check_csv('a\n1\n', schema)
    def test_cli_codes(self):
        for file, code in [('clean.csv',0),('dirty.csv',1),('absent.csv',2)]:
            p = subprocess.run([sys.executable,'sentry.py','examples/'+file,'examples/schema.json'],
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, code, p.stderr)
            if code != 2: self.assertIn('valid', json.loads(p.stdout))

if __name__ == '__main__': unittest.main()
