#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import urllib2 as u2
import urllib as ul
from lxml import html
from lxml import etree
import os
import hashlib
import string
import random
import json
import ast
import logging
import webapp2
import jinja2
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
#from oauth2client import client, crypt


API_KEY = "AIzaSyDiTED6ZYPJu2UX_OiCI2XRk5PvXFl2GNc"
GCM_URL = "https://gcm-http.googleapis.com/gcm/send"
WEB_CLIENT_ID = "175731938341-240t3vrm416e74re74t35mfs0c4bo5o7.apps.googleusercontent.com"

letters = string.ascii_letters
letters = [x for x in letters]


# message = """Hello,
# Your voting details are as follows:
# username: %s
# password: %s
# Please login to http://cseaelection.appspot.com to cast your vote.
# Voting Portal will be closed tommorow ie 23/08/2014 at 5 pm.
# Happy Voting
# Connectree Team :-)
# """


def passwordGenerator():
    target = ""
    for i in range(10):
        target += random.choice(letters)
    return target


template_dir = os.path.dirname(__file__)
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)


def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    return h == make_pw_hash(name, pw, salt)


class Pics(ndb.Model):
    caption = ndb.StringProperty(required=True)
    url = ndb.BlobProperty(required=True)
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)


class News(ndb.Model):
    subject = ndb.StringProperty(required=True)
    details = ndb.TextProperty(required=True)
    image = ndb.BlobProperty()
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)


class Community(ndb.Model):
    name = ndb.StringProperty(required=True)
    about = ndb.TextProperty(required=True)
    image = ndb.BlobProperty()
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)

class Attendance(ndb.Model):
    macId = ndb.StringProperty(required=True)
    present = ndb.IntegerProperty(required=True)
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)

class File(ndb.Model):
    name = ndb.StringProperty(required=True)
    url = ndb.BlobProperty(required=True)
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)

class Timetable(ndb.Model):
    branch = ndb.StringProperty(required=True)
    year = ndb.StringProperty(required=True)
    degree = ndb.StringProperty(required=True)
    monday = ndb.PickleProperty(required=True)
    tuesday = ndb.PickleProperty(required=True)
    wednesday = ndb.PickleProperty(required=True)
    thursday = ndb.PickleProperty(required=True)
    friday = ndb.PickleProperty(required=True)
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)

class RegistrationIds(ndb.Model):
    id = ndb.StringProperty()
    name = ndb.StringProperty()
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)

class UserDetails(ndb.Model):
    token = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    group = ndb.StringProperty(required=True)
    branch = ndb.StringProperty(required=True)
    year = ndb.StringProperty(required=True)



class Admin(ndb.Model):
    id = ndb.StringProperty(required=True)


class Wall(ndb.Model):
    text = ndb.TextProperty()
    name = ndb.StringProperty()


class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, filename, parameter={}):
        template = jinja_env.get_template(filename)
        self.response.write(template.render(parameter))


# def sendGcmMessage(message):
#     ids = RegistrationIds.query(RegistrationIds.name == "nitg").fetch()
#     idsSend = ids[0].ids
#     headers= {'Authorization': 'key='+ API_KEY, 'Content-Type': 'application/json'}
#     data = {'data': {
#                       "message": "Testing"},
#             'to': '/topics/global'}

#     url = "https://gcm-http.googleapis.com/gcm/send"
#     request = Request(url, headers = headers, data = json.dumps(data))
#     try:
#         resp = urlopen(request)
#         results = json.loads(resp.read())
#         results = results["results"]
#         ids = ids[0]
#         newIds = ids.ids
#         for i in range(len(ids.ids)):
#             if results[i].get("registration_id", None):
#                 newIds[i] = results[i]["registration_id"]
#         newIds = list(set(newIds))
#         ids.ids = newIds
#         ids.put()
#         return True
#     except HTTPError as e:
#         return False

def sendGcmMessage(message, groups):
    headers = {'Authorization': 'key=' + API_KEY, 'Content-Type': 'application/json'}
    for group in groups:
        data = {'data': message,
                'to': '/topics/' + group}
        request = u2.Request(GCM_URL, headers=headers, data=json.dumps(data))
        try:
            resp = u2.urlopen(request)
            results = json.loads(resp.read())
            return True
        except u2.HTTPError as e:
            return False


class MainHandler(Handler):
    def get(self):
        # self.render("signin.html")
        self.render("index.html")

    def post(self):
        emailid = self.request.get("Email")
        password = self.request.get("password")
        if emailid and password:
            admin = Admin.query(Admin.emailid == emailid, Admin.password == password).fetch(1)
            if admin:
                self.response.headers.add_header("Set-Cookie", str("email=%s" % (emailid)))
                self.response.headers.add_header("Set-Cookie", str("password=%s" % (passwordGenerator())))
                self.response.headers.add_header("Set-Cookie", str("qid=%s" % (hashlib.sha256(password).hexdigest())))
                # self.redirect("/votelist")
            else:
                self.response.write("Sorry You aint Authorized!!")

        else:
            self.response.write("Wrong emailId or password :/")


# class VoteHandler(Handler):
#     def get(self):
#         email = self.request.cookies.get("email", None)
#         password = self.request.cookies.get("qid", None)
#         if email and password:
#             voter = Voter.query(Voter.emailid == email).fetch(1)
#             if voter:
#                 voter = voter[0]
#                 if password == hashlib.sha256(voter.password).hexdigest():
#                     if not voter.completed:
#                         self.render("candidates.html")
#                     else:
#                         self.response.write("We know you are over enthusiastic, but we can't let you vote twice!")
#                 else:
#                     self.response.write("Haaha and you think it will work!!!")
#         else:
#             self.redirect("/")
#
#     def post(self):
#         email = self.request.cookies.get("email", None)
#         password = self.request.cookies.get("qid", None)
#         if email and password:
#             voter = Voter.query(Voter.emailid == email).fetch(1)
#             if voter:
#                 voter = voter[0]
#                 if password == hashlib.sha256(voter.password).hexdigest():
#                     if not voter.completed:
#                         president = self.request.get("president")
#                         vice_president = self.request.get("vice-president")
#                         treasurer = self.request.get("treasurer")
#                         secretary = self.request.get("secretary")
#                         gen_secretary = self.request.get("gen-secretary")
#                         joint_secretary = self.request.get("joint-secretary")
#                         mtech_secretary = self.request.get("secretary-mtech")
#                         if president and vice_president and treasurer and secretary and gen_secretary and
#                           joint_secretary and mtech_secretary:
#                             candidates = [president, vice_president, treasurer, secretary, gen_secretary,
#                                           joint_secretary, mtech_secretary]
#                             for candidate in candidates:
#                                 nominee = Nominee.query(Nominee.name == candidate).fetch(1)
#                                 if nominee:
#                                     nominee = nominee[0]
#                                     nominee.noOfVotes += 1
#                                     voter.completed = True
#                                     # nominee.put()
#                                     # voter.put()
#                                     # self.redirect("/thankYou")
#                                     self.redirect("/result")
#                         else:
#                             self.response.write("Kindly vote for all fields, your vote was rejected!")
#                     else:
#                         self.response.write("We know you are over enthusiastic, but we can't let you vote twice!")
#
#                         self.response.write(
#                             president + "," + vice_president + "," + treasurer + "," + secretary + "," +
#                             gen_secretary + "," + joint_secretary + "," + mtech_secretary)


# class CreateVoter(Handler):
#     def get(self):
#         fob = open("password.csv")
#         for line in fob:
#             target = line.split(",")
#             voter = Voter()
#             voter.emailid = target[0]
#             voter.password = target[1].replace("\n", "").replace(" ", "")
#             voter.completed = False
#             # voter.put()
#
#
# class AddVoter(Handler):
#     def get(self):
#         fob = open("passwordLeftout.csv")
#         for line in fob:
#             target = line.split(",")
#             voter = Voter()
#             voter.emailid = target[0]
#             voter.password = target[1].replace("\n", "").replace(" ", "")
#             voter.completed = False
#             # voter.put()
#             '''mail.send_mail(sender="anuja2910@gmail.com",
#               to=target[0],
#               subject="CSEA Election Details",
#               body=message%(target[0], target[1]))'''


class ConfirmHandler(Handler):
    def post(self):
        email = self.request.get("email")
        logging.debug("Confirm Request from : %s" % str(self.request))
        details = UserDetails.query(UserDetails.email == email).fetch(1)
        if details:
            self.response.write(json.dumps({"confirm": 1,
                                            "branch": details[0].branch,
                                            "year": details[0].year}))
        else:
            self.response.write(json.dumps({"confirm": 0}))


class ThankHandler(Handler):
    def get(self):
        self.render("thank_you.html")


class GCMTestHandler(Handler):
    def get(self):
        message = {"head": "Test",
                   "message": "Testing!!"}
        sendGcmMessage(message, ["global"])


class SignupHandler(Handler):
    def get(self):
        self.render("signup.html")


class HomeHandler(Handler):
    def get(self):
        self.render("dashboard.html")


class RegisterHandler(Handler):
    def post(self):
        token = self.request.get("id")
        name = self.request.get("name")
        email = self.request.get("email")
        group = self.request.get("group")
        branch = self.request.get("branch")
        year = self.request.get("year")

        existing = UserDetails.query(UserDetails.email == email).fetch(1)
        if not existing:
            details = UserDetails()
            details.token = token
            details.name = name
            details.email = email
            details.group = group
            details.branch = branch
            details.year = year
            details.put()


class PostNewsHandler(Handler):
    def get(self):
        self.render("postNews.html")

    def post(self):
        details = self.request.get("details")
        subject = self.request.get("subject")
        news = News()
        news.subject = subject
        news.details = details
        news.put()
        upload_url = blobstore.create_upload_url('/upload', max_bytes_per_blob=2000000)
        self.response.set_cookie("subject", subject)
        self.response.set_cookie("type", "news")
        parameter = {"subject": subject, "details": details, "url": upload_url}
        message = {"head": "News",
                   "message": subject}
        sendGcmMessage(message, ["global"])
        self.render("postNewsImageUpload.html", parameter=parameter)


class NewsSuccessHandler(Handler):
    def get(self):
        self.render("postNewsSuccess.html")


class CommunitySuccessHandler(Handler):
    def get(self):
        self.render("makeCommunitySuccess.html")


class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        uploadType = self.request.cookies.get("type", None)
        upload_files = self.get_uploads('file')
        image = upload_files[0].key()

        if uploadType == "news":
            subject = self.request.cookies.get("subject", None)
            if subject:
                news = News.query(News.subject == subject).fetch(1)
                if news:
                    news = news[0]
                    news.image = str(image)
                    news.put()
                    self.redirect("/news/success")
                else:
                    self.response.write("No database entry could be found for %s" % subject)
            else:
                self.response.write("Switch on cookie and try again!")
        elif uploadType == "community":
            name = self.request.cookies.get("name", None)
            if name:
                community = Community.query(Community.name == name).fetch(1)
                if community:
                    community = community[0]
                    community.image = str(image)
                    community.put()
                    self.redirect("/community/success")
                else:
                    self.response.write("No database entry could be found for %s" % community)
            else:
                self.response.write("Switch on cookie and try again!")
        elif uploadType == "pics":
            pic = Pics()
            caption = self.request.cookies.get("caption")
            pic.caption = caption
            pic.url = str(image)
            pic.put()
            self.response.write("Picture Uploaded Succesfully!")
        elif uploadType == "files":
            file = File()
            name = self.request.cookies.get("name")
            file.name = name
            file.url = str(image)
            file.put()
            self.response.write("File Uploaded Succesfully!")


class WallHandler(Handler):
    def get(self):
        wall = Wall.query(Wall.name == "nitg").fetch(1)
        if wall:
            wall = wall[0]
            self.response.write(wall.text)
        else:
            wall = Wall()
            wall.name = "nitg"
            wall.put()
            self.response.write("")

    def post(self):
        wall = Wall.query(Wall.name == "nitg").fetch(1)
        text = self.request.get("text")
        if wall:
            wall = wall[0]
            wall.text = text
            wall.put()
        else:
            wall = Wall()
            wall.name = "nitg"
            wall.text = text
            wall.put()
            self.response.write("")


class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(ul.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)


class CommunityHandler(Handler):
    def get(self):
        self.render("makeCommunity.html")

    def post(self):
        name = self.request.get("name")
        about = self.request.get("about")
        if name and about:
            community = Community()
            community.name = name
            community.about = about
            community.put()
            upload_url = blobstore.create_upload_url('/upload', max_bytes_per_blob=2000000)
            self.response.set_cookie("name", name)
            self.response.set_cookie("type", "community")
            message = {"head": "Community",
                       "message": name + " added."}
            sendGcmMessage(message, ["global"])
            parameter = {"name": name, "about": about, "url": upload_url}
            self.render("makeCommunityImageUpload.html", parameter=parameter)
        else:
            self.response.write("Name or About cannot be NULL")


class CommunityAppHandler(Handler):
    def get(self):
        communities = Community.query().order(Community.name)
        communityResponse = []
        for community in communities:
            data = {}
            data["url"] = community.image
            data["name"] = community.name
            data["about"] = community.about
            communityResponse.append(data)
        self.response.write(json.dumps(communityResponse))


class NewsAppHandler(Handler):
    def get(self):
        news = News.query().order(-News.timestamp)
        newsResponse = []
        for item in news:
            data = {}
            data["url"] = item.image
            data["subject"] = item.subject
            data["detail"] = item.details
            newsResponse.append(data)
        self.response.write(json.dumps(newsResponse))


class PicsAppHandler(Handler):
    def get(self):
        picsUrl = []
        pics = Pics.query().order(-Pics.timestamp)
        for pic in pics:
            data = {}
            data["url"] = pic.url
            data["caption"] = pic.caption
            picsUrl.append(data)
        self.response.write(json.dumps(picsUrl))


class PicsUploaderHandler(Handler):
    def get(self):
        self.render("picUploader.html")

    def post(self):
        caption = self.request.get("caption")
        if caption:
            self.response.set_cookie("caption", caption)
            self.response.set_cookie("type", "pics")
            upload_url = blobstore.create_upload_url('/upload', max_bytes_per_blob=2000000)
            parameter = {"url": upload_url, "caption": caption}
            message = {"head": "Picture",
                       "message": caption}
            sendGcmMessage(message, ["global"])
            self.render("picImageUploader.html", parameter=parameter)
        else:
            self.response.write("Captions cant be empty!")


class TimetableHandler(Handler):
    def get(self):
        self.render("addTimetable.html")

    def post(self):
        timetable = Timetable()
        branch = self.request.get("branch")
        year = self.request.get("year")
        degree = self.request.get("degree")
        if degree and year and branch:
            timetable.branch = branch
            timetable.year = year
            timetable.degree = degree
            monday = [self.request.get("monday1"), self.request.get("monday2"), self.request.get("monday3"),
                      self.request.get("monday4"), self.request.get("monday5"), self.request.get("monday6"),
                      self.request.get("monday7")]
            tuesday = [self.request.get("tuesday1"), self.request.get("tuesday2"), self.request.get("tuesday3"),
                       self.request.get("tuesday4"), self.request.get("tuesday5"), self.request.get("tuesday6"),
                       self.request.get("tuesday7")]
            wednesday = [self.request.get("wednesday1"), self.request.get("wednesday2"), self.request.get("wednesday3"),
                         self.request.get("wednesday4"), self.request.get("wednesday5"), self.request.get("wednesday6"),
                         self.request.get("wednesday7")]
            thursday = [self.request.get("thursday1"), self.request.get("thursday2"), self.request.get("thursday3"),
                        self.request.get("thursday4"), self.request.get("thursday5"), self.request.get("thursday6"),
                        self.request.get("thursday7")]
            friday = [self.request.get("friday1"), self.request.get("friday2"), self.request.get("friday3"),
                      self.request.get("friday4"), self.request.get("friday5"), self.request.get("friday6"),
                      self.request.get("friday7")]
            timetable.monday = monday
            timetable.tuesday = tuesday
            timetable.wednesday = wednesday
            timetable.thursday = thursday
            timetable.friday = friday
            timetable.put()
            self.render("addTimetableSuccess.html")
        else:
            self.response.write("Branch or Year or Degree is Null")


class CancelClassHandler(Handler):
    def get(self):
        timetables = Timetable.query().fetch(30)
        parameter = {"timetables": timetables}
        self.render("cancelClass.html", parameter=parameter)

    def post(self):
        name = self.request.get("timetableName")
        degree, branch, year = name.split("-")
        if name != "":
            timetable = Timetable.query(Timetable.branch == branch, Timetable.degree == degree,
                                        Timetable.year == year).fetch(1)
            if timetable:
                timetable = timetable[0]
                parameter = {"timetable": timetable}
                self.render("cancelClassTimetable.html", parameter=parameter)
            else:
                self.response.write("Cannot find timetable for the selected name")
        else:
            self.response.write("Invalid name provided")


class CancelConfirmHandler(Handler):
    def post(self):
        reason = self.request.get("message")
        classes = self.request.get_all("classesSelected")
        if reason and classes:
            message = {"head": "Notification",
                       "message": ",".join(classes) + " cancelled.\nReason:" + reason}
            sendGcmMessage(message, ["global"])
            self.render("cancelClassSuccess.html")
        else:
            self.response.write("Failed Kindly enter the message and select classes!")


class TimetableAppHandler(Handler):
    def post(self):
        degree = self.request.get("degree")
        branch = self.request.get("branch")
        year = self.request.get("year")
        if degree and branch and year:
            timetable = Timetable.query(Timetable.branch == branch, Timetable.degree == degree,
                                        Timetable.year == year).fetch(1)
            if timetable:
                timetable = timetable[0]
                response = {"timetable": [{"monday": timetable.monday}, {"tuesday": timetable.tuesday},
                                          {"wednesday": timetable.wednesday}, {"thursday": timetable.thursday},
                                          {"friday": timetable.friday}]}
                self.response.write(json.dumps(response))
            else:
                self.response.write("{'error': 'no database entry could be found'}")
        else:
            self.response.write("{'error': 'Input parameter arent proper'}")


class AttendanceAppHandler(Handler):
    def get(self):
        students = Attendance.query().fetch(1000)  # for testing purpose only! this is shity coding
        for student in students:
            self.response.write(student.macId + ":" + str(student.present))

    def post(self):
        macIds = self.request.get("attendance")
        if macIds:
            macIds = ast.literal_eval(macIds)
            macIds = macIds["present"]
            macIds = list(set(macIds))

            for macId in macIds:
                student = Attendance.query(Attendance.macId == macId).fetch(1)
                if student:
                    student = student[0]
                    student.present += 1
                    student.put()
                else:
                    student = Attendance()
                    student.macId = macId
                    student.present = 1
                    student.put()
            mail.send_mail(sender="tanaygahlot@gmail.com",
                           to="tanay@sterio.me",
                           subject="Attendance",
                           body="Following students attended your classes:\n%s" % ('\n'.join(macIds))
                           )

        else:
            self.response.write("{'error': 'Invalid data'}")


class FileAppHandler(Handler):
    def get(self):
        fileNames = File.query().fetch(30)
        dataResponse = []
        for fileName in fileNames:
            data = {"name": fileName.name, "url": fileName.url}
            dataResponse.append(data)
        self.response.write(json.dumps(dataResponse))


class FileHandler(Handler):
    def get(self):
        self.render("fileUploader.html")

    def post(self):
        name = self.request.get("name")
        if name:
            self.response.set_cookie("name", name)
            self.response.set_cookie("type", "files")
            upload_url = blobstore.create_upload_url('/upload', max_bytes_per_blob=2000000)
            parameter = {"url": upload_url, "name": name}
            message = {"head": "File Shared",
                       "message": name}
            sendGcmMessage(message, ["global"])
            self.render("fileFileUploader.html", parameter=parameter)
        else:
            self.response.write("Name cannot be empty!")


class ResultsHandler(Handler):
    def post(self):
        regNo = self.request.get("regNo")
        data = {"txtRegno": regNo, "hfIdno": 236, "ddlSemester": 6, "__EVENTTARGET": "", "__EVENTARGUMENT": "",
                "__VIEWSTATE": "/wEPDwUJMjIzMTE0MDQxD2QWAgIBD2QWBAILDxBkEBUCBlNlbGVjdAJWSRUCATABNhQrAwJnZxYBZmQCGQ8PFgIeB1Zpc2libGVoZBYEAhMPFCsAAg8WBB4LXyFEYXRhQm91bmRnHgtfIUl0ZW1Db3VudAL/////D2RkZAIXDw8WAh4EVGV4dGVkZBgCBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAwUKYnRuaW1nU2hvdwUQYnRuaW1nU2hvd1Jlc3VsdAUMYnRuaW1nQ2FuY2VsBRBsdlN1YmplY3REZXRhaWxzD2dk",
                "HiddenField1": "", "btnimgShowResult.x": 39, "btnimgShowResult.y": 4}

        url = "http://www.nitgoa.ac.in/results/"

        request = u2.Request(url=url, data=ul.urlencode(data))

        resp = u2.urlopen(request)

        respText = resp.read()

        tree = html.fromstring(respText)

        semester = 0
        for i in range(len(tree.xpath("id('ddlSemester')")[0].getchildren())):
            if len(tree.xpath("id('ddlSemester')")[0].getchildren()[i].values()) == 2:
                semester = int(tree.xpath("id('ddlSemester')")[0].getchildren()[i].values()[1])

        data["ddlSemester"] = semester

        url = "http://www.nitgoa.ac.in/results/Default2.aspx"

        request = u2.Request(url=url, data=ul.urlencode(data))

        resp = u2.urlopen(request)

        respText = resp.read()

        tree = html.fromstring(respText)

        self.response.write(etree.tostring(tree.xpath("id('PnlShowResult')")[0]))


class TokenSignInHandler(Handler):
    # (Receive token by HTTPS POST)
    def post(self):
        token = self.request.get("idtoken")
        try:
            idinfo = client.verify_id_token(token, WEB_CLIENT_ID)  #CLIENT_ID)
            # # If multiple clients access the backend server:
            # if idinfo['aud'] not in [WEB_CLIENT_ID]:  #ANDROID_CLIENT_ID, IOS_CLIENT_ID, WEB_CLIENT_ID]:
            #     raise crypt.AppIdentityError("Unrecognized client.")
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise crypt.AppIdentityError("Wrong issuer.")
            # if idinfo['hd'] != APPS_DOMAIN_NAME:
            #     raise crypt.AppIdentityError("Wrong hosted domain.")
        except crypt.AppIdentityError:
            # Invalid token
            pass
        userid = idinfo['sub']
        admin = Admin.query(Admin.id == userid).fetch(1)
        if admin:
            self.render_str()


app = webapp2.WSGIApplication([
    ('/', MainHandler), ('/gcm', GCMTestHandler), ('/signup', SignupHandler), ('/home', HomeHandler),
    ('/register', RegisterHandler),
    ('/news/add', PostNewsHandler), ('/upload', UploadHandler), ('/wall', WallHandler),
    ('/serve/([^/]+)?', ServeHandler), ('/community/add', CommunityHandler),
    ('/app/community', CommunityAppHandler), ('/app/news', NewsAppHandler), ('/pic', PicsUploaderHandler),
    ('/app/pic', PicsAppHandler), ('/timetable/add', TimetableHandler),
    ('/timetable/cancel', CancelClassHandler), ('/timetable/cancel/confirm', CancelConfirmHandler),
    ('/app/timetable', TimetableAppHandler),
    ('/news/success', NewsSuccessHandler), ('/community/success', CommunitySuccessHandler),
    ('/tokensignin' , TokenSignInHandler),('/app/attendance', AttendanceAppHandler),
    ('/app/files', FileAppHandler), ('/file', FileHandler), ('/confirm', ConfirmHandler), ('/results', ResultsHandler)
], debug=True)
