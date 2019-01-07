import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth

import psycopg2
import json
import datetime
import os


class FirebaseAuth:

    def __init__(self):
        obj = {
            "type": os.environ.get('type'),
            "project_id": os.environ.get('project_id'),
            "private_key_id": os.environ.get('private_key_id'),
            "private_key": os.environ.get('private_key'),
            "client_email": os.environ.get('client_email'),
            "client_id": os.environ.get('client_id'),
            "auth_uri": os.environ.get('auth_uri'),
            "token_uri": os.environ.get('token_uri'),
            "auth_provider_x509_cert_url": os.environ.get('auth_provider_x509_cert_url'),
            "client_x509_cert_url": os.environ.get('client_x509_cert_url'),
        }
        cred = credentials.Certificate(obj)
        self.default = firebase_admin.initialize_app(cred)


        self.config = {
            'host':os.environ.get('host'),
            'database':os.environ.get('database'),
            'user':os.environ.get('user'),
            'password':os.environ.get('password')
        }
        self.conn = psycopg2.connect(host=self.config['host'], database=self.config['database'], user=self.config['user'], password=self.config['password'])

    def verifyToken(self, token, uid):
        dec_tok = auth.verify_id_token(token)
        uid_v = dec_tok['uid']
        return uid_v == uid

    def checkToken(self, token, uid):
        cur = self.conn.cursor()
        cur.execute('select * from tokens where uid=%s', [uid])
        try:
            res = cur.fetchall()[0]
            return res[1]==token
        except:
            return False

    def addTokenToDatabase(self, token, uid, cuid):
        cur = self.conn.cursor()
        cur.execute('select exists(select 1 from tokens where uid=%s)', [uid])
        chckusr = cur.fetchall()
        exptime = datetime.datetime.now()+datetime.timedelta(seconds=7149)
        if chckusr[0][0]:
            print('Updating user token')
            cur.execute('UPDATE tokens SET cu_token=%s, cu_expire=%s WHERE uid=%s', [token, exptime, uid])
        else:
            print('Inserting new token')
            cur.execute('INSERT INTO tokens (uid, cu_token, cu_expire, cu_uid) VALUES(%s, %s, %s, %s)', [uid, token, exptime, cuid])
        self.conn.commit()

    def getCUInfo(self, uid):
        cur = self.conn.cursor()
        cur.execute('select * from tokens where uid=%s', [uid])
        try:
            res = cur.fetchall()[0]
            return res
        except:
            return None
