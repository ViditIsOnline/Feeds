#oggpnosn 
#hkhr 

import urllib2 as u2
import urllib as ul
from lxml import html
from lxml import etree


regNo = raw_input()

data = { "txtRegno":regNo, "hfIdno":236, "ddlSemester":6, "__EVENTTARGET":"", "__EVENTARGUMENT":"", "__VIEWSTATE":"/wEPDwUJMjIzMTE0MDQxD2QWAgIBD2QWBAILDxBkEBUCBlNlbGVjdAJWSRUCATABNhQrAwJnZxYBZmQCGQ8PFgIeB1Zpc2libGVoZBYEAhMPFCsAAg8WBB4LXyFEYXRhQm91bmRnHgtfIUl0ZW1Db3VudAL/////D2RkZAIXDw8WAh4EVGV4dGVkZBgCBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAwUKYnRuaW1nU2hvdwUQYnRuaW1nU2hvd1Jlc3VsdAUMYnRuaW1nQ2FuY2VsBRBsdlN1YmplY3REZXRhaWxzD2dk", "HiddenField1": "", "btnimgShowResult.x":39, "btnimgShowResult.y":4}

url = "http://www.nitgoa.ac.in/results/"

request = u2.Request(url = url, data = ul.urlencode(data))

resp = u2.urlopen(request)

respText = resp.read()

tree = html.fromstring(respText)

semester = 0
for i in range(len(tree.xpath("id('ddlSemester')")[0].getchildren())):
	if(len(tree.xpath("id('ddlSemester')")[0].getchildren()[i].values())== 2):
		semester = int(tree.xpath("id('ddlSemester')")[0].getchildren()[i].values()[1])



data["ddlSemester"] = semester

url = "http://www.nitgoa.ac.in/results/Default2.aspx"

request = u2.Request(url = url, data = ul.urlencode(data))

resp = u2.urlopen(request)

respText = resp.read()

tree = html.fromstring(respText)

print etree.tostring(tree.xpath("id('PnlShowResult')")[0])






