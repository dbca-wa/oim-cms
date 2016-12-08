#!/usr/bin/env python
import confy
import os
import sys
import json
import string
import psycopg2

from confy import env, database, cache
from subprocess import call
from django.utils.encoding import smart_str
from types import NoneType

confy.read_environment_file()

locmap = {} 
suppliermap = {}
dupecache = {}

# New Database Connection
newdbconn = psycopg2.connect(database=env("NEW_DB"), user=env("NEW_DB_USER"), password=env("NEW_DB_PASS"), host=env("NEW_DB_HOST"), port="5432")
# OLD database Connection 
olddbconn = psycopg2.connect(database=env("OLD_DB"), user=env("OLD_DB_USER"), password=env("OLD_DB_PASS"), host=env("OLD_DB_HOST"), port="5432")

newcur = newdbconn.cursor()
oldcur = olddbconn.cursor()

# Assets_Supplier
tablemap = {}
rowjson = {}
tablemap['id'] = 0
tablemap['revision_id'] = 1
tablemap['object_id'] = 2
tablemap['content_type_id'] = 3
tablemap['format'] = 4
tablemap['serialized_data'] = 5
tablemap['object_repr'] = 6
tablemap['type'] = 7
tablemap['db'] = 8

boolmap = {}
boolmap['t'] = 'True';
boolmap['f'] = 'False';

query="select id,revision_id,object_id,content_type_id,format,serialized_data,object_repr,type,db from reversion_version where content_type_id = 40 "
oldcur.execute(query)
rows=oldcur.fetchall()
for row in rows:

    q="select id,date_created,user_id,comment from reversion_revision where id = '"+str(row[tablemap['revision_id']])+"' "
#    print q
    oldcur.execute(q)
    result=oldcur.fetchone()

    # get user_id in new table
    q="select id,username,first_name,last_name,email,password,is_staff,is_active,is_superuser,last_login,date_joined from auth_user where id = '"+str(result[2])+"' "
#    print q
    oldcur.execute(q)
    oldauthuser=oldcur.fetchone()

    q="select id from auth_user where username = '"+str(oldauthuser[1])+"' "
 #   print q
    newcur.execute(q)
    newauthuser=newcur.fetchone()
#   print newauthuser[0]
#    print str(oldauthuser[7])
#   print boolmap[str(oldauthuser[7])];
    
    if newauthuser: 
        print "User exists"
    else:
        sqlcommanduser = "insert into auth_user (username,first_name,last_name,email,password,is_staff,is_active,is_superuser,last_login,date_joined) values ('"+oldauthuser[1]+"','"+string.replace(str(oldauthuser[2]),"'","''")+"','"+string.replace(str(oldauthuser[3]),"'","''")+"','"+oldauthuser[4]+"','"+oldauthuser[5]+"',"+str(oldauthuser[6])+","+str(oldauthuser[7])+","+str(oldauthuser[8])+",'"+str(oldauthuser[9])+"','"+str(oldauthuser[10])+"')"
        print sqlcommanduser
        try:
            newcur.execute(sqlcommanduser);
        except Exception, e:
            print "ERROR: ",e[0]

        newdbconn.commit()
        q="select id from auth_user where username = '"+str(oldauthuser[1])+"' "
        print q
        newcur.execute(q)
        newauthuser=newcur.fetchone()
        print newauthuser[0]


    sqlcommand1 = "insert into reversion_revision (manager_slug, date_created, comment, user_id) values ('default','"+str(result[1])+"','"+string.replace(str(result[3]),"'","''")+"','"+str(newauthuser[0])+"')"
#    print sqlcommand1

    try:
        newcur.execute(sqlcommand1)
    except Exception, e:
        print sqlcommand1
        print "ERROR: ",e[0]

    newdbconn.commit()
        
    q="select id from reversion_revision order by id desc limit 1"
    newcur.execute(q)
    lastrev=newcur.fetchone()
        

#    print "ID:"
 #   print lastrev[0]
#   print result[0]
    print "----";
    rowjson = { "id": row[tablemap['id']],
                "revision_id": row[tablemap['revision_id']],
                "object_id": row[tablemap['object_id']],
                "content_type_id": str(row[tablemap['content_type_id']]),
                "format": str(row[tablemap['format']]),
                "serialized_data": row[tablemap['serialized_data']],
                "object_repr": row[tablemap['object_repr']],
                "type": row[tablemap['type']],
                "db": row[tablemap['db']],
    }

    print "RevID:"+str(lastrev[0])
#    print row[tablemap['revision_id']]
    #    print row[tablemap['serialized_data']]

    content_type_id = '123'

    #rowjsonstring = json.dumps(rowjson);
    sqlcommand = "insert into reversion_version (object_id, object_id_int, format, serialized_data, object_repr, content_type_id, revision_id ) values ( '"+str(row[tablemap['object_id']])+"','"+str(row[tablemap['object_id']])+"','"+str(row[tablemap['format']])+"','"+string.replace(str(row[tablemap['serialized_data']]),"'","''")+"','"+str(row[tablemap['object_repr']])+"','"+content_type_id+"','"+str(lastrev[0])+"'  )"

    #sqlcommand1 = "insert into reversion_revision (manager_slug, date_created, comment, user_id) values ('')"
#    sqlcommand = "insert into reversion_version (id,name,details,extra_data,account_rep,contact_email,contact_phone,website) values ("+str(row[tablemap['id']])+",'"+row[tablemap['name']]+"','"+row[tablemap['notes']]+"','"+rowjsonstring+"','"+row[tablemap['account_rep']]+"','"+row[tablemap['contact_email']]+"','"+row[tablemap['contact_phone']]+"','"+row[tablemap['website']]+"');"

#    print sqlcommand

    try:
        newcur.execute(sqlcommand)
    except Exception, e:
        print sqlcommand
        print "ERROR: ",e[0]
        
#    newdbconn.commit()


#newdbconn.close()
