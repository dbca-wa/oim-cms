from __future__ import unicode_literals, absolute_import
from babel.dates import format_timedelta
from django.conf import settings
import itertools
import json
from oim_cms.utils import CSVDjangoResource
from restless.dj import DjangoResource
from restless.resources import skip_prepare
from django.http import HttpResponse
from django.utils.html import format_html
from json2html import json2html
from registers.models import ITSystem
from organisation.models import DepartmentUser 
from django.core import serializers

def ITSystemObj(self):
    # Get It system Request Data and Custdian Basic Info and return a json response.

    reqid = self.GET["reqid"]
    itrequest = []
    itsobj = { 
            'reqid': '',
            'reqname': '',
            'surname': '',
            'title': '',
            'labelfield': '',
            'custodianid': '',
            'reqdescription': '',
            'reqcustodianid' : ''
          }

    ITSystem.objects.only('id','name','description')
    resp2 = ITSystem.objects.filter(id=reqid)
    for value in resp2:
            itsobj['reqid'] = value.id
            itsobj['reqname'] =  value.name
            itsobj['reqdescription'] = value.description
            itsobj['reqcustodianid'] = value.custodian_id

    DepartmentUser.objects.only('id','given_name','surname', 'title')
    rows = DepartmentUser.objects.filter(id=itsobj['reqcustodianid'])
    for value in rows:
            itsobj['custodianid'] = value.id
            itsobj['given_name'] = value.given_name
            itsobj['surname'] = value.surname
            itsobj['title'] = value.title
            itsobj['labelfield'] =  value.given_name + ' ' + value.surname + ' - ' + value.title
            itsobj['searchfield'] = value.given_name + ' ' + value.surname + ' ' + value.title 

    itrequest.append(itsobj)

    data = json.dumps(itrequest)

    return HttpResponse(data)

def PeopleObj(self):
    # Allow filtered list of people based on name and job title keyword search and return json response.

    stringval = ''
    OrgPeople = []
    keyword = self.GET["keyword"]
    if keyword: 
        rows = DepartmentUser.objects.filter(name__contains=keyword) | DepartmentUser.objects.filter(title__contains=keyword) 
        for value in rows:
            stringval = stringval + value.name
            stringval = stringval + "<BR>"
            row = {
                'id': value.id,
                'given_name': value.given_name,
                'surname': value.surname,
                'searchfield': value.given_name + ' ' + value.surname + ' ' + value.title,
                'labelfield':  value.given_name + ' ' + value.surname + ' - ' + value.title,
                'title': value.title

            }
            OrgPeople.append(row)

        data =    json.dumps(OrgPeople)
        if data: 
            return HttpResponse( data ) 
        else: 
            return HttpResponse( "" )
    else: 
        return HttpResponse( "" )


def SaveITSystemRequest(self):
    # Save changes to IT system Request Table, eg custodian, description, name

    reqid = self.POST["reqid"]
    reqcustodian = self.POST["reqcustodian"]
    reqname = self.POST["reqname"]
    reqdescription = self.POST["reqdescription"]
    itsystemreq = ITSystem.objects.get(id=reqid)   
    
    itsystemreq.custodian_id = reqcustodian
    itsystemreq.name = reqname
    itsystemreq.description = reqdescription
    itsystemreq.save()
    
    return HttpResponse('Saved')



