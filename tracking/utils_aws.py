from __future__ import absolute_import, unicode_literals
import json
import os

from .models import EC2Instance
from .utils import logger_setup


def aws_load_instances():
    """Update the database with EC2 Instance information.
    """
    logger = logger_setup('aws_load_instances')
    logger_ex = logger_setup('exceptions_aws_load_instances')
    json_path = os.environ.get('AWS_JSON_PATH')

    # Serialise the instance data.
    ec2_info = open(os.path.join(json_path, 'aws_ec2_describe_instances.json'))
    ec2_info = json.loads(ec2_info.read())
    ssm_info = open(os.path.join(json_path, 'aws_ssm_instance_information.json'))
    ssm_info = json.loads(ssm_info.read())
    inst_ssm = {i['InstanceId']: i for i in ssm_info['InstanceInformationList']}
    inst_ec2 = {}
    for i in ec2_info['Reservations']:
        for j in i['Instances']:
            inst_ec2[j['InstanceId']] = j

    for k, v in inst_ec2.iteritems():
        try:
            if EC2Instance.objects.filter(ec2id=k).exists():
                ec2 = EC2Instance.objects.get(ec2id=k)
            else:
                ec2 = EC2Instance(ec2id=k)
            # Parse the silly 'Tags' output.
            name = None
            tags = {}
            for t in v['Tags']:
                if t['Key'].lower() == 'name':
                    name = t['Value']
                tags[t['Key']] = t['Value']

            ec2.name = name
            ec2.tags = tags
            ec2.save()
            logger.info('EC2 instance {} ({}) updated'.format(ec2.ec2id, ec2.name))
        except Exception as e:
            logger_ex.error('Error while loading EC2 instance information')
            logger_ex.exception(e)

    for k, v in inst_ssm.iteritems():
        if k.startswith('i'):  # Don't check objects without an EC2 instance ID.
            try:
                if EC2Instance.objects.filter(ec2id=k).exists():
                    ec2 = EC2Instance.objects.get(ec2id=k)
                else:
                    ec2 = EC2Instance(ec2id=k)

                ec2.agent_version = v['AgentVersion']
                ec2.save()
                logger.info('EC2 instance {} ({}) updated'.format(ec2.ec2id, ec2.name))
            except Exception as e:
                logger_ex.error('Error while loading EC2 instance information')
                logger_ex.exception(e)
