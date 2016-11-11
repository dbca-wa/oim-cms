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

f =  open('locmap.csv', 'r')
for line in f.readlines():
    oldid,newid = line.strip().split(',')
    if len(newid) > 0:
        locmap[oldid] = int(newid)
    else:
        locmap[oldid] = 200

# New Database Connection
newdbconn = psycopg2.connect(database=env("NEW_DB"), user=env("NEW_DB_USER"), password=env("NEW_DB_PASS"), host=env("NEW_DB_HOST"), port="5432")
# OLD database Connection 
olddbconn = psycopg2.connect(database=env("OLD_DB"), user=env("OLD_DB_USER"), password=env("OLD_DB_PASS"), host=env("OLD_DB_HOST"), port="5432")

newcur = newdbconn.cursor()
oldcur = olddbconn.cursor()

# Add Default Data
sqlcommand = "insert into assets_vendor (id,name) values (0,'Unknown Vendor');";
try:
    newcur.execute(sqlcommand)
except Exception, e:
    print "ERROR: ",e[0]

newdbconn.commit()

sqlcommand = "insert into organisation_location (id,name,address,pobox) values (0,'Unknown Location', 'Unknown Address','Unknown PO Box');";
try:
    newcur.execute(sqlcommand)
except Exception, e:
    print "ERROR: ",e[0]

newdbconn.commit()

# Assets_Supplier
tablemap = {}
rowjson = {}
tablemap['id'] = 0
tablemap['creator_id'] = 1
tablemap['modifier_id'] = 2
tablemap['created'] = 3
tablemap['modified'] = 4
tablemap['name'] = 5
tablemap['account_rep'] = 6
tablemap['contact_email'] = 7
tablemap['contact_phone'] = 8
tablemap['website'] = 9
tablemap['notes'] = 10

query="select id,creator_id,modifier_id,created,modified,name,account_rep,contact_email,contact_phone,website,notes from assets_supplier"
oldcur.execute(query)
rows=oldcur.fetchall()
for row in rows:
    rowjson = { "id": row[tablemap['id']],
                "creator_id": row[tablemap['creator_id']],
                "modifier_id": row[tablemap['modifier_id']],
                "created": str(row[tablemap['created']]),
                "modified": str(row[tablemap['modified']]),
                "name": row[tablemap['name']],
                "account_rep": row[tablemap['account_rep']],
                "contact_email": row[tablemap['contact_email']],
                "contact_phone": row[tablemap['contact_phone']],
                "website": row[tablemap['website']],
                "notes":row[tablemap['notes']]
    }

    rowjsonstring = json.dumps(rowjson);
    sqlcommand = "insert into assets_vendor (id,name,details,extra_data,account_rep,contact_email,contact_phone,website) values ("+str(row[tablemap['id']])+",'"+row[tablemap['name']]+"','"+row[tablemap['notes']]+"','"+rowjsonstring+"','"+row[tablemap['account_rep']]+"','"+row[tablemap['contact_email']]+"','"+row[tablemap['contact_phone']]+"','"+row[tablemap['website']]+"');"

    print sqlcommand

    try:
        newcur.execute(sqlcommand)
    except Exception, e:
        print "ERROR: ",e[0]

    newdbconn.commit()


# Asset Hardware Model
rowjson = {}
tablemap = {}
tablemap['id'] = 0
tablemap['creator_id'] = 1
tablemap['modifier_id'] = 2
tablemap['created'] = 3
tablemap['modified'] = 4
tablemap['manufacturer_id'] = 5
tablemap['model'] = 6
tablemap['lifecycle'] = 7
tablemap['notes'] = 8
tablemap['model_type'] = 9

query="select id,creator_id,modifier_id,created,modified,manufacturer_id,model,lifecycle,notes,model_type from assets_model"
oldcur.execute(query)
rows=oldcur.fetchall()
for row in rows:


    rowjson = { "id": row[tablemap['id']],
                "creator_id": row[tablemap['creator_id']],
                "modifier_id": row[tablemap['modifier_id']],
                "created": str(row[tablemap['created']]),
                "modified": str(row[tablemap['modified']]),
                "manufacturer_id": row[tablemap['manufacturer_id']],
                "model": row[tablemap['model']],
                "lifecycle": row[tablemap['lifecycle']],
                "notes": str(row[tablemap['notes']]),
                "model_type":str(row[tablemap['model_type']]),
    }

    rowjsonstring = json.dumps(rowjson)

    suppliermap[row[tablemap['id']]] = row[tablemap['manufacturer_id']]

    sqlcommand = "insert into assets_hardwaremodel (id,model_type,model_no,lifecycle,notes,vendor_id) values ("+str(row[tablemap['id']])+",'"+row[tablemap['model_type']]+"','"+row[tablemap['model']]+"','"+str(row[tablemap['lifecycle']])+"','"+row[tablemap['notes']]+"','"+str(row[tablemap['manufacturer_id']])+"');"

    print sqlcommand 

    try:
        newcur.execute(sqlcommand)
    except Exception, e:
        print "ERROR: ",e[0]

    newdbconn.commit()


# Asset Invoice 
rowjson = {}
tablemap = {}
tablemap['id'] = 0
tablemap['creator_id'] = 1
tablemap['modifier_id'] = 2
tablemap['created'] = 3
tablemap['modified'] = 4
tablemap['supplier_id'] = 5
tablemap['supplier_ref'] = 6
tablemap['job_number'] = 7
tablemap['total_value'] = 8
tablemap['notes'] = 9
tablemap['date'] = 10
tablemap['cost_centre_name'] = 11
tablemap['cost_centre_number'] = 12
tablemap['etj_number'] = 13

query="select id,creator_id,modifier_id,created,modified,supplier_id,supplier_ref,job_number,total_value,notes,date,cost_centre_name,cost_centre_number,etj_number from assets_invoice"
oldcur.execute(query)
rows=oldcur.fetchall()
for row in rows:

    rowjson = { "id": row[tablemap['id']],
                "creator_id": row[tablemap['creator_id']],
                "modifier_id": row[tablemap['modifier_id']],
                "created": str(row[tablemap['created']]),
                "modified": str(row[tablemap['modified']]),
                "supplier_id": row[tablemap['supplier_id']],
                "supplier_ref": row[tablemap['supplier_ref']],
                "job_number": row[tablemap['job_number']],
                "total_value": str(row[tablemap['total_value']]),
                "notes": row[tablemap['notes']],
                "date":str(row[tablemap['date']]),
                "cost_centre_name":row[tablemap['cost_centre_name']],
                "cost_centre_number": row[tablemap['cost_centre_number']],
                "etj_number": row[tablemap['etj_number']]
    }

    rowjsonstring = json.dumps(rowjson)



    total_value = row[tablemap['total_value']]
    if isinstance(row[tablemap['total_value']], NoneType) is True:
        total_value = str('null') 
    else: 
        if total_value:
            total_value = "'"+str(total_value)+"'"
        else:
            total_value = null
    
    date = row[tablemap['date']]
    if isinstance(row[tablemap['date']], NoneType) is True:
        date = str('null')
    else:
        print type(date)
        if len(str(date)) > 2:
            print type(date)

            date = "'"+str(date)+"'"
        else:
            date = 'null'

    notes = row[tablemap['notes']]
    #notes =  string.replace(notes,"'","''")


    sqlcommand = "insert into assets_invoice (id,date_created,date_updated,extra_data,vendor_ref,job_number,date,etj_number,total_value,notes,cost_centre_id,org_unit_id,vendor_id) values "
    sqlcommand = sqlcommand + "("+str(row[tablemap['id']])+",'"
    sqlcommand = sqlcommand +   str(row[tablemap['created']])+"','"
    sqlcommand = sqlcommand +   str(row[tablemap['modified']])+"',"
    sqlcommand = sqlcommand + "'"+rowjsonstring+"',"
    sqlcommand = sqlcommand + "'"+row[tablemap['supplier_ref']]+"',"
    sqlcommand = sqlcommand + "'"+row[tablemap['job_number']]+"',"
    sqlcommand = sqlcommand + ""+date+","
    sqlcommand = sqlcommand + "'"+row[tablemap['etj_number']]+"',"
    sqlcommand = sqlcommand + ""+total_value+","
    sqlcommand = sqlcommand + "'"+notes+"',"
    sqlcommand = sqlcommand + "null,"
    sqlcommand = sqlcommand + "null,"
    sqlcommand = sqlcommand + str(row[tablemap['supplier_id']])+");"

    print sqlcommand

    try:
        newcur.execute(sqlcommand)
    except Exception, e:
        print "ERROR: ",e[0]

    newdbconn.commit()

# Hardware Assets

tablemap = {}
tablemap['id'] = 0
tablemap['creator_id'] = 1
tablemap['modifier_id'] = 2
tablemap['created'] = 3
tablemap['modified'] = 4
tablemap['asset_tag'] = 5
tablemap['model_id'] = 6
tablemap['serial'] = 7
tablemap['date_purchased'] = 8
tablemap['location_id'] = 9
tablemap['assigned_user'] = 10
tablemap['status'] = 11
tablemap['invoice_id'] = 12
tablemap['purchased_value'] = 13
tablemap['notes'] = 14
tablemap['finance_asset_tag'] = 15

query="select id,creator_id,modifier_id,created,modified,asset_tag,model_id,serial,date_purchased,location_id,assigned_user,status,invoice_id,purchased_value,notes,finance_asset_tag from assets_asset "
oldcur.execute(query)
rows=oldcur.fetchall()
for row in rows:

    rowjson = { "id": row[tablemap['id']],
                "creator_id": row[tablemap['creator_id']],
                "modifier_id": row[tablemap['modifier_id']],
                "created": str(row[tablemap['created']]),
                "modified": str(row[tablemap['modified']]),
                "asset_tag": row[tablemap['asset_tag']],
                "model_id": row[tablemap['model_id']],
                "serial": row[tablemap['serial']],
                "date_purchased": str(row[tablemap['date_purchased']]),
                "location_id": row[tablemap['location_id']],
                "assigned_user":str(row[tablemap['assigned_user']]),
                "status": str(row[tablemap['status']]),
                "invoice_id": row[tablemap['invoice_id']],
                "purchased_value": str(row[tablemap['purchased_value']]),
                "notes": row[tablemap['notes']],
                "finance_asset_tag": row[tablemap['finance_asset_tag']],
    }

    rowjsonstring = json.dumps(rowjson)

    invoice_id = row[tablemap['invoice_id']]
    if isinstance(row[tablemap['invoice_id']], NoneType) is True:
        invoice_id = str('null')
    else:
        if invoice_id:
            invoice_id = "'"+str(invoice_id)+"'"
        else:
            invoice_id = "null" 

    purchased_value = row[tablemap['purchased_value']]
    if isinstance(row[tablemap['purchased_value']], NoneType) is True:
        purchased_value = str("'0.00'")
    else:
        if purchased_value:
            purchased_value = "'"+str(purchased_value)+"'"
        else:
            purchased_value = "'0.00'" 

    if purchased_value == "None": 
        purchased_value = "'0.00'"
    elif len(purchased_value) == 0:
        purchased_value = "'0.00'"

    assigned_user = row[tablemap['assigned_user']]

    assigned_user_id = "null"
    if len(assigned_user) > 2:
        # Locate Assigned User
        assigned_user = string.replace(assigned_user,"'","''")
        q="select id from organisation_departmentuser where concat(given_name,' ',surname) = '"+assigned_user+"';"
        print q
        newcur.execute(q)
        result=newcur.fetchone()
        if isinstance(result, NoneType) is True:
            assigned_user_id = "null"
        else:
            print "ASSIGNED USER ID:"+str(result[0])
            if result[0] > 0:
                assigned_user_id = str(result[0])
            else:
                assigned_user_id = "null"


    sqlcommand = "insert into assets_hardwareasset (id,date_created,date_updated,extra_data,date_purchased,purchased_value,notes,asset_tag,finance_asset_tag,status,serial,assigned_user_id,cost_centre_id,hardware_model_id,invoice_id,location_id,org_unit_id,vendor_id) values "
    sqlcommand = sqlcommand + "('"+str(row[tablemap['id']])+"',"
    sqlcommand = sqlcommand + "'"+str(row[tablemap['created']])+"',"
    sqlcommand = sqlcommand + "'"+str(row[tablemap['modified']])+"',"
    sqlcommand = sqlcommand + "'"+rowjsonstring+"',"
    sqlcommand = sqlcommand + "'"+str(row[tablemap['date_purchased']])+"',"
    sqlcommand = sqlcommand + ""+purchased_value+","
    sqlcommand = sqlcommand + "'"+row[tablemap['notes']]+"',"
    sqlcommand = sqlcommand + "'"+row[tablemap['asset_tag']]+"',"
    sqlcommand = sqlcommand + "'"+row[tablemap['finance_asset_tag']]+"',"
    sqlcommand = sqlcommand + "'"+row[tablemap['status']]+"',"
    sqlcommand = sqlcommand + "'"+row[tablemap['serial']]+"',"
    sqlcommand = sqlcommand + assigned_user_id+"," # assigned user id
    sqlcommand = sqlcommand + "null,"
    sqlcommand = sqlcommand + str(row[tablemap['model_id']])+","
    sqlcommand = sqlcommand + invoice_id+","
    sqlcommand = sqlcommand + str(locmap.get(row[tablemap['location_id']],'0'))+","
    sqlcommand = sqlcommand + "null,"
    sqlcommand = sqlcommand + str(suppliermap.get(row[tablemap['model_id']],'null'))+"" # use model_id to 
    
    
    sqlcommand = sqlcommand + ");"

    print sqlcommand

    try:
        newcur.execute(sqlcommand)
    except Exception, e:
        print "ERROR: ",e[0]

    newdbconn.commit()

newdbconn.close()
