"""Offline fixtures: generated temporary test keys never leave the test directory."""
import datetime as dt
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('checker',Path(__file__).resolve().parents[1]/'check-ocsp.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
OPENSSL=os.environ.get('TEST_OPENSSL',shutil.which('openssl'))

class OCSPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.path=Path(cls.tmp.name)
        def run(*args):
            return subprocess.run([shutil.which('openssl'),*args],cwd=cls.path,check=True,capture_output=True)
        cls.runssl=staticmethod(run)
        run('req','-x509','-newkey','rsa:2048','-nodes','-subj','/CN=Offline Test CA','-days','2','-keyout','ca.key','-out','issuer.pem')
        run('req','-new','-newkey','rsa:2048','-nodes','-subj','/CN=Offline Target','-keyout','target.key','-out','target.csr')
        run('x509','-req','-in','target.csr','-CA','issuer.pem','-CAkey','ca.key','-set_serial','1','-days','1','-out','target.pem')
        run('ocsp','-issuer','issuer.pem','-cert','target.pem','-no_nonce','-reqout','request.der')
        now=dt.datetime.now(dt.timezone.utc)
        expiry=(now+dt.timedelta(days=1)).strftime('%y%m%d%H%M%SZ')
        revoked=(now-dt.timedelta(hours=1)).strftime('%y%m%d%H%M%SZ')
        for state,line in [('good',f'V\t{expiry}\t\t01\tunknown\t/CN=Offline Target\n'),('revoked',f'R\t{expiry}\t{revoked}\t01\tunknown\t/CN=Offline Target\n'),('unknown','')]:
            (cls.path/'index').write_text(line)
            run('ocsp','-index','index','-CA','issuer.pem','-rsigner','issuer.pem','-rkey','ca.key','-reqin','request.der','-ndays','1','-respout',state+'.der')
        (cls.path/'empty-ca').mkdir()

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def verify(self,name):
        r=subprocess.run([OPENSSL,'ocsp','-issuer','issuer.pem','-cert','target.pem','-respin',name,'-no_nonce','-CAfile','issuer.pem','-CApath','empty-ca','-validity_period','300'],cwd=self.path,capture_output=True)
        return r.returncode,(r.stdout+r.stderr).decode()

    def test_signed_statuses(self):
        for status in ['good','revoked','unknown']:
            with self.subTest(status=status):
                code,text=self.verify(status+'.der');self.assertEqual(checker.classify(code,text),status,text)

    def test_tampered_signature(self):
        self.runssl('ocsp','-index','index','-CA','issuer.pem','-rsigner','issuer.pem','-rkey','ca.key','-reqin','request.der','-ndays','1','-badsig','-respout','bad.der')
        self.assertEqual(checker.classify(*self.verify('bad.der')),'unverified')

    def test_malformed_response(self):
        (self.path/'bad.der').write_text('<html>Blocked</html>')
        self.assertEqual(checker.classify(*self.verify('bad.der')),'unverified')

    def test_stale_and_future(self):
        code,text=self.verify('revoked.der')
        now=dt.datetime.now(dt.timezone.utc)
        for instant in [now+dt.timedelta(days=3),now-dt.timedelta(days=3)]:
            self.assertEqual(checker.classify(code,text,instant),'unverified')

    def test_wrong_certificate(self):
        r=subprocess.run([OPENSSL,'ocsp','-issuer','issuer.pem','-serial','2','-respin','revoked.der','-no_nonce','-CAfile','issuer.pem'],cwd=self.path,capture_output=True)
        self.assertEqual(checker.classify(r.returncode,(r.stdout+r.stderr).decode()),'unverified')

    def test_http_error_and_timeout(self):
        original=checker.run
        try:
            def mock(args,**kw):
                if args[0]=='curl':return subprocess.CompletedProcess(args,0,b'403',b'')
                return subprocess.CompletedProcess(args,0,b'',b'')
            checker.run=mock
            r=checker.probe(checker.TARGETS[0],'openssl','curl')
            self.assertEqual((r['http'],r['ocsp']),('403','unverified'))
            def timeout(args,**kw):
                if args[0]=='curl':return subprocess.CompletedProcess(args,28,b'000',b'')
                return subprocess.CompletedProcess(args,0,b'',b'')
            checker.run=timeout
            r=checker.probe(checker.TARGETS[0],'openssl','curl')
            self.assertEqual((r['http'],r['ocsp']),('unconfirmed','unverified'))
        finally:checker.run=original

if __name__=='__main__':unittest.main()
