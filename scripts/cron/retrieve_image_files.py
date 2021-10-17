#!/usr/local/bin/python3.5
# -*- coding: utf-8 -*-
from __future__ import print_function
import urllib
import pymysql
import shortuuid
import re
import sys
from pathlib import Path

# print ('Number of arguments:', len(sys.argv), 'arguments.')

genus = ''
app = sys.argv[1]
tab = app.lower() + "_spcimages"

# import mysqlclient
from urllib.request import urlopen
from PIL import Image
import glob, os, sys


size = 500, 400
HOST = '134.209.46.210'
conn = pymysql.connect(host=HOST, user='chariya', port=3306, passwd='Imh#r3r3', db='bluenanta')
cur = conn.cursor()
if app != 'other':
    family = app.title()
    imgdir = "/mnt/static/utils/images/" + family + "/"
    Path(imgdir).mkdir(parents=True, exist_ok=True)


stmthead = "UPDATE " + tab + " set image_file = '%s' where id = %d"
stmt = "SELECT id, image_url, genus, family  FROM " + tab + " where image_url <>'' and image_url is not null and (image_file is null or image_file = '') order by id"
# print (stmt)

cur.execute(stmt)
i = 0
for row in cur:
    i = i + 1
    url = row[1]
    if app == 'other' and row[3]:
        family = row[3].title()
    urlparts = re.search('\/(.*)(\?)?', url)
    a = urlparts.group(1)
    # ext = a.split('.')[-1]
    ext = 'jpg'
    uid = shortuuid.uuid()
    # print(row[2],uid, ext)
    fname = row[2] + '_' + shortuuid.uuid() + "." + ext
    # fname = "%s_%09d_%09d.jpg" % (type, row[0], row[2])


    if not url or url == '':
        print ("Bad", url)
        cur.nextset()

    try:
        # html = urlopen(url)
        if app == 'other':
            imgdir = "/mnt/static/utils/images/" + family + "/"
            Path(imgdir).mkdir(parents=True, exist_ok=True)
        local_filename, headers = urllib.request.urlretrieve(url, imgdir + fname)
        print(imgdir + fname)
        stmt = stmthead % (fname, row[0])
        # print(stmt)
        curinsert = conn.cursor()

        curinsert.execute(stmt)
        conn.commit()
    except urllib.error.URLError as e:
        print("URLError -- ", row[0], e.reason)
        cur.nextset()
    except urllib.error.HTTPError as e:
        print("HTTPError -- ", row[0], e.reason)
        cur.nextset()
    except urllib.error.FileNotFoundError as e:
        print("HTTPError -- ", row[0], e.reason)
        cur.nextset()
    except:
        cur.nextset()

    # stmt = stmthead % (fname, row[0])
    # # print(stmt)
    # curinsert = conn.cursor()
    #
    # curinsert.execute(stmt)
    # conn.commit()


cur.close()
conn.close()