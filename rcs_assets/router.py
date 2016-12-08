class RCSAssetsRouter(object):
    """
    A read-only router to control all database operations on models in the
    rcs_assets application.
    """
    def db_for_read(self, model, **hints):
        """
        Attempts to read rcs_assets models go to rcs_assets.
        """
        if model._meta.app_label == 'rcs_assets':
            return 'rcs_assets'
        return None

    def db_for_write(self, model, **hints):
        """
        No writes.
        """
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the rcs_assets app is involved.
        """
        if obj1._meta.app_label == 'rcs_assets' or obj2._meta.app_label == 'rcs_assets':
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        No migrations.
        """
        return None
