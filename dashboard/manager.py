from django.db import models
from django.db.models import Max


class NavShortcutManager(models.Manager):
    def next_order(self):
        """Get the next available order for a new shortcut"""
        max_order = self.aggregate(Max('order'))['order__max']
        return 1 if max_order is None else max_order + 1

    def fix_ordering(self):
        """Renumber all shortcuts sequentially starting from 1"""
        shortcuts = self.all().order_by('order', 'id')
        for idx, shortcut in enumerate(shortcuts, start=1):
            if shortcut.order != idx:
                shortcut.order = idx
                shortcut.save(update_fields=['order'])