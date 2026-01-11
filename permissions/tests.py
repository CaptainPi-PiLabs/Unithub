from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from orbat.models import Section
from permissions.models import PermissionGroup, PermissionGroupMembership, PermissionGrant
from permissions.services import user_has_permission


class SectionPermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        # Users
        self.normal_user = User.objects.create(username="normal_user", display_name="Normal User")
        self.section_leader1 = User.objects.create(username="section_leader_1", display_name="Section Leader 1")
        self.section_leader2 = User.objects.create(username="section_leader_2", display_name="Section Leader 2")
        self.staff_user = User.objects.create(username="staff_user", display_name="Staff User")
        self.other_user = User.objects.create(username="other_user", display_name="Other User")

        # Groups
        self.section_all_edit = PermissionGroup.objects.create(name="AllSectionEditors")
        self.section_other_edit = PermissionGroup.objects.create(name="OtherSectionEditors")

        # Memberships
        PermissionGroupMembership.objects.create(user=self.staff_user, group=self.section_all_edit)
        PermissionGroupMembership.objects.create(user=self.other_user, group=self.section_other_edit)

        # Sections
        self.section1 = Section.objects.create(
            name="Section 1",
            leader=self.section_leader1,
            shorthand="S1",
            type="infantry",
            max_size=10,
            platoon=None
        )
        self.section2 = Section.objects.create(
            name="Section 2",
            leader=self.section_leader2,
            shorthand="S2",
            type="infantry",
            max_size=10,
            platoon=None
        )

        # ContentType for Section
        ct = ContentType.objects.get_for_model(Section)

        # Object-level grant: normal user can edit section1 only
        PermissionGrant.objects.create(
            group=self.section_other_edit,
            permission="modify",
            module="orbat",
            effect=PermissionGrant.ALLOW,
            content_type=ct,
            object_id=self.section1.id,
        )

        # Type-level grant: section leader can edit all sections
        PermissionGrant.objects.create(
            group=self.section_all_edit,
            permission="modify",
            module="orbat",
            effect=PermissionGrant.ALLOW,
            content_type=ct,
            object_id=None,
        )

    def test_normal_user_cannot_edit_any_section(self):
        """Normal user has no grants, should not be able to edit any section"""
        self.assertFalse(
            user_has_permission(self.normal_user, "modify", module="orbat", scope=self.section1))
        self.assertFalse(
            user_has_permission(self.normal_user, "modify", module="orbat", scope=self.section2))

    def test_section_leader1_inherits_permission_for_own_section(self):
        """Section leader 1 should be able to edit section1 via inherited rule"""
        self.assertTrue(
            user_has_permission(self.section_leader1, "modify", module="orbat", scope=self.section1))
        self.assertFalse(
            user_has_permission(self.section_leader1, "modify", module="orbat", scope=self.section2))

    def test_section_leader2_inherits_permission_for_own_section(self):
        """Section leader 2 should be able to edit section2 via inherited rule"""
        self.assertTrue(
            user_has_permission(self.section_leader2, "modify", module="orbat", scope=self.section2))
        self.assertFalse(
            user_has_permission(self.section_leader2, "modify", module="orbat", scope=self.section1))

    def test_other_user_can_edit_section1_only(self):
        """Other user has object-level grant for section1 only"""
        self.assertTrue(user_has_permission(self.other_user, "modify", module="orbat", scope=self.section1))
        self.assertFalse(user_has_permission(self.other_user, "modify", module="orbat", scope=self.section2))

    def test_staff_user_can_edit_all_sections(self):
        """Staff user has type-level grant: can edit any section"""
        self.assertTrue(user_has_permission(self.staff_user, "modify", module="orbat", scope=self.section1))
        self.assertTrue(user_has_permission(self.staff_user, "modify", module="orbat", scope=self.section2))