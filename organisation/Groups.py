from datetime import datetime

def groupCheck(request, groupname):

    for group in request.user.groups.all():
        if group.name ==  groupname:
            return True


    return False

