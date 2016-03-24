from __future__ import absolute_import
from collections import namedtuple
import argparse
import ConfigParser
import logging

from django.core.management.base import BaseCommand
from pycsw.core import admin
from pycsw.core.config import StaticContext

from ...pycswsettings import build_pycsw_settings
from ... import mappings
#from ... import events  # relying on custom pycsw branch

logger = logging.getLogger(__name__)


class PycswAdminHandler(object):
    config = None
    config_defaults = {"table": "records",}

    def __init__(self):
        self.config = None
        self.context = None

    def parse_configuration(self, config, context):
        self.config = ConfigParser.SafeConfigParser(self.config_defaults)
        if isinstance(config, str):
            self.config.readfp(open(config))
        elif isinstance(config, dict):
            for section, options in config.iteritems():
                self.config.add_section(section)
                for k, v in options.iteritems():
                    self.config.set(section, k, v)
        self.context = context
        self.context.md_core_model = mappings.MD_CORE_MODEL
        self.context.refresh_dc(mappings.MD_CORE_MODEL)

    def handle_db(self, args):
        database, table = self._get_db_settings()
        if args.db_command == "create":
            home = self.config.get('server', 'home')
            admin.setup_db(database, table, home)
        elif args.db_command == "optimize":
            admin.optimize_db(self.context, database, table)
        elif args.db_command == "rebuild":
            admin.rebuild_db_indexes(database, table)
        elif args.db_command == "clean":
            force = args.accept_changes
            if not force:
                msg = "This will delete all records! Continue [Y/n] "
                if raw_input(msg) == 'Y':
                    force = True
            if force:
                admin.delete_records(self.context, database, table)

    def handle_load(self, args):
        database, table = self._get_db_settings()
        admin.load_records(self.context, database, table, args.input_directory,
                           args.recursive, args.accept_changes)

    def handle_export(self, args):
        database, table = self._get_db_settings()
        admin.export_records(self.context, database, table,
                             args.output_directory)

    def handle_harvest(self, args):
        database, table = self._get_db_settings()
        url = self.config.get("server", "url")
        admin.refresh_harvested_records(self.context, database, table, url)

    def handle_sitemap(self, args):
        database, table = self._get_db_settings()
        url = self.config.get("server", "url")
        admin.gen_sitemap(self.context, database, table, url, args.output_path)

    def handle_post(self, args):
        return admin.post_xml(args.url, args.xml, args.timeout)

    def handle_dependencies(self, args):
        return admin.get_sysprof()

    def handle_validate(self, args):
        admin.validate_xml(args.xml, args.xml_schema)

    def get_parser(self):
        parser = argparse.ArgumentParser(
            description="PyCSW command-line configuration tool")
        #parser.add_argument("-v", "--verbose", action="store_true",
        #                    help="Be verbose about the output")
        #parser.add_argument(
        #    "-c", "--config",
        #    help="Filepath to pycsw configuration. Alternatively, you "
        #         "can set the PYCSW_CONFIG environment variable"
        #)
        subparsers = parser.add_subparsers(title="Available commands")
        self._add_db_parser(subparsers)
        self._add_load_parser(subparsers)
        self._add_export_parser(subparsers)
        self._add_harvest_parser(subparsers)
        self._add_sitemap_parser(subparsers)
        self._add_post_parser(subparsers)
        self._add_dependencies_parser(subparsers)
        self._add_validate_parser(subparsers)
        return parser

    def _add_db_parser(self, subparsers_obj):
        parser = subparsers_obj.add_parser(
            "db", help="Manage repository",
            description="Perform actions on the database repository"
        )
        subsubparsers = parser.add_subparsers(title="Available commands")
        subsubs = {
            "create": ("Create a new repository",
                       "Creates a new database repository",
                       []),
            "optimize": ("Optimize the current repository",
                         "Optimizes the database repository",
                         []),
            "rebuild": ("Rebuild database indexes",
                        "Rebuilds database indexes for the repository",
                        []),
            "clean": ("Delete all records from the repository",
                      "Deletes all of the metadata records from the database "
                      "repository",
                      [
                          (("-y", "--accept-changes",),
                           {"action": "store_true",
                            "help": "Do not prompt for confirmation"},)
                      ],
                      )
        }
        for cmd, info in subsubs.iteritems():
            help_text, description, arguments = info
            p = subsubparsers.add_parser(cmd, help=help_text,
                                         description=description)
            for a in arguments:
                args, kwargs = a
                p.add_argument(*args, **kwargs)
            p.set_defaults(func=self.handle_db, db_command=cmd)

    def _add_load_parser(self, subparsers_obj):
        parser = subparsers_obj.add_parser(
            "load",
            help="Loads metadata records from directory into repository",
            description="Loads metadata records stored as XML files. Files "
                        "are searched in the input directory."
        )
        parser.add_argument(
            "input_directory",
            help="path to input directory to read metadata records"
        )
        parser.add_argument(
            "-r", "--recursive", help="Read sub-directories recursively",
            action="store_true")
        parser.add_argument(
            "-y", "--accept-changes", help="Force updates", action="store_true")
        parser.set_defaults(func=self.handle_load)

    def _add_export_parser(self, subparsers_obj):
        parser = subparsers_obj.add_parser(
            "export",
            help="Dump metadata records from repository into directory",
            description="Write all of the metadata records present in the "
                        "database into individual XML files. The files are "
                        "created at the specified output directory."
        )
        parser.add_argument(
            "output_directory",
            help="path to output directory to write metadata records"
        )
        parser.set_defaults(func=self.handle_export)

    def _add_harvest_parser(self, subparsers_obj):
        parser = subparsers_obj.add_parser(
            "harvest",
            help="Refresh harvested records",
            description="Refresh harvested records"
        )
        parser.set_defaults(func=self.handle_harvest)

    def _add_sitemap_parser(self, subparsers_obj):
        parser = subparsers_obj.add_parser(
            "sitemap",
            help="Generate XML sitemap",
            description="Generate an XML sitemap file"
        )
        parser.add_argument(
            "-o", "--output-path",
            help="full path to output file. Defaults to the current directory",
            default=".")
        parser.set_defaults(func=self.handle_sitemap)

    def _add_post_parser(self, subparsers_obj):
        parser = subparsers_obj.add_parser(
            "post",
            help="Generate HTTP POST requests",
            description="Generate HTTP POST requests to an input CSW server "
                        "using an input XML file with the request"
        )
        parser.add_argument("xml", help="Path to an XML file to be POSTed")
        parser.add_argument(
            "-u", "--url", default="http://localhost:8000/",
            help="URL endpoint of the CSW server to contact. Defaults "
                 "to %(default)s"
        )
        parser.add_argument(
            "-t", "--timeout", type=int, default=30,
            help="Timeout (in seconds) for HTTP requests. Defaults "
                 "to %(default)s"
        )
        parser.set_defaults(func=self.handle_post)

    def _add_dependencies_parser(self, subparsers_obj):
        parser = subparsers_obj.add_parser(
            "dependencies",
            help="Inspect the version of installed dependencies",
            description="Inspect the version of installed dependencies"
        )
        parser.set_defaults(func=self.handle_dependencies)

    def _add_validate_parser(self, subparsers_obj):
        parser = subparsers_obj.add_parser(
            "validate",
            help="Validate XML files against schema documents",
            description="Validate an input XML file with a CSW request using "
                        "an XML schema file"
        )
        parser.add_argument("xml", help="Path to an XML file to be validated")
        parser.add_argument(
            "-x", "--xml-schema",
            help="Path to an XMl schema file to use for validation"
        )
        parser.set_defaults(func=self.handle_validate)

    def _get_db_settings(self):
        database = self.config.get("repository", "database")
        table = self.config.get('repository', 'table')
        return database, table


class Command(BaseCommand):
    help = "Manage PyCSW catalogue"
    pycsw_admin_handler = PycswAdminHandler()

    def create_parser(self,prog_name, subcommand):
        parser = self.pycsw_admin_handler.get_parser()
        parser.add_argument('--version', action='version',
                           version=self.get_version())
        parser.add_argument('-v', '--verbosity', action='store',
                            dest='verbosity', default=1,
                            type=int, choices=[0, 1, 2, 3],
                            help='Verbosity level; 0=minimal output, '
                                 '1=normal output, 2=verbose output, '
                                 '3=very verbose output. Defaults to '
                                 '%(default)s')
        parser.add_argument(
            '--settings',
            help='The Python path to a settings module, e.g. '
                 '"myproject.settings.main". If this isn\'t provided, the '
                 'DJANGO_SETTINGS_MODULE environment variable will be used.',
            )
        parser.add_argument(
            '--pythonpath',
            help='A directory to add to the Python path, e.g. '
                 '"/home/djangoprojects/myproject".'
        )
        parser.add_argument('--traceback', action='store_true',
                            help='Raise on CommandError exceptions')
        parser.add_argument('--no-color', action='store_true',
                            dest='no_color', default=False,
                            help="Don't colorize the command output.")
        return parser

    def handle(self, *args, **options):
        log_level = {
            0: logging.ERROR,
            1: logging.WARNING,
            2: logging.INFO,
            3: logging.DEBUG
        }.get(options["verbosity"])
        logger.setLevel(log_level)
        pycsw_logger = logging.getLogger("pycsw")
        pycsw_logger.setLevel(log_level)
        pycsw_config = build_pycsw_settings()
        context = StaticContext()
        self.pycsw_admin_handler.parse_configuration(pycsw_config, context)
        ArgsObject = namedtuple("ArgsObject", options.keys())
        the_args = ArgsObject(**options)
        result = the_args.func(the_args)
        if result is not None:
            self.stdout.write(result)
        self.stdout.write("Done!")
