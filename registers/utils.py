from django.contrib.admin import ModelAdmin
from .models import ITSystemHardware, ITSystem


class OimModelAdmin(ModelAdmin):
    """ OimModelAdmin"""

    def has_module_permission(self, request):
        user = request.user
        if user.is_superuser:
            return True

        if user.is_staff:
            if user.groups.filter(name="OIM Staff").exists():
                return True

        return False


def squash_duplicate_itsystemhardware():
    """Single-use migration script to remove any host/role duplicates.
    """
    for i in ITSystemHardware.objects.all():
        if ITSystemHardware.objects.filter(computer=i.computer, role=i.role).count() > 1:
            others = ITSystemHardware.objects.filter(computer=i.computer, role=i.role).exclude(pk=i.pk)
            # Alter any ITSystems to use the first ITSystemHardware object.
            for its in others:
                systems = ITSystem.objects.filter(hardwares__in=[its])
                for s in systems:
                    s.hardwares.remove(its)
                    s.hardwares.add(i)
                    s.save()

    # Now delete any ITSystemHardware objects with no linked ITSystems.
    for i in ITSystemHardware.objects.all():
        if i.itsystem_set.all().count() == 0:
            i.delete()

    print('Done!')
