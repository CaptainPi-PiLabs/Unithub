from django.db import models
from django.db.models import Max, F


class OrderedModelMixin(models.Model):
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]
        abstract = True

    def _get_ordering_scope(self):
        """
        Determine the queryset scope for ordering.
        Priority:
        1. Custom attribute `_order_scope_fields` on the instance
        2. unique_together containing 'order'
        3. None (global)
        """

        qs = type(self).objects.all()
        scope_fields = getattr(self, "_order_scope_fields", None)

        if not scope_fields:
            unique_fields = getattr(self._meta, "unique_together", None)
            if unique_fields:
                for field_tuple in unique_fields:
                    if "order" in field_tuple:
                        scope_fields = [f for f in field_tuple if f != "order"]
                        break

        if scope_fields:
            filter_kwargs = {f: getattr(self, f) for f in scope_fields}
            qs = qs.filter(**filter_kwargs)

        return qs, scope_fields

    def save(self, *args, **kwargs):
        # Only assign order if this is a new object or order not set
        if not self.pk or not self.order:
            qs, _ = self._get_ordering_scope()
            max_order = qs.aggregate(max_order=Max("order"))["max_order"] or 0
            self.order = max_order + 1
        super().save(*args, **kwargs)

    @classmethod
    def fix_ordering(cls):
        """
        Renumber all objects sequentially based on _order_scope_fields,
        then unique_together containing 'order', then globally.
        """
        qs = cls.objects.all().order_by("order", "id")
        instance = cls()
        _, scope_fields = instance._get_ordering_scope()

        if scope_fields:
            # Build a set of all unique combinations for this scope
            seen_scopes = set()
            for obj in qs:
                key = tuple(getattr(obj, f) for f in scope_fields)
                seen_scopes.add(key)

            for key in seen_scopes:
                filter_kwargs = dict(zip(scope_fields, key))
                sub_qs = qs.filter(**filter_kwargs).order_by("order", "id")
                for idx, obj in enumerate(sub_qs, start=1):
                    if obj.order != idx:
                        obj.order = idx
                        obj.save(update_fields=["order"])
        else:
            # No scope, global renumber
            for idx, obj in enumerate(qs, start=1):
                if obj.order != idx:
                    obj.order = idx
                    obj.save(update_fields=["order"])

    # --- Core move logic ---
    def _move(self, up=True):
        qs, _ = self._get_ordering_scope()
        current_order = self.order

        if up:
            if current_order == 1:
                return  # Already at top
            neighbor = qs.filter(order__lt=current_order).order_by("-order").first()
        else:
            max_order = qs.aggregate(max_order=Max("order"))["max_order"] or current_order
            if current_order >= max_order:
                return  # Already at bottom
            neighbor = qs.filter(order__gt=current_order).order_by("order").first()

        if neighbor:
            # Swap orders directly
            neighbor_order = neighbor.order
            neighbor.order = current_order
            neighbor.save(update_fields=["order"])

            self.order = neighbor_order
            self.save(update_fields=["order"])

    # --- Public move methods ---
    def move_up(self):
        self._move(up=True)
        type(self).fix_ordering()

    def move_down(self):
        self._move(up=False)
        type(self).fix_ordering()

    def move_to(self, target_position):
        """
        Shifts other objects in the scope accordingly.
        Move the current object to a specific position.
        Runs fix ordering in case of remaining gaps.
        """
        if self.order == target_position:
            return  # Already in position

        qs, _ = self._get_ordering_scope()

        if target_position < self.order:
            # Moving up: increment orders for items in [target_position, current_order-1]
            qs.filter(order__gte=target_position, order__lt=self.order).update(order=F('order') + 1)
        else:
            # Moving down: decrement orders for items in [current_order+1, target_position]
            qs.filter(order__gt=self.order, order__lte=target_position).update(order=F('order') - 1)

        # Assign new order to self
        self.order = target_position
        self.save(update_fields=["order"])

        # Renumber sequentially to remove gaps
        type(self).fix_ordering()