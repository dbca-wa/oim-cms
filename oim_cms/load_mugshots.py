#!/usr/bin/env python
import os

from tracking.models import DepartmentUser
from django.core.files.base import ContentFile

DATA_DIR = '/root/mugshots'

files = [x for x in os.listdir(DATA_DIR) if os.path.isfile(os.path.join(DATA_DIR, x))]

valid = 0

for f in files:
    name = os.path.splitext(f)[0]
    qs = DepartmentUser.objects.filter(username__iexact=name)
    if qs:
        with open(os.path.join(DATA_DIR, f)) as fp:
            qs[0].photo.save(f, ContentFile(fp.read()))
        print('+++ - Updated photo for {}'.format(name))
        valid += 1
    else:
        print('!!! - Username {} not found'.format(name))

print('{}/{} photos valid'.format(valid, len(files)))
