#oggpnosn 
#hkhr 



import urllib2 as u2
import urllib as ul
from lxml import html
from lxml import etree


regNo = raw_input()

data = { "regNo":regNo}

url = "http://localhost:8080/results"

request = u2.Request(url = url, data = ul.urlencode(data))

resp = u2.urlopen(request)

respText = resp.read()

print respText
