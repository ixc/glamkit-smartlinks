from django.core.management.base import BaseCommand

from smartlinks import smartlinks_conf
from smartlinks.models import IndexEntry

class ResetSmartLinkIndex(BaseCommand):
    can_import_settings = False
    requires_model_validation = False

    help = """Reset the index for smartlinks."""

    def handle(self, *args, **options):
        recreate_index()

def recreate_index():
    IndexEntry.objects.delete()
    seen = []
    for conf in smartlinks_conf.values():
        if conf in seen: continue
        seen.append(conf)

        # Generate index entries for corresponding items.
        conf.recreate_index()