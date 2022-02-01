from django.core.management.base import BaseCommand
from cdl_journal_transfer_janeway.interfaces.journal_handler import JournalHandler

import json

class Command(BaseCommand):
    help = 'Import some shit'

    def add_arguments(self, parser):
        parser.add_argument("json_file", nargs=1, type=str)

    def handle(self, **options):
        with open(options["json_file"][0]) as file:
            data = json.load(file)

        if not data : return

        self.stdout.write(json.dumps(data, indent=2))

        handler = JournalHandler()
        handler.import_single(data)

        self.stdout.write("Done!?")
