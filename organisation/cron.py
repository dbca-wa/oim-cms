from confy import env
from django.core.mail import send_mail
from django.template import loader
from django_cron import CronJobBase,Schedule
from .models import DepartmentUser
import logging


class PasswordReminderCronJob(CronJobBase):
    """ Model to send reminder emails to users about imminent password expiry """
    RUN_EVERY_MINS = 24*60 #run every 24 hours
    EXPIRY = [30,14,7,3,2,1] # password expires in 30,14,7,3,2,1 days
    EMAIL_FROM = env('EMAIL_FROM', "noreply@dpaw.wa.gov.au")

    schedule = Schedule(run_every_mins = RUN_EVERY_MINS)
    code = 'organisation.password_reminder_cron_job'
    logger  = logging.getLogger(__name__)

    def do(self):
        #send email to users with password which is about to expire
        try:
            users = [d for d in DepartmentUser.objects.all() if d.password_age_days in self.EXPIRY] #find users with passwords about to expire

            for u in users:
                context = {
                    'given_name':u.given_name,
                    'surname':u.surname,
                    'expiry': u.password_age_days
                }
                subject  = 'Password Expiry Reminder'

                template = loader.render_to_string('organisation/email/password_expiry_email.html',context)
                to = u.email

                send_mail(subject,template,self.EMAIL_FROM,[to],fail_silently=False,html_message=template)
                self.logger.info("Email sent to "+ u.email )
        except Exception as e:
            self.logger.error( str(e) )
'''
cron job command
0 0 * * * source /home/user/.bashrc && source /home/user/path/to/project/your-project/venv/bin/activate && python /home/user/path/to/project/your-project/manage.py runcrons > /home/user/path/to/project/tour-project/logs/cronjob.log
'''
