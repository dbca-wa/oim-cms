from __future__ import unicode_literals, absolute_import
from django.db.models import F
from oim_cms.utils import CSVDjangoResource
from restless.resources import skip_prepare

from .models import EC2Instance


class EC2InstanceResource(CSVDjangoResource):
    VALUES_ARGS = (
        'pk', 'name', 'ec2id', 'launch_time', 'running', 'next_state'
    )

    def is_authenticated(self):
        return True

    def list_qs(self):
        if 'ec2id' in self.request.GET:
            return EC2Instance.objects.filter(
                ec2id=self.request.GET['ec2id']).values(*self.VALUES_ARGS)
        else:
            return EC2Instance.objects.exclude(
                running=F('next_state')).values(*self.VALUES_ARGS)

    @skip_prepare
    def list(self):
        data = list(self.list_qs())
        return data

    @skip_prepare
    def create(self):
        if not isinstance(self.data, list):
            self.data = [self.data]
            deleted = None
        else:
            deleted = EC2Instance.objects.exclude(
                ec2id__in=[i['InstanceId'] for i in self.data]).delete()
        for instc in self.data:
            instance, created = EC2Instance.objects.get_or_create(ec2id=instc['InstanceId'])
            instance.name = [x['Value'] for x in instc['Tags'] if x['Key'] == 'Name'][0]
            instance.launch_time = instc['LaunchTime']
            instance.running = instc['State']['Name'] == 'running'
            instance.extra_data = instc
            instance.save()
        return {'saved': len(self.data), 'deleted': deleted}
