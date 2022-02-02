from django.core.management.base import BaseCommand
from cdl_journal_transfer_janeway.interfaces.journal_handler import JournalHandler

import json

class Command(BaseCommand):
    help = 'Import some shit'

    def add_arguments(self, parser):
        parser.add_argument("operation", nargs=1, type=str)
        parser.add_argument("--file", nargs=1, type=str)
        parser.add_argument("--")

    def handle(self, **options):
        if options["operation"] == "get":
            self.handle_get(*args, **options)
        elif options["operation"] == "put":
            self.handle_put(*args, **options)


    def handle_get(self, *args, **options):
        pass # WIP


    def handle_put(self, *args, **options):
        with open(options["json_file"][0]) as file:
            data = json.load(file)

        if not data : return

        self.stdout.write(json.dumps(data, indent=2))

        handler = JournalHandler()
        handler.import_single(data)

        self.stdout.write("Done!?")
