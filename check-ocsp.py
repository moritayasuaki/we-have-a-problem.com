#!/usr/bin/env python3
"""Read-only, on-demand OCSP diagnostic. Python 3, curl and OpenSSL/LibreSSL.

Three fixed public certificate queries; no retries or OS trust changes.
Embedded CA certificates authenticate responses only within this process.
This does not evaluate Safari, Apple trustd, or another device's connection.
"""
import datetime as dt
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

TARGETS = [{'label': 'EM DV TLS CA - G3B / emSign issuer', 'url': 'http://ocsp-b.emsign.com', 'cert': '-----BEGIN CERTIFICATE-----\nMIIDaDCCAu6gAwIBAgIQAKSu5njyM2K0wORgt3LyFDAKBggqhkjOPQQDAzBWMQsw\nCQYDVQQGEwJJTjElMCMGA1UECgwcZU11ZGhyYSBUZWNobm9sb2dpZXMgTGltaXRl\nZDEgMB4GA1UEAwwXZW1TaWduIFJvb3QgVExTIENBIC0gRzMwHhcNMjUwNDMwMTU1\nNDA4WhcNNDAwNDI4MTgzMDAwWjA/MQswCQYDVQQGEwJOTDETMBEGA1UECgwKZU11\nZGhyYSBCVjEbMBkGA1UEAwwSRU0gRFYgVExTIENBIC0gRzNCMHYwEAYHKoZIzj0C\nAQYFK4EEACIDYgAE557ZwEqXc8RzXlERHahawr1eZKs3S4DhLLwgOOweTw47gS/J\nhZ4eZ6+wTi+LyX90hbplqpEe6KTkW2LVzAPVa+Z4s8OMtNyTfKJGDiOEU8iSk10p\n1E+R4VYGtjzO2rRoo4IBljCCAZIwHwYDVR0jBBgwFoAU4TqrIXzx401UrtRyt/2L\nWUIgkFQwHQYDVR0OBBYEFOIeL+ccGTkOVUtiwSAkVzUkiiUUMB0GA1UdJQQWMBQG\nCCsGAQUFBwMBBggrBgEFBQcDAjBdBgNVHSAEVjBUMDkGCysGAQQBg44hAQABMCow\nKAYIKwYBBQUHAgEWHGh0dHA6Ly9yZXBvc2l0b3J5LmVtc2lnbi5jb20wDQYLKwYB\nBAGDjiEBAmQwCAYGZ4EMAQIBMHUGCCsGAQUFBwEBBGkwZzAkBggrBgEFBQcwAYYY\naHR0cDovL29jc3AtYi5lbXNpZ24uY29tMD8GCCsGAQUFBzAChjNodHRwOi8vcmVw\nb3NpdG9yeS5lbXNpZ24uY29tL2NlcnRzL0VNRFZUTFNDQUczQi5wN2MwNwYDVR0f\nBDAwLjAsoCqgKIYmaHR0cDovL2NybC5lbXNpZ24uY29tLz9yb290dGxzY2FnMy5j\ncmwwDgYDVR0PAQH/BAQDAgEGMBIGA1UdEwEB/wQIMAYBAf8CAQAwCgYIKoZIzj0E\nAwMDaAAwZQIwLmsGXi6oFMJ2klkcEMXMug6gvxQWZWkewiDWVzQyl2L6z6DuQfPO\nIbh1grvdULDCAjEAxZvLlxUavG69J6wnSjC8XBbqNIQsJ6CE2QdNOe84Ptxb6VG8\ngt2TlfJbHii+KNvK\n-----END CERTIFICATE-----\n', 'issuer': '-----BEGIN CERTIFICATE-----\nMIICKTCCAa+gAwIBAgIQDnYGcvFDRZ/I/gqwvAXjlDAKBggqhkjOPQQDAzBWMQsw\nCQYDVQQGEwJJTjElMCMGA1UECgwcZU11ZGhyYSBUZWNobm9sb2dpZXMgTGltaXRl\nZDEgMB4GA1UEAwwXZW1TaWduIFJvb3QgVExTIENBIC0gRzMwHhcNMjQwMjA4MDgx\nOTMyWhcNNDkwMjA3MDgxOTMyWjBWMQswCQYDVQQGEwJJTjElMCMGA1UECgwcZU11\nZGhyYSBUZWNobm9sb2dpZXMgTGltaXRlZDEgMB4GA1UEAwwXZW1TaWduIFJvb3Qg\nVExTIENBIC0gRzMwdjAQBgcqhkjOPQIBBgUrgQQAIgNiAARfD9w/q1cWxL6D9bMG\nH6CQ4u+gAV6GN9s+PwQx9Bl4hC+0iU8QOk8mWO/RwXQy10DCSxT8vSIJClHKp+Ao\n4qJKdYeV0SwZ7LMQziyLfxIUOY6Grja/sQFwLKYf8EdDXAyjQjBAMB0GA1UdDgQW\nBBThOqshfPHjTVSu1HK3/YtZQiCQVDAOBgNVHQ8BAf8EBAMCAQYwDwYDVR0TAQH/\nBAUwAwEB/zAKBggqhkjOPQQDAwNoADBlAjBhCFTkly7Yl7+s4hiw+k6ZJTXT2AiI\nrvmsmfqPr5E7ecwXb6kXA5LTFd6rjwTuV3sCMQC9w6ZSbVq1mveMO6dKFziOzClT\nKCT2RFT6yXtq6nzgRICgBmiXbJAXsmZ8yAwjyWc=\n-----END CERTIFICATE-----\n'}, {'label': 'EM DV TLS CA - G3B / AAA cross-sign', 'url': 'http://ocsp.comodoca.com', 'cert': '-----BEGIN CERTIFICATE-----\nMIIDzjCCAragAwIBAgIRAKAk/fS6Zlx4XOSgIEg4WLcwDQYJKoZIhvcNAQELBQAw\nezELMAkGA1UEBhMCR0IxGzAZBgNVBAgMEkdyZWF0ZXIgTWFuY2hlc3RlcjEQMA4G\nA1UEBwwHU2FsZm9yZDEaMBgGA1UECgwRQ29tb2RvIENBIExpbWl0ZWQxITAfBgNV\nBAMMGEFBQSBDZXJ0aWZpY2F0ZSBTZXJ2aWNlczAeFw0yNTA1MTQwMDAwMDBaFw0y\nODEyMzEyMzU5NTlaMD8xCzAJBgNVBAYTAk5MMRMwEQYDVQQKDAplTXVkaHJhIEJW\nMRswGQYDVQQDDBJFTSBEViBUTFMgQ0EgLSBHM0IwdjAQBgcqhkjOPQIBBgUrgQQA\nIgNiAATnntnASpdzxHNeUREdqFrCvV5kqzdLgOEsvCA47B5PDjuBL8mFnh5nr7BO\nL4vJf3SFumWqkR7opORbYtXMA9Vr5nizw4y03JN8okYOI4RTyJKTXSnUT5HhVga2\nPM7atGijggE1MIIBMTAfBgNVHSMEGDAWgBSgEQojPpbxB+zirynvgqV/0DCktDAd\nBgNVHQ4EFgQU4h4v5xwZOQ5VS2LBICRXNSSKJRQwDgYDVR0PAQH/BAQDAgEGMBIG\nA1UdEwEB/wQIMAYBAf8CAQAwHQYDVR0lBBYwFAYIKwYBBQUHAwEGCCsGAQUFBwMC\nMDEGA1UdIAQqMCgwCAYGZ4EMAQIBMA0GCysGAQQBg44hAQABMA0GCysGAQQBg44h\nAQJkMEMGA1UdHwQ8MDowOKA2oDSGMmh0dHA6Ly9jcmwuY29tb2RvY2EuY29tL0FB\nQUNlcnRpZmljYXRlU2VydmljZXMuY3JsMDQGCCsGAQUFBwEBBCgwJjAkBggrBgEF\nBQcwAYYYaHR0cDovL29jc3AuY29tb2RvY2EuY29tMA0GCSqGSIb3DQEBCwUAA4IB\nAQBzQ1IoqpdotM6gFrR4Q3YrKifOLeaj5XXunldpVE/vZn2TxC2y0s8oYiLR5ICE\nwqVXSB7N6BM1Mp+Nif7Jbhb2IswAfSR4Iik8+B0iRmi7lYoNlycCgHjmsjOmZaxM\nQkPmjXAJbG5f4V41OsvJZmS7lI3r0IuvEDVX3GAZ13on6IImSs9ybNpHQ7NCqkMQ\n7wH4uAO1dtpFycgJSdHaCOhHjrox2BTYGLdpUrYwY3EOAjlZ8UGgsxs7mG+xquMl\nbN1LFURwfnkVMP3T/DBIZ/ys2+lNFyxK3FlArrV4/000uTnVB1lO8oGORYdXoT5V\nGUyRCEIDhF5TBUuKF4E3kf1h\n-----END CERTIFICATE-----\n', 'issuer': '-----BEGIN CERTIFICATE-----\nMIIEMjCCAxqgAwIBAgIBATANBgkqhkiG9w0BAQUFADB7MQswCQYDVQQGEwJHQjEb\nMBkGA1UECAwSR3JlYXRlciBNYW5jaGVzdGVyMRAwDgYDVQQHDAdTYWxmb3JkMRow\nGAYDVQQKDBFDb21vZG8gQ0EgTGltaXRlZDEhMB8GA1UEAwwYQUFBIENlcnRpZmlj\nYXRlIFNlcnZpY2VzMB4XDTA0MDEwMTAwMDAwMFoXDTI4MTIzMTIzNTk1OVowezEL\nMAkGA1UEBhMCR0IxGzAZBgNVBAgMEkdyZWF0ZXIgTWFuY2hlc3RlcjEQMA4GA1UE\nBwwHU2FsZm9yZDEaMBgGA1UECgwRQ29tb2RvIENBIExpbWl0ZWQxITAfBgNVBAMM\nGEFBQSBDZXJ0aWZpY2F0ZSBTZXJ2aWNlczCCASIwDQYJKoZIhvcNAQEBBQADggEP\nADCCAQoCggEBAL5AnfRu4ep2hxxNRUSOvkbIgwadwSr+GB+O5AL686tdUIoWMQua\nBtDFcCLNSS1UY8y2bmhGC1Pqy0wkwLxyTurxFa70VJoSCsN6sjNg4tqJVfMiWPPe\n3M/vg4aijJRPn2jymJBGhCfHdr/jzDUsi14HZGWCwEiwqJH5YZ92IFCokcdmtet4\nYgNW8IoaE+oxox6gmf049vYnMlhvB/VruPsUK6+3qszWY19zjNoFmag4qMsXeDZR\nrOme9Hg6jc8P2ULimAyrL58OAd7vn5lJ8S3frHRNG5i1R8XlKdH5kBjHYpy+g8cm\nez6KJcfA3Z3mNWgQIJ2P2N7Sw4ScDV7oL8kCAwEAAaOBwDCBvTAdBgNVHQ4EFgQU\noBEKIz6W8Qfs4q8p74Klf9AwpLQwDgYDVR0PAQH/BAQDAgEGMA8GA1UdEwEB/wQF\nMAMBAf8wewYDVR0fBHQwcjA4oDagNIYyaHR0cDovL2NybC5jb21vZG9jYS5jb20v\nQUFBQ2VydGlmaWNhdGVTZXJ2aWNlcy5jcmwwNqA0oDKGMGh0dHA6Ly9jcmwuY29t\nb2RvLm5ldC9BQUFDZXJ0aWZpY2F0ZVNlcnZpY2VzLmNybDANBgkqhkiG9w0BAQUF\nAAOCAQEACFb8AvCb6P+k+tZ7xkSAzk/ExfYAWMymtrwUSWgEdujm7l3sAg9g1o1Q\nGE8mTgHj5rCl7r+8dFRBv/38ErjHT1r0iWAFf2C3BUrz9vHCv8S5dIa2LX1rzNLz\nRt0vxuBqw8M0Ayx9lt1awg6nCpnBBYurDC/zXDrPbDdVCYfeU0BsWO/8tqtlbgT2\nG9w84FoVxp7Z8VlIMCFlA2zs6SFz7JsDoeA3raAVGI/6ugLOpyypEBMs1OUIJqsi\nl2D4kF501KKaU73yqWjgom7C12yxow+ev+to51byrvLjKzg6CYG1a4XXvi3tPxq3\nsmPi9WIsgtRqAEFQ8TmDn5XpNpaYbg==\n-----END CERTIFICATE-----\n'}, {'label': 'emSign Root TLS CA - G3 / ECC G3 cross-sign', 'url': 'http://ocsp.emsign.com', 'cert': '-----BEGIN CERTIFICATE-----\nMIIDdDCCAvmgAwIBAgIQAJYaPvsTWVdu0EAFtGhKWzAKBggqhkjOPQQDAzBrMQsw\nCQYDVQQGEwJJTjETMBEGA1UECxMKZW1TaWduIFBLSTElMCMGA1UEChMcZU11ZGhy\nYSBUZWNobm9sb2dpZXMgTGltaXRlZDEgMB4GA1UEAxMXZW1TaWduIEVDQyBSb290\nIENBIC0gRzMwHhcNMjQwNzExMTU0MzM2WhcNMzkwNzA5MTgzMDAwWjBWMQswCQYD\nVQQGEwJJTjElMCMGA1UECgwcZU11ZGhyYSBUZWNobm9sb2dpZXMgTGltaXRlZDEg\nMB4GA1UEAwwXZW1TaWduIFJvb3QgVExTIENBIC0gRzMwdjAQBgcqhkjOPQIBBgUr\ngQQAIgNiAARfD9w/q1cWxL6D9bMGH6CQ4u+gAV6GN9s+PwQx9Bl4hC+0iU8QOk8m\nWO/RwXQy10DCSxT8vSIJClHKp+Ao4qJKdYeV0SwZ7LMQziyLfxIUOY6Grja/sQFw\nLKYf8EdDXAyjggF1MIIBcTAfBgNVHSMEGDAWgBR8XQKEE9TMipuBzhccLikenEhj\nQjAdBgNVHQ4EFgQU4TqrIXzx401UrtRyt/2LWUIgkFQwHQYDVR0lBBYwFAYIKwYB\nBQUHAwEGCCsGAQUFBwMCMD0GA1UdIAQ2MDQwMgYEVR0gADAqMCgGCCsGAQUFBwIB\nFhxodHRwOi8vcmVwb3NpdG9yeS5lbXNpZ24uY29tMHgGCCsGAQUFBwEBBGwwajAi\nBggrBgEFBQcwAYYWaHR0cDovL29jc3AuZW1zaWduLmNvbTBEBggrBgEFBQcwAoY4\naHR0cDovL3JlcG9zaXRvcnkuZW1zaWduLmNvbS9jZXJ0cy9lbVNpZ25FQ0NSb290\nQ0FHMy5jcnQwMwYDVR0fBCwwKjAooCagJIYiaHR0cDovL2NybC5lbXNpZ24uY29t\nP1Jvb3RDQUczLmNybDAOBgNVHQ8BAf8EBAMCAQYwEgYDVR0TAQH/BAgwBgEB/wIB\nATAKBggqhkjOPQQDAwNpADBmAjEAt9CIpRGp46QHQYDUBnLKw+vvK0/h9vmilEAg\nTroUl/anH4x2rXHqiCtBTBfgKDegAjEA8WpG1LTZdAIL0FSYqxXeREaeTSxEofM0\n1jJH3jGvCXC79LU9UPJ2o3TU+UIj2gMV\n-----END CERTIFICATE-----\n', 'issuer': '-----BEGIN CERTIFICATE-----\nMIICTjCCAdOgAwIBAgIKPPYHqWhwDtqLhDAKBggqhkjOPQQDAzBrMQswCQYDVQQG\nEwJJTjETMBEGA1UECxMKZW1TaWduIFBLSTElMCMGA1UEChMcZU11ZGhyYSBUZWNo\nbm9sb2dpZXMgTGltaXRlZDEgMB4GA1UEAxMXZW1TaWduIEVDQyBSb290IENBIC0g\nRzMwHhcNMTgwMjE4MTgzMDAwWhcNNDMwMjE4MTgzMDAwWjBrMQswCQYDVQQGEwJJ\nTjETMBEGA1UECxMKZW1TaWduIFBLSTElMCMGA1UEChMcZU11ZGhyYSBUZWNobm9s\nb2dpZXMgTGltaXRlZDEgMB4GA1UEAxMXZW1TaWduIEVDQyBSb290IENBIC0gRzMw\ndjAQBgcqhkjOPQIBBgUrgQQAIgNiAAQjpQy4LRL1KPOxst3iAhKAnjlfSU2fySU0\nWXTsuwYc58Byr+iuL+FBVIcUqEqy6HyC5ltqtdyzdc6LBtCGI79G1Y4PPwT01xyS\nfvalY8L1X44uT6EYGQIrMgqCZH0Wk9GjQjBAMB0GA1UdDgQWBBR8XQKEE9TMipuB\nzhccLikenEhjQjAOBgNVHQ8BAf8EBAMCAQYwDwYDVR0TAQH/BAUwAwEB/zAKBggq\nhkjOPQQDAwNpADBmAjEAvvNhzwIQHWSVB7gYboiFBS+DCBeQyh+KTOgNG3qxrdWB\nCUfvO6wIBHxcmbHtRwfSAjEAnbpV/KlK6O3t5nYBQnvI+GDZjVGLVTv7jHvrZQnD\n+JbNR6iC8hZVdyR+EhCVBCyj\n-----END CERTIFICATE-----\n'}]
LIMIT = 262144


def run(args, **kwargs):
    return subprocess.run(args, capture_output=True, timeout=15,
                          env={**os.environ, 'LC_ALL': 'C'}, **kwargs)


def classify(returncode, output, now=None):
    """Fail closed on authenticity, certificate matching, or freshness errors."""
    if returncode or 'Response verify OK' not in output:
        return 'unverified'
    match = re.search(r'^target\.pem: (good|revoked|unknown)\s*$', output, re.M)
    if not match or re.search(r'WARNING|ERROR|invalid|expired', output, re.I):
        return 'unverified'
    now = now or dt.datetime.now(dt.timezone.utc)
    times = {}
    for field in ('This Update', 'Next Update'):
        value = re.search(r'^\s*' + field + r': (.+)$', output, re.M)
        if value:
            try:
                times[field] = dt.datetime.strptime(value[1].strip(), '%b %d %H:%M:%S %Y GMT').replace(tzinfo=dt.timezone.utc)
            except ValueError:
                return 'unverified'
    if 'This Update' not in times or times['This Update'] > now + dt.timedelta(minutes=5):
        return 'unverified'
    if 'Next Update' in times:
        if times['Next Update'] < now - dt.timedelta(minutes=5) or times['Next Update'] < times['This Update']:
            return 'unverified'
    elif now - times['This Update'] > dt.timedelta(days=1):
        return 'unverified'
    return match[1]


def probe(target, openssl, curl):
    result = {'target': target['label'], 'url': target['url'],
              'http': 'unconfirmed', 'ocsp': 'unverified'}
    with tempfile.TemporaryDirectory(prefix='emudhra-ocsp-') as directory:
        path = Path(directory)
        (path / 'target.pem').write_text(target['cert'])
        (path / 'issuer.pem').write_text(target['issuer'])
        (path / 'empty-ca').mkdir()
        request = run([openssl, 'ocsp', '-issuer', 'issuer.pem', '-cert', 'target.pem',
                       '-no_nonce', '-reqout', 'request.der'], cwd=directory)
        if request.returncode:
            result['detail'] = 'OCSP request could not be prepared / リクエスト作成を確認できません'
            return result
        # Fixed URLs from the certificates' AIA. No redirects; bounded time and size.
        response = run([curl, '--disable', '--silent', '--show-error', '--proto', '=http',
                        '--connect-timeout', '5', '--max-time', '10', '--max-filesize', str(LIMIT),
                        '--max-redirs', '0', '--header', 'Content-Type: application/ocsp-request',
                        '--header', 'Accept: application/ocsp-response',
                        '--data-binary', '@request.der', '--output', 'response.der',
                        '--write-out', '%{http_code}', target['url']], cwd=directory)
        code = response.stdout.decode('ascii', 'replace').strip()
        if re.fullmatch(r'[1-5][0-9]{2}', code):
            result['http'] = code
        if response.returncode or code != '200':
            result['detail'] = 'No usable OCSP response / 利用できるOCSP応答を確認できません'
            return result
        if not (path / 'response.der').is_file() or (path / 'response.der').stat().st_size > LIMIT:
            return result
        verified = run([openssl, 'ocsp', '-issuer', 'issuer.pem', '-cert', 'target.pem',
                        '-respin', 'response.der', '-no_nonce', '-CAfile', 'issuer.pem',
                        '-CApath', 'empty-ca', '-validity_period', '300'],
                       cwd=directory)
        output = (verified.stdout + verified.stderr).decode('utf-8', 'replace')
        result['ocsp'] = classify(verified.returncode, output)
        # Only recognized date/status fields are shown, never arbitrary server text.
        result['dates'] = re.findall(r'^\s*(?:This Update|Next Update|Revocation Time): [A-Za-z0-9 :]+$', output, re.M)
    return result


def main():
    openssl, curl = shutil.which('openssl'), shutil.which('curl')
    if not openssl or not curl:
        raise SystemExit('Requires Python 3, curl and OpenSSL/LibreSSL / Python 3・curl・OpenSSLまたはLibreSSLが必要です')
    print('OCSP response check / OCSP応答の確認')
    print(dt.datetime.now(dt.timezone.utc).isoformat())
    print('From this tool and network; HTTP/proxy routing may differ from the OS.\n'
          'このツール・回線からの確認です。プロキシなどの通信経路はOSと異なる場合があります。')
    print('Queries 3 public certificates once each. No system settings are changed.\n'
          '公開証明書3件を各1回照会します。システム設定は変更しません。')
    labels = {'revoked': 'Signed revocation response / 署名・時刻を確認した失効応答',
              'good': 'Signed good response for this certificate / この証明書への署名・時刻を確認したgood応答',
              'unknown': 'Signed unknown response / 署名・時刻を確認したunknown応答',
              'unverified': 'Status unconfirmed / 失効状態は未確認'}
    for target in TARGETS:
        try:
            result = probe(target, openssl, curl)
        except (OSError, subprocess.TimeoutExpired):
            result = {'target': target['label'], 'url': target['url'],
                      'http': 'unconfirmed', 'ocsp': 'unverified'}
        print('\n' + result['target'] + '\n' + result['url'])
        print('HTTP: ' + result['http'] + '\n' + labels[result['ocsp']])
        for date in result.get('dates', []):
            print(date.strip())
    print('\nHTTP response ≠ verified OCSP status ≠ browser protection.\n'
          'HTTP応答・署名付きの失効応答・ブラウザの保護状態は、それぞれ別の確認です。\n'
          'A failure can involve DNS, routing, a proxy, server or tool; it does not establish an outage.\n'
          '失敗時はDNS・経路・プロキシ・サーバー・ツールなどの切り分けが必要です。')


if __name__ == '__main__':
    main()
