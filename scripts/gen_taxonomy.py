#!/usr/local/bin/python3.7
# -*- coding: utf-8 -*-
import urllib
import pymysql
import mysql.connector

from urllib.request import urlopen
from dotenv import load_dotenv
load_dotenv()

conn = pymysql.connect(host='134.209.46.210', port=3306, user='chariya', passwd=os.getenv('MYDBPSSWD'),  db=os.getenv('DBNAME'))
cur = conn.cursor()
curinsert = conn.cursor()

# Family
stmt = "insert ignore into common_taxonomy (taxon, `rank`, `level`) SELECT family, 'family', 1 from common_family;"
curinsert.execute(stmt)
conn.commit()

# SubFamily
stmt = "insert ignore into common_taxonomy (taxon, `rank`, `level`, parent_id, parent_name) SELECT a.subfamily, 'subfamily', b.level + 1, b.id, b.taxon from common_subfamily a join common_taxonomy b on a.family = b.taxon;"
curinsert.execute(stmt)
conn.commit()

# Tribe
stmt = "insert ignore into common_taxonomy (taxon, `rank`, `level`, parent_id, parent_name) SELECT a.tribe, 'tribe', b.level + 1, b.id, b.taxon from common_tribe a join common_taxonomy b on a.subfamily = b.taxon;"
curinsert.execute(stmt)
conn.commit()
stmt = "insert ignore into common_taxonomy (taxon, `rank`, `level`, parent_id, parent_name) SELECT a.tribe, 'tribe', b.level + 1, b.id, b.taxon from common_tribe a join common_taxonomy b on a.family = b.taxon and a.subfamily is null or a.subfamily = '';"
curinsert.execute(stmt)
conn.commit()

# Subtribe
stmt = "insert ignore into common_taxonomy (taxon, `rank`, `level`, parent_id, parent_name) SELECT a.subtribe, 'subtribe', b.level + 1, b.id, b.taxon from common_subtribe a join common_taxonomy b on a.tribe = b.taxon;"
curinsert.execute(stmt)
conn.commit()
stmt = "insert ignore into common_taxonomy (taxon, `rank`, `level`, parent_id, parent_name) SELECT a.subtribe, 'subtribe', b.level + 1, b.id, b.taxon from common_subtribe a join common_taxonomy b on a.subfamily = b.taxon and a.tribe is null or a.tribe = '';"
curinsert.execute(stmt)
conn.commit()
stmt = "insert ignore into common_taxonomy (taxon, `rank`, `level`, parent_id, parent_name) SELECT a.subtribe, 'subtribe', b.level + 1, b.id, b.taxon from common_subtribe a join common_taxonomy b on a.family = b.taxon and (a.subfamily is null or a.subfamily = '') and (a.tribe is null or a.tribe = '');"
curinsert.execute(stmt)
conn.commit()
