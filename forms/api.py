from __future__ import unicode_literals, absolute_import
from babel.dates import format_timedelta
from django.conf import settings
import itertools
import json
from oim_cms.utils import CSVDjangoResource
from restless.dj import DjangoResource
from restless.resources import skip_prepare
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.html import format_html
from json2html import json2html
from registers.models import ITSystem
from organisation.models import DepartmentUser
from django.core import serializers
from datetime import datetime
from organisation.Groups import groupCheck

def ITSystemObj(self):
    # Get It system Request Data and Custdian Basic Info and return a json response.
    reqid = self.GET["reqid"]
    if not self.user.is_authenticated():
        return HttpResponseForbidden()

    PermsResp = ITSystemPermssionCheck(self,reqid)
    if PermsResp == False:
        return HttpResponseForbidden()

    itrequest = []
    itsobj = {
            'reqid': '',
            'reqname': '',
            'surname': '',
            'title': '',
            'labelfield': '',
            'custodianid': '',
            'reqdescription': '',
            'reqcustodianid' : '',
            'reqnotes': '',
            'reqdocumentation': '',
            'reqtechnical_documentation': '',
            'reqsystem_reqs': '',
            'reqworkaround': '',
            'reqrecovery_docs': '',
            'reqsystem_creation_date': '',
            'reqcritical_period': '',
            'reqalt_processing': '',
            'reqtechnical_recov': '',
            'reqpost_recovery': '',
            'requser_notification': '',
            'requnique_evidence': '',
            'reqpoint_of_truth': '',
            'reqlegal_need_to_retain': '',
          }

    ITSystem.objects.only('id','name','description','notes','documentation','technical_documentation','system_reqs','workaround','recovery_docs','system_creation_date','critical_period','alt_processing','technical_recov','post_recovery','user_notification','unique_evidence','point_of_truth','legal_need_to_retain')

    resp2 = ITSystem.objects.filter(id=reqid)
    for value in resp2:
            itsobj['reqid'] = value.id
            itsobj['reqname'] =  value.name
            itsobj['reqdescription'] = value.description
            itsobj['reqcustodianid'] = value.custodian_id
            itsobj['reqnotes'] = value.notes
            itsobj['reqdocumentation'] = value.documentation
            itsobj['reqtechnical_documentation'] = value.technical_documentation
            itsobj['reqsystem_reqs'] = value.system_reqs
            itsobj['reqworkaround'] = value.workaround
            itsobj['reqrecovery_docs'] = value.recovery_docs
            itsobj['reqcritical_period'] = value.critical_period
            itsobj['reqalt_processing'] = value.alt_processing
            itsobj['reqtechnical_recov'] = value.technical_recov
            itsobj['reqpost_recovery'] = value.post_recovery
            itsobj['requser_notification'] = value.user_notification
            itsobj['requnique_evidence'] = value.unique_evidence
            itsobj['reqpoint_of_truth'] = value.point_of_truth
            itsobj['reqlegal_need_to_retain'] = value.legal_need_to_retain

            if value.system_creation_date:
                itsobj['reqsystem_creation_date'] = value.system_creation_date.strftime('%d/%m/%Y')
            else:
                itsobj['reqsystem_creation_date'] = ""

    if itsobj['reqcustodianid']:
        DepartmentUser.objects.only('id','given_name','surname', 'title','org_unit')
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
    reqnotes =  self.POST["reqnotes"]
    reqdocumentation =  self.POST["reqdocumentation"]
    reqtechnical_documentation = self.POST["reqtechnical_documentation"]
    reqsystem_reqs = self.POST["reqsystem_reqs"]
    reqworkaround = self.POST["reqworkaround"]
    reqrecovery_docs = self.POST["reqrecovery_docs"]
    reqsystem_reqs = self.POST["reqsystem_reqs"]
    reqcritical_period = self.POST["reqcritical_period"]
    reqalt_processing = self.POST["reqalt_processing"]
    reqtechnical_recov = self.POST["reqtechnical_recov"]
    reqpost_recovery = self.POST["reqpost_recovery"]
    requser_notification = self.POST["requser_notification"]
    requnique_evidence = self.POST["requnique_evidence"]
    reqpoint_of_truth = self.POST["reqpoint_of_truth"]
    reqlegal_need_to_retain = self.POST["reqlegal_need_to_retain"]
    reqsystem_creation_date = self.POST["reqsystem_creation_date"]

    PermsResp = ITSystemPermssionCheck(self,reqid)
    if PermsResp == False:
        return HttpResponseForbidden()


    itsystemreq.custodian_id = reqcustodian
    itsystemreq.name = reqname
    itsystemreq.description = reqdescription
    itsystemreq.notes = reqnotes
    itsystemreq.documentation = reqdocumentation
    itsystemreq.technical_documentation = reqtechnical_documentation
    itsystemreq.system_reqs = reqsystem_reqs
    itsystemreq.workaround = reqworkaround
    itsystemreq.system_reqs = reqsystem_reqs
    itsystemreq.critical_period = reqcritical_period
    itsystemreq.alt_processing  = reqalt_processing
    itsystemreq.technical_recov = reqtechnical_recov
    itsystemreq.post_recovery = reqpost_recovery
    itsystemreq.user_notification = requser_notification
    itsystemreq.unique_evidence = str2bool(requnique_evidence)
    itsystemreq.point_of_truth = str2bool(reqpoint_of_truth)
    itsystemreq.legal_need_to_retain = str2bool(reqlegal_need_to_retain)
    itsystemreq.system_creation_date = datetime.strptime(reqsystem_creation_date, '%d/%m/%Y')

    itsystemreq.save()

    return HttpResponse('Saved')

def str2bool(v):
    if v.lower() in ("yes", "true", "t", "1"):
        return True

    if v.lower() in ("no", "false", "f", "0"):
        return False
    else:
        return


def ITSystemPermssionCheck(self,reqid):
    permObj = {}
    PermUserInfo = {}
    permObj['groupcheck'] = False
    permObj['custodiancheck'] = False
    permObj['superUserCheck'] = self.user.is_superuser
    PermUserInfo['userid'] = 0

    # Check Logged in User is in Group
    permObj['groupcheck'] = groupCheck(self, 'OIM Staff')

    # Get custonian id from IT System Req
    itsystemreq = ITSystem.objects.filter(id=reqid)
    for value in itsystemreq:
        PermUserInfo['userid'] = value.custodian_id

    # Check Custonian if Matches IT System Req
    DepartmentUser.objects.only('id')
    rows = DepartmentUser.objects.filter(username=self.user.username)
    for value in rows:
        if value.id == PermUserInfo['userid']:
            permObj['custodiancheck'] = True

    if permObj['groupcheck'] == True:
        return True
    elif permObj['custodiancheck'] == True:
        return True
    elif permObj['superUserCheck'] == True:
        return True
    else:
        return False








