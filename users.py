import firebase_admin
from firebase_admin import credentials
from firebase_admin import auth

import psycopg2
import json
import datetime
import os
import uuid


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
        while obj['private_key'].find('\\n')>-1:
            obj['private_key'] = obj['private_key'].replace('\\n', '\n')
        cred = credentials.Certificate(obj)
        self.default = firebase_admin.initialize_app(cred)


        self.config = {
            'host':os.environ.get('host'),
            'database':os.environ.get('database'),
            'user':os.environ.get('user'),
            'password':os.environ.get('password')
        }
        self.conn = psycopg2.connect(host=self.config['host'], database=self.config['database'], user=self.config['user'], password=self.config['password'])

    def __del__(self):
        self.conn.close()

    #Verify the Google token is for the UID and valid
    def verifyToken(self, token, uid):
        dec_tok = auth.verify_id_token(token)
        uid_v = dec_tok['uid']
        return uid_v == uid

    #Verify the cu token matches the one in the database => user can only be logged in one place at a time, maybe not neccesary
    def checkToken(self, token, uid):
        cur = self.conn.cursor()
        try:
            cur.execute('select * from tokens where uid=%s', [uid])
            res = cur.fetchall()[0]
            self.conn.commit()
            return res[1]==token
        except:
            self.conn.rollback()
            return False

    #Return the cu id matching the cu token from the database
    def getCIDToken(self, token):
        cur = self.conn.cursor()
        try:
            cur.execute('select * from tokens where cu_token=%s', [token])
            res = cur.fetchall()[0]
            self.conn.commit()
            return res[3]
        except:
            self.conn.rollback()
            return None

    #Set the cu token and expiration for the UID
    def addTokenToDatabase(self, token, uid, cuid):
        cur = self.conn.cursor()
        try:
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
        except:
            self.conn.rollback()

    #Return database row for UID
    def getCUInfo(self, uid):
        cur = self.conn.cursor()
        try:
            cur.execute('SELECT * FROM tokens WHERE uid=%s', [uid])
            res = cur.fetchall()[0]
            self.conn.commit()
            return res
        except:
            self.conn.rollback()
            return None

    #Check if uid has a nonexpired token to prevent spending time acquiring a new one
    def checkCUTokenExpire(self, uid):
        cur = self.conn.cursor()
        try:
            cur.execute('select * from tokens where uid=%s', [uid])
            res = cur.fetchall()[0]
            self.conn.commit()
            tk = res[1]
            exp = res[2].replace(tzinfo=None)
            if datetime.datetime.now()<exp:
                return tk
            return False
        except Exception as e:
            print(e)
            self.conn.rollback()
            return False

    #Delete all section entries for uid, and write new ones
    def saveSectList(self, uid, saved):
        saved = json.loads(saved)
        cur = self.conn.cursor()
        try:
            cur.execute('DELETE FROM saved_sections WHERE uid=%s', [uid])
            self.conn.commit()
            for s in saved:
                self.addSectionToSaved(uid, s)
        except:
            self.conn.rollback()

    #Write one section entry
    def addSectionToSaved(self, uid, sect):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO saved_sections (uid, code, meeting_html, hours_text, crn, section) VALUES(%s, %s, %s, %s, %s, %s)',
            [uid, sect['code'], sect['meeting_html'], sect['hours_text'], sect['crn'], sect['section']])
        self.conn.commit()

    #Read and return all section entries for uid
    def loadSectList(self, uid):
        cur = self.conn.cursor()
        try:
            cur.execute('SELECT * FROM saved_sections WHERE uid=%s', [uid])
            res = cur.fetchall()
            self.conn.commit()
            ret = [{'code':r[1], 'meeting_html':r[2], 'hours_text':r[3], 'crn':r[4], 'section':r[5]} for r in res]
            return ret
        except Exception as e:
            print(e)
            self.conn.rollback()
            return "Something went wrong"

    def loadOldList(self, uid):
        cur = self.conn.cursor()
        try:
            cur.execute('SELECT * FROM old_courses WHERE uid=%s', [uid])
            res = cur.fetchall()
            self.conn.commit()
            ret = [{'Term':r[1], 'Year':r[2], 'Subject':r[3], 'Course':r[4], 'Section':r[5], 'Instructor_Name':r[6], 'Grade':r[7]} for r in res]
            return ret
        except Exception as e:
            print(e)
            self.conn.rollback()
            return "Something went wrong"

    def saveOldList(self, uid, saved):
        saved = json.loads(saved)
        cur = self.conn.cursor()
        cur.execute('DELETE FROM old_courses WHERE uid=%s', [uid])
        self.conn.commit()
        for s in saved:
            self.addCourseToSaved(uid, s)

    def addCourseToSaved(self, uid, course):
        cur = self.conn.cursor()
        cur.execute('INSERT INTO old_courses (uid, term, year, subject, course, section, instructor, grade) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)',
                    [uid, course['term'], course['year'], course['subject'], course['course'], course['section'], course['instructor'], course['grade']])
        self.conn.commit()

    def makeShareUrl(self, courses):
        guid = uuid.uuid4().hex
        for co in courses:
            c = json.loads(courses[co])
            cur = self.conn.cursor()
            cur.execute('INSERT INTO shared_sections (guid, code, meeting_html, hours_text, crn, section) VALUES(%s, %s, %s, %s, %s, %s)',
                        [guid, c['code'], c['meeting_html'], c['hours_text'], c['crn'], c['section']])
            self.conn.commit()
        return guid

    def getShareFromUrl(self, url):
        guid = url[url.find("cal=")+4:]
        cur = self.conn.cursor()
        try:
            cur.execute('SELECT * FROM shared_sections WHERE guid=%s', [guid])
            res = cur.fetchall()
            self.conn.commit()
            ret = {r[4]: json.dumps({'code':r[1], 'meeting_html':r[2], 'hours_text':r[3], 'crn':r[4], 'section':r[5]}) for r in res}
            return ret
        except Exeption as e:
            print(e)
            self.conn.rollback()
            return "Something went wrong"
