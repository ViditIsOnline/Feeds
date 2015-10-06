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


API_KEY = "AIzaSyDAgxN-483Qq8eoj-zcfU0pUH5lSpC_kLQ"
GCM_URL = "https://gcm-http.googleapis.com/gcm/send"
WEB_CLIENT_ID = "175731938341-240t3vrm416e74re74t35mfs0c4bo5o7.apps.googleusercontent.com"

letters = string.ascii_letters
letters = [x for x in letters]

#console options for users
CONSOLE_OPTION = {"Admin":[{"Name": "Add Manager", "Link":"/manager/add"},{"Name": "Post News", "Link":"/news/add"}, {"Name": "Edit News", "Link":"/news/edit"}, {"Name": "Delete News", "Link":"/news/delete"}, {"Name": "Add Community", "Link":"/community/add"}, {"Name": "Edit Community", "Link":"/community/edit"}, {"Name": "Delete Community", "Link":"/community/delete"}, {"Name": "Add Timetable", "Link":"/timetable/add"}, {"Name": "Edit Timetable", "Link":"/timetable/edit"}, {"Name": "Schedule Extra Classes", "Link":"/timetable/schedule"}, {"Name": "Cancel Classes", "Link":"/timetable/cancel"}, {"Name": "Add Pics", "Link":"/pics/add"},  {"Name": "Delete Pics", "Link":"/pics/delete"}, {"Name": "Add File", "Link":"/file/add"}, {"Name": "Delete File", "Link":"/file/delete"}], "Journalist":[{"Name": "Post News", "Link":"/news/add"}, {"Name": "Edit News", "Link":"/news/edit"}, {"Name": "Delete News", "Link":"/news/delete"}, {"Name": "Add Timetable", "Link":"/timetable/add"}, {"Name": "Edit Timetable", "Link":"/timetable/edit"}, {"Name": "Add Pics", "Link":"/pics/add"},  {"Name": "Delete Pics", "Link":"/pics/delete"}], "Faculty": [ {"Name": "Schedule Extra Classes", "Link":"/timetable/schedule"}, {"Name": "Cancel Classes", "Link":"/timetable/cancel"}, {"Name": "Add File", "Link":"/file/add"}, {"Name": "Delete File", "Link":"/file/delete"}, {"Name": "Add Community", "Link":"/community/add"}, {"Name": "Edit Community", "Link":"/community/edit"}, {"Name": "Delete Community", "Link":"/community/delete"}], "CommunityLeader": [{"Name": "Add Community", "Link":"/community/add"}, {"Name": "Edit Community", "Link":"/community/edit"}, {"Name": "Delete Community", "Link":"/community/delete"}]}    



MANAGER_MESSAGE = """Ola,\nCongratulation!! you are selected as %s for college feed application. Your login details are as follows:
username: %s
password: %s

You can login at http://nitg-app.appspot.com.

Best Wishes,
Tanay Gahlot
College Feed Team :-)
"""


def passwordGenerator():
    target = ""
    for i in range(10):
        target += random.choice(letters)
    return target


template_dir = os.path.dirname(__file__)
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(15))


def make_pw_hash(name, pw, salt=None):
    if not salt:
        salt = make_salt()
        h = hashlib.sha256(name + pw + salt).hexdigest()
        return (h, salt)
    else:
        h = hashlib.sha256(name + pw + salt).hexdigest()
        return h    


def valid_pw(name, pw, salt,  h):
    return h == make_pw_hash(name, pw, salt)


def scramble(password):
    return password


class Pics(ndb.Model):
    caption = ndb.StringProperty(required=True)
    url = ndb.BlobProperty()
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)
    addedBy = ndb.StringProperty(required=True)


class News(ndb.Model):
    subject = ndb.StringProperty(required=True)
    details = ndb.TextProperty(required=True)
    image = ndb.BlobProperty()
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)
    addedBy = ndb.StringProperty(required=True)


class Community(ndb.Model):
    name = ndb.StringProperty(required=True)
    about = ndb.TextProperty(required=True)
    image = ndb.BlobProperty()
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)
    addedBy = ndb.StringProperty(required=True)


class Attendance(ndb.Model):
    macId = ndb.StringProperty(required=True)
    present = ndb.IntegerProperty(required=True)
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)


class File(ndb.Model):
    name = ndb.StringProperty(required=True)
    url = ndb.BlobProperty()
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)
    addedBy = ndb.StringProperty(required=True)


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
    addedBy = ndb.StringProperty(required=True)


class RegistrationIds(ndb.Model):
    id = ndb.StringProperty()
    name = ndb.StringProperty()
    timestamp = ndb.DateTimeProperty(required = True, auto_now = True)


class UserDetails(ndb.Model):
    id = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    group = ndb.StringProperty(required=True)
    branch = ndb.StringProperty(required=True)
    year = ndb.StringProperty(required=True)
    url = ndb.StringProperty(required=True)


class Manager(ndb.Model):
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty(required=True)
    managerType = ndb.StringProperty(required=True)
    password = ndb.StringProperty(required=True)
    salt = ndb.StringProperty(required=True)


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

    def authenticateUser(self):
        email = self.request.cookies.get("email", None)
        hashVal = self.request.cookies.get("qid", None)
        manager = Manager.query(Manager.email == email).fetch(1)
        if manager:
            manager = manager[0]
            password = manager.password
            salt = manager.salt
            if valid_pw(email, password, salt, hashVal):
                return manager 
            else:
                return None

    def getParameter(self):
        manager = self.authenticateUser()
        if manager:
            options = CONSOLE_OPTION[manager.managerType]
            parameter = {"options": options}
            return parameter
        else:
            self.response.write("not authenticated!")
            return None 


def sendGcmMessage(message, groups):
    #pass
    headers = {'Authorization': 'key=' + API_KEY, 'Content-Type': 'application/json'}
    for group in groups:
        data = {'data': message,
                'to': '/topics/' + group}
        request = u2.Request(GCM_URL, headers=headers, data=json.dumps(data))
        try:
            resp = u2.urlopen(request,timeout=30)
            results = json.loads(resp.read())
            return True
        except u2.HTTPError as e:
            return False


class MainHandler(Handler):
    def get(self):
        manager = self.authenticateUser()
        if manager:
            self.redirect("/home")
        else:    
            self.render("index.html")

    def post(self):
        email = self.request.get("email")
        password = self.request.get("password")
        if email and password:
            password = scramble(password)
            manager = Manager.query(Manager.email == email, Manager.password == password).fetch(1)
            if manager:
                manager = manager[0]
                salt = manager.salt
                self.response.headers.add_header("Set-Cookie", str("email=%s" % (email)))
                self.response.headers.add_header("Set-Cookie", str("password=%s" % (passwordGenerator())))
                self.response.headers.add_header("Set-Cookie", str("qid=%s" % (make_pw_hash(email, password, salt))))
                self.redirect("/home")
            else:
                self.response.write("Sorry You aint Authorized!!")

        else:
            self.response.write("Wrong emailId or password :/")


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


class HomeHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter: 
            self.render("dashboard.html", parameter = parameter)


class RegisterHandler(Handler):
    def post(self):
        id = self.request.get("id")
        name = self.request.get("name")
        email = self.request.get("email")
        group = self.request.get("group")
        branch = self.request.get("branch")
        year = self.request.get("year")

        existing = UserDetails.query(UserDetails.email == email).fetch(1)
        if not existing:
            details = UserDetails()
            details.id = id
            details.name = name
            details.email = email
            details.group = group
            details.branch = branch
            details.year = year
            details.put()


class PostNewsHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            self.render("postNews.html", parameter = parameter)

    def post(self):
        parameter = self.getParameter()
        if parameter:
            details = self.request.get("details")
            subject = self.request.get("subject")
            news = News()
            news.subject = subject
            news.details = details
            
            manager = self.authenticateUser()
            news.addedBy = manager.email

            news.put()
            upload_url = blobstore.create_upload_url('/upload', max_bytes_per_blob=2000000)
            self.response.set_cookie("subject", subject)
            self.response.set_cookie("type", "news")
            parameter["subject"] = subject 
            parameter["details"] = details 
            parameter["url"] = upload_url
            message = {"head": "News",
                       "message": subject}
            sendGcmMessage(message, ["global"])

            self.render("postNewsImageUpload.html", parameter=parameter)


class NewsSuccessHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            self.render("postNewsSuccess.html", parameter = parameter)


class CommunitySuccessHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            self.render("makeCommunitySuccess.html", parameter = parameter)


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
            caption = self.request.cookies.get("caption")
            pic = Pics.query(Pics.caption == caption).fetch(1)
            if pic:
                pic = pic[0]
                pic.url = str(image)
                pic.put()
                self.redirect("/pics/success")
            else:
                self.response.write("No Database entry exist for the given caption!")    
        elif uploadType == "files":
            name = self.request.cookies.get("name")
            file = File.query(File.name == name ).fetch(1)
            if file:
                file = file[0]
                file.url = str(image)
                file.put()
                self.redirect("/file/success")
            else:
                self.response.write("No Database entry exist for the given caption!")        


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
        parameter = self.getParameter()
        if parameter:
            self.render("makeCommunity.html", parameter= parameter)

    def post(self):
        parameter = self.getParameter()
        if parameter:
            name = self.request.get("name")
            about = self.request.get("about")
            if name and about:
                community = Community()
                community.name = name
                community.about = about
                
                manager = self.authenticateUser()
                community.addedBy = manager.email
                
                community.put()
                upload_url = blobstore.create_upload_url('/upload', max_bytes_per_blob=2000000)
                self.response.set_cookie("name", name)
                self.response.set_cookie("type", "community")
                message = {"head": "Community",
                           "message": name + " added."}
                sendGcmMessage(message, ["global"])
                parameter["name"] = name 
                parameter["about"] = about
                parameter["url"] = upload_url
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

#needs work on html

class PicsUploaderHandler(Handler):
    def get(self):
        self.render("picUploader.html")

    def post(self):
        caption = self.request.get("caption")
        if caption:
            self.response.set_cookie("caption", caption)
            self.response.set_cookie("type", "pics")
            pic = Pics()
            pic.caption = caption 

            manager = self.authenticateUser()
            pic.addedBy = manager.email

            pic.put()
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
        parameter = self.getParameter()
        if parameter:
            self.render("addTimetable.html", parameter = parameter)

    def post(self):
        parameter = self.getParameter()
        if parameter:
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

                manager = self.authenticateUser()
                timetable.addedBy = manager.email

                timetable.put()
                self.render("addTimetableSuccess.html", parameter = parameter)
            else:
                self.response.write("Branch or Year or Degree is Null")





class CancelClassHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            timetables = Timetable.query().fetch(30)
            parameter["timetables"] = timetables
            self.render("cancelClass.html", parameter=parameter)

    def post(self):
        parameter = self.getParameter()
        if parameter:
            name = self.request.get("timetableName")
            degree, branch, year = name.split("-")
            if name != "":
                timetable = Timetable.query(Timetable.branch == branch, Timetable.degree == degree,
                                            Timetable.year == year).fetch(1)
                if timetable:
                    timetable = timetable[0]
                    parameter["timetable"] = timetable

                    self.render("cancelClassTimetable.html", parameter=parameter)
                else:
                    self.response.write("Cannot find timetable for the selected name")
            else:
                self.response.write("Invalid name provided")

class TimetableEditSubmitHandler(Handler):
    def post(self):
        parameter = self.getParameter()
        if parameter:
            branch = self.request.cookies.get("branch")
            year = self.request.cookies.get("year")
            degree = self.request.cookies.get("degree")
            timetable = Timetable.query(Timetable.branch == branch, Timetable.degree == degree,
                                            Timetable.year == year).fetch(1)
            if timetable:
                timetable = timetable[0]
                classes = timetable.monday
                for i in xrange(7):
                    lecture = self.request.get("monday"+str(i+1))
                    if lecture:
                        classes[i] = lecture
                timetable.monday = classes        

                classes = timetable.tuesday
                for i in xrange(7):
                    lecture = self.request.get("tuesday"+str(i+1))
                    if lecture:
                        classes[i] = lecture
                timetable.tuesday = classes   

                classes = timetable.wednesday
                for i in xrange(7):
                    lecture = self.request.get("wednesday"+str(i+1))
                    if lecture:
                        classes[i] = lecture
                timetable.wednesday = classes 

                classes = timetable.thursday
                for i in xrange(7):
                    lecture = self.request.get("thursday"+str(i+1))
                    if lecture:
                        classes[i] = lecture
                timetable.thursday = classes

                classes = timetable.friday
                for i in xrange(7):
                    lecture = self.request.get("friday"+str(i+1))
                    if lecture:
                        classes[i] = lecture
                timetable.friday = classes

                timetable.put()  

                self.render("editTimetableSuccess.html", parameter = parameter)                              
        else:
            self.response.write("You aint authorized")            


class EditTimetableHomeHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            timetables = Timetable.query().fetch(30)
            parameter["timetables"] = timetables
            self.render("editTimetableHome.html", parameter=parameter)
    def post(self):
        parameter = self.getParameter()
        if parameter:
            name = self.request.get("timetableName")
            degree, branch, year = name.split("-")
            if name != "":
                timetable = Timetable.query(Timetable.branch == branch, Timetable.degree == degree,
                                            Timetable.year == year).fetch(1)
                if timetable:
                    timetable = timetable[0]
                    self.response.set_cookie("branch", branch)
                    self.response.set_cookie("year", year)
                    self.response.set_cookie("degree", degree)
                    parameter["timetable"] = timetable
                    self.render("editTimetableEditor.html", parameter=parameter)
                else:
                    self.response.write("Cannot find timetable for the selected name")
            else:
                self.response.write("Invalid name provided")

class CancelConfirmHandler(Handler):
    def post(self):
        parameter = self.getParameter()
        if parameter:
            reason = self.request.get("message")
            classes = self.request.get_all("classesSelected")
            if reason and classes:
                message = {"head": "Notification",
                           "message": ",".join(classes) + " cancelled.\nReason:" + reason}
                sendGcmMessage(message, ["global"])
                self.render("cancelClassSuccess.html", parameter = parameter)
            else:
                self.response.write("Failed Kindly enter the message and select classes!")

class ScheduleConfirmHandler(Handler):
    def post(self):
        parameter = self.getParameter()
        if parameter:
            reason = self.request.get("message")
            classes = self.request.get_all("classesSelected")
            if reason and classes:
                message = {"head": "Notification",
                           "message": ",".join(classes) + " scheduled.\nReason:" + reason}
                sendGcmMessage(message, ["global"])
                self.render("classScheduledSuccess.html", parameter = parameter)
            else:
                self.response.write("Failed Kindly enter the message and select classes!")


class ScheduleClassHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            timetables = Timetable.query().fetch(30)
            parameter["timetables"] = timetables
            self.render("scheduleClass.html", parameter=parameter)

    def post(self):
        parameter = self.getParameter()
        if parameter:
            name = self.request.get("timetableName")
            degree, branch, year = name.split("-")
            if name != "":
                timetable = Timetable.query(Timetable.branch == branch, Timetable.degree == degree,
                                            Timetable.year == year).fetch(1)
                if timetable:
                    timetable = timetable[0]
                    parameter["timetable"] = timetable

                    self.render("scheduleClassTimetable.html", parameter=parameter)
                else:
                    self.response.write("Cannot find timetable for the selected name")
            else:
                self.response.write("Invalid name provided")


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

#needs work here, gotta integrate it 
class FileHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            self.render("fileUploader.html")

    def post(self):
        parameter = self.getParameter()
        if parameter:
            name = self.request.get("name")
            if name:
                self.response.set_cookie("name", name)
                self.response.set_cookie("type", "files")
                file = File()
                file.name = name 

                manager = self.authenticateUser()
                file.addedBy = manager.email

                file.put()
                upload_url = blobstore.create_upload_url('/upload', max_bytes_per_blob=2000000)
                parameter = {"url": upload_url, "name": name}
                message = {"head": "File Shared",
                           "message": name}
                #sendGcmMessage(message, ["global"])
                self.render("fileFileUploader.html", parameter=parameter)
            else:
                self.response.write("Name cannot be empty!")


class ResultsHandler(Handler):
    def post(self):
        regNo = self.request.get("regNo")
        
        dataFormat = [{"__EVENTTARGET":"", "__EVENTARGUMENT":"", "__VIEWSTATE":"/wEPDwUJMjIzMTE0MDQxD2QWAgIBD2QWBAILDxBkEBUCBlNlbGVjdAJJSRUCATABMhQrAwJnZxYBZmQCGQ8PFgIeB1Zpc2libGVoZBYiAgEPDxYCHgRUZXh0BRAyMDE0LTIwMTUgSUkgUkVHZGQCAw8PFgIfAQUHQi5UZWNoLmRkAgUPDxYCHwEFCkFNSVQgS1VNQVJkZAIHDw8WAh8BBQkxNENTRTEwMDFkZAIJDw8WAh8BBQJJSWRkAgsPDxYCHwEFAUlkZAINDw8WAh8BBQdCLlRlY2guZGQCDw8PFgIfAQUgQ29tcHV0ZXIgU2NpZW5jZSBhbmQgRW5naW5lZXJpbmdkZAITDxQrAAIPFgQeC18hRGF0YUJvdW5kZx4LXyFJdGVtQ291bnQCCWRkZAIVDw8WAh8BBQIyMmRkAhcPDxYCHwFlZGQCGQ8PFgIfAQUCMjFkZAIbDw8WAh8BBQMxNjRkZAIdDw8WAh8BBQQ3LjgxZGQCHw8PFgIfAQUCNDNkZAIhDw8WAh8BBQMzMzFkZAIjDw8WAh8BBQQ3LjcwZGQYAgUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgMFCmJ0bmltZ1Nob3cFEGJ0bmltZ1Nob3dSZXN1bHQFDGJ0bmltZ0NhbmNlbAUQbHZTdWJqZWN0RGV0YWlscw88KwAKAQgCCWQ=", "txtRegno":"14CSE1001", "hfIdno":"448", "ddlSemester": "2", "HiddenField1":"", "btnimgShowResult.x":24, "btnimgShowResult.y":10}, {"__EVENTTARGET":"", "__EVENTARGUMENT":"", "__VIEWSTATE":"/wEPDwUJMjIzMTE0MDQxD2QWAgIBD2QWBAILDxBkEBUCBlNlbGVjdAJJVhUCATABNBQrAwJnZxYBZmQCGQ8PFgIeB1Zpc2libGVoZBYiAgEPDxYCHgRUZXh0BRAyMDE0LTIwMTUgSUkgUkVHZGQCAw8PFgIfAQUHQi5UZWNoLmRkAgUPDxYCHwEFCkFNSVQgS1VNQVJkZAIHDw8WAh8BBQkxNENTRTEwMDFkZAIJDw8WAh8BBQJJSWRkAgsPDxYCHwEFAUlkZAINDw8WAh8BBQdCLlRlY2guZGQCDw8PFgIfAQUgQ29tcHV0ZXIgU2NpZW5jZSBhbmQgRW5naW5lZXJpbmdkZAITDxQrAAIPFgQeC18hRGF0YUJvdW5kZx4LXyFJdGVtQ291bnQCCWRkZAIVDw8WAh8BBQIyMmRkAhcPDxYCHwFlZGQCGQ8PFgIfAQUCMjFkZAIbDw8WAh8BBQMxNjRkZAIdDw8WAh8BBQQ3LjgxZGQCHw8PFgIfAQUCNDNkZAIhDw8WAh8BBQMzMzFkZAIjDw8WAh8BBQQ3LjcwZGQYAgUeX19Db250cm9sc1JlcXVpcmVQb3N0QmFja0tleV9fFgMFCmJ0bmltZ1Nob3cFEGJ0bmltZ1Nob3dSZXN1bHQFDGJ0bmltZ0NhbmNlbAUQbHZTdWJqZWN0RGV0YWlscw88KwAKAQgCCWQ=", "txtRegno":"13CSE019", "hfIdno":"314", "ddlSemester": "4", "HiddenField1":"", "btnimgShowResult.x":45, "btnimgShowResult.y":9}, {"__EVENTTARGET":"", "__EVENTARGUMENT":"", "__VIEWSTATE":"/wEPDwUJMjIzMTE0MDQxD2QWAgIBD2QWBAILDxBkEBUCBlNlbGVjdAJWSRUCATABNhQrAwJnZxYBZmQCGQ8PFgIeB1Zpc2libGVoZBYiAgEPDxYCHgRUZXh0BRAyMDE0LTIwMTUgSUkgUkVHZGQCAw8PFgIfAQUHQi5UZWNoLmRkAgUPDxYCHwEFDlAgUkVTSE1BIFNBR0FSZGQCBw8PFgIfAQUIMTNDU0UwMTlkZAIJDw8WAh8BBQJJVmRkAgsPDxYCHwEFAklJZGQCDQ8PFgIfAQUHQi5UZWNoLmRkAg8PDxYCHwEFIENvbXB1dGVyIFNjaWVuY2UgYW5kIEVuZ2luZWVyaW5nZGQCEw8UKwACDxYEHgtfIURhdGFCb3VuZGceC18hSXRlbUNvdW50AghkZGQCFQ8PFgIfAQUCMjFkZAIXDw8WAh8BZWRkAhkPDxYCHwEFAjIwZGQCGw8PFgIfAQUDMTc2ZGQCHQ8PFgIfAQUEOC44MGRkAh8PDxYCHwEFAjg0ZGQCIQ8PFgIfAQUDNzg3ZGQCIw8PFgIfAQUEOS4zN2RkGAIFHl9fQ29udHJvbHNSZXF1aXJlUG9zdEJhY2tLZXlfXxYDBQpidG5pbWdTaG93BRBidG5pbWdTaG93UmVzdWx0BQxidG5pbWdDYW5jZWwFEGx2U3ViamVjdERldGFpbHMPPCsACgEIAghk", "txtRegno":"12CSE019", "hfIdno":"236", "ddlSemester": "6", "HiddenField1":"", "btnimgShowResult.x":33, "btnimgShowResult.y":14}]
        dataFormat = dataFormat[::-1]
        year = int(regNo[:2])
        index = year%4
        semester = ((index +3)%4)*2#remeber to add one and subtract one to get right results 

        data = dataFormat[index]
        data["txtRegno"] = regNo


        url = "http://www.nitgoa.ac.in/results/Default2.aspx"

        request = u2.Request(url=url, data=ul.urlencode(data))

        resp = u2.urlopen(request)

        respText = resp.read()


        tree = html.fromstring(respText)
        self.response.write(etree.tostring(tree.xpath("id('PnlShowResult')")[0]))

# class TokenSignInHandler(Handler):
#     # (Receive token by HTTPS POST)
#     def post(self):
#         token = self.request.get("idtoken")
#         try:
#             idinfo = client.verify_id_token(token, WEB_CLIENT_ID)  #CLIENT_ID)
#             # # If multiple clients access the backend server:
#             # if idinfo['aud'] not in [WEB_CLIENT_ID]:  #ANDROID_CLIENT_ID, IOS_CLIENT_ID, WEB_CLIENT_ID]:
#             #     raise crypt.AppIdentityError("Unrecognized client.")
#             if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
#                 raise crypt.AppIdentityError("Wrong issuer.")
#             # if idinfo['hd'] != APPS_DOMAIN_NAME:
#             #     raise crypt.AppIdentityError("Wrong hosted domain.")
#         except crypt.AppIdentityError:
#             # Invalid token
#             pass
#         userid = idinfo['sub']
#         admin = Admin.query(Admin.id == userid).fetch(1)
#         if admin:
#             self.render_str()

class AddManagerHandler(Handler):
    def get(self):  
        parameter = self.getParameter()
        if parameter:
            self.render("addManager.html", parameter = parameter)
    def post(self):
        parameter = self.getParameter()
        if parameter:            
            email = self.request.get("email")
            name = self.request.get("name")
            managerType = self.request.get("managerType")
            password = passwordGenerator()
            salt = make_salt()
            
            if email and name and managerType and password:
                manager = Manager()
                manager.email = email
                manager.password = scramble(password)
                manager.name = name 
                manager.managerType = managerType
                manager.salt = salt
                manager.put()

                mail.send_mail(sender="tanaygahlot@gmail.com",
                  to=email,
                  subject="College Feed Login Details",
                  body=MANAGER_MESSAGE%(managerType, email, password))
                self.render("addManagerSuccess.html", parameter = parameter)
            else:
                self.response.write("You cant leave any field empty, try again!")    


class ChatHandler(Handler):
    def get(self):
        users = UserDetails.query().fetch()
        if users:
            pupil = []
            for user in users:
                pupil.append({"id": user.id, "name": user.name, "url": user.url, "email": user.email, })
            self.response.write(json.dumps(pupil))

    def post(self):
        id = self.request.get("id")
        users = UserDetails.query(UserDetails.id is not id).fetch()
        if users:
            pupil = []
            for user in users:
                pupil.append({"id": user.id, "name": user.name, "url": user.email, "email": user.email})
            self.response.write(json.dumps(pupil))    

class PicsSuccessHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            self.render("picUploaderSuccess.html", parameter = parameter)

class FileSuccessHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            self.render("fileUploaderSuccess.html", parameter = parameter)

class LogoutHandler(Handler):
    def get(self):
        self.response.headers.add_header("Set-Cookie", str("email=%s" % ("")))
        self.response.headers.add_header("Set-Cookie", str("password=%s" % (passwordGenerator())))
        self.response.headers.add_header("Set-Cookie", str("qid=%s" % ("")))
        self.redirect("/")

class EditNewsHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            manager = self.authenticateUser()
            email = manager.email
            news = News.query(News.addedBy == email).order(-News.timestamp).fetch(20)
            parameter["news"] = news
            self.render("editNewsHome.html", parameter = parameter)

class EditCommunityHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            manager = self.authenticateUser()
            email = manager.email
            community = Community.query(Community.addedBy == email).order(-Community.timestamp).fetch(20)
            parameter["communities"] = community
            self.render("editCommunityHome.html", parameter = parameter)


class EditNewsEditorHandler(Handler):
    def get(self, key):
        parameter = self.getParameter()
        if parameter:
            if key:
                key = ndb.Key(urlsafe=key)
                news = key.get()
                parameter["news"] = news
                self.render("editNewsEditor.html", parameter = parameter)
            else:
                self.response.write("Invalid key")    
        else:
            self.response.write("Not authenticated")                 
    def post(self, key):
        parameter = self.getParameter()
        if parameter:
            if key:
                key = ndb.Key(urlsafe=key)
                news = key.get()
                details = self.request.get("details")
                subject = self.request.get("subject")
                if subject:
                    news.subject = subject
                else:    
                    news.subject = news.subject
                    subject = news.subject

                news.details = details
                
                news.put()
                upload_url = blobstore.create_upload_url('/upload', max_bytes_per_blob=2000000)
                self.response.set_cookie("subject", subject)
                self.response.set_cookie("type", "news")
                parameter["subject"] = subject 
                parameter["details"] = details 
                parameter["url"] = upload_url

                self.render("postNewsImageUpload.html", parameter=parameter)

class EditCommunityEditorHandler(Handler):
    def get(self, key):
        parameter = self.getParameter()
        if parameter:
            if key:
                key = ndb.Key(urlsafe=key)
                community = key.get()
                parameter["community"] = community
                self.render("editCommunityEditor.html", parameter = parameter)
            else:
                self.response.write("Invalid key")    
        else:
            self.response.write("Not authenticated")                 
    def post(self, key):
        parameter = self.getParameter()
        if parameter and key:
            name = self.request.get("name")
            about = self.request.get("about")
            
            key = ndb.Key(urlsafe = key)
            community = key.get()
            if name:
                community.name = name
            else:
                community.name = community.name  
                name = community.name 

            community.about = about
            
            manager = self.authenticateUser()
            community.addedBy = manager.email
            
            community.put()
            upload_url = blobstore.create_upload_url('/upload', max_bytes_per_blob=2000000)
            self.response.set_cookie("name", name)
            self.response.set_cookie("type", "community")
            parameter["name"] = name 
            parameter["about"] = about
            parameter["url"] = upload_url
            self.render("makeCommunityImageUpload.html", parameter=parameter)
        

class DeleteNewsHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            manager = self.authenticateUser()
            email = manager.email
            news = News.query(News.addedBy == email).order(-News.timestamp).fetch(20)
            parameter["news"] = news
            self.render("deleteNewsHome.html", parameter = parameter)

class DeleteCommunityHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            manager = self.authenticateUser()
            email = manager.email
            communities = Community.query(Community.addedBy == email).order(-Community.timestamp).fetch(20)
            parameter["communities"] = communities
            self.render("deleteCommunityHome.html", parameter = parameter)


class DeleteNewsActualHandler(Handler):
    def get(self, key):
        manager = self.authenticateUser()
        key = ndb.Key(urlsafe=key)
        news = key.get()
        if key and news.addedBy == manager.email:
            parameter = self.getParameter()        
            key.delete()
            self.render("deleteNewsSuccess.html", parameter = parameter)
        else:
            self.response.write("You aint authorized to perform this operation")    

class DeleteCommunityActualHandler(Handler):
    def get(self, key):
        manager = self.authenticateUser()
        key = ndb.Key(urlsafe=key)
        community = key.get()
        if key and community.addedBy == manager.email:
            parameter = self.getParameter()        
            key.delete()
            self.render("deleteCommunitySuccess.html", parameter = parameter)
        else:
            self.response.write("You aint authorized to perform this operation")    

class PicsDeleteHomeHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            manager = self.authenticateUser()
            email = manager.email
            pics = Pics.query(Pics.addedBy == email).order(-Pics.timestamp).fetch(20)
            parameter["pics"] = pics
            self.render("deletePicHome.html", parameter = parameter)

class DeletePicsActualHandler(Handler):
    def get(self, key):
        parameter = self.getParameter()
        if parameter and key:
            key = ndb.Key(urlsafe = key)
            key.delete()
            self.render("DeletePicSuccess.html", parameter = parameter)
        else:
            self.response.write("You Aint authorized!")    

class FileDeleteHomeHandler(Handler):
    def get(self):
        parameter = self.getParameter()
        if parameter:
            manager = self.authenticateUser()
            email = manager.email
            files = File.query(File.addedBy == email).order(-File.timestamp).fetch(20)
            parameter["files"] = files
            self.render("fileDeleteHome.html", parameter = parameter)

class DeleteFileActualHandler(Handler):
    def get(self, key):
        parameter = self.getParameter()
        if parameter and key:
            key = ndb.Key(urlsafe = key)
            key.delete()
            self.render("DeleteFileSuccess.html", parameter = parameter)
        else:
            self.response.write("You Aint authorized!")    



app = webapp2.WSGIApplication([
    ('/', MainHandler), ('/gcm', GCMTestHandler), ('/home', HomeHandler),
    ('/register', RegisterHandler),
    ('/news/add', PostNewsHandler), ('/upload', UploadHandler), ('/wall', WallHandler),
    ('/serve/([^/]+)?', ServeHandler), ('/community/add', CommunityHandler),
    ('/app/community', CommunityAppHandler), ('/app/news', NewsAppHandler), ('/pics/add', PicsUploaderHandler),
    ('/app/pic', PicsAppHandler), ('/timetable/add', TimetableHandler),
    ('/timetable/cancel', CancelClassHandler), ('/timetable/cancel/confirm', CancelConfirmHandler),
    ('/app/timetable', TimetableAppHandler),
    ('/news/success', NewsSuccessHandler), ('/community/success', CommunitySuccessHandler),
    ('/app/attendance', AttendanceAppHandler),
    ('/app/files', FileAppHandler), ('/file/add', FileHandler), ('/confirm', ConfirmHandler), ('/results', ResultsHandler),
    ('/manager/add', AddManagerHandler), ("/app/chat", ChatHandler), ('/pics/success', PicsSuccessHandler), ('/file/success', FileSuccessHandler)
    ,('/logout', LogoutHandler), ('/news/edit', EditNewsHandler), ('/news/edit/([^/]+)?', EditNewsEditorHandler),
    ('/news/delete', DeleteNewsHandler), ('/news/delete/([^/]+)?', DeleteNewsActualHandler), 
    ('/community/edit', EditCommunityHandler), ('/community/edit/([^/]+)?', EditCommunityEditorHandler)
    ,('/community/delete', DeleteCommunityHandler), ('/community/delete/([^/]+)?', DeleteCommunityActualHandler), 
    ('/timetable/edit', EditTimetableHomeHandler), ('/timetable/edit/submit', TimetableEditSubmitHandler), ('/timetable/schedule', ScheduleClassHandler),
    ('/timetable/schedule/confirm', ScheduleConfirmHandler), ('/pics/delete', PicsDeleteHomeHandler), ('/pics/delete/([^/]+)?', DeletePicsActualHandler),
    ('/file/delete', FileDeleteHomeHandler), ('/file/delete/([^/]+)?', DeleteFileActualHandler)
], debug=True)
