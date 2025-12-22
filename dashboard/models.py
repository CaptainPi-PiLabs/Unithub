from django.db import models

from dashboard.manager import NavShortcutManager
from unithub.mixins.model_mixin import OrderedModelMixin


class NavShortcut(OrderedModelMixin, models.Model):
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=255)


    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        # Fix ordering after delete
        self.fix_ordering()