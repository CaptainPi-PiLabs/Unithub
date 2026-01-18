from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apis.models import UserAPIKey, ServiceAPIKey, APIKeyBase
from orbat.enums import OrbatActions
from orbat.models import Section
from permissions.models import PermissionGrant, PermissionRule, PermissionModule

User = get_user_model()

class APIAuthTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user1")

        self.section1 = Section.objects.create(
            name="Section 1",
            leader=self.user,
            shorthand="S1",
            type="infantry",
            max_size=10,
            platoon=None,
            order=0
        )

        self.rule, _ = PermissionRule.objects.get_or_create(
            module=PermissionModule.ORBAT,
            action=OrbatActions.MODIFY_SECTION.value
        )

        self.url = reverse("api-orbat-section-membership", kwargs={"section_slug": self.section1.slug})

        self.client = APIClient()

    def test_user_key_auth_success(self):
        key = UserAPIKey.objects.create(user=self.user, name="key1")
        PermissionGrant.objects.create(
            user_api_key=key,
            rule=self.rule,
            effect=PermissionGrant.ALLOW,
        )
        response = self.client.get(self.url, HTTP_X_API_KEY=key._raw_key)
        self.assertEqual(response.status_code, 200)

    def test_anonymous_auth_fail(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_user_key_missing_perms(self):
        key = ServiceAPIKey.objects.create(name="key2")
        response = self.client.get(self.url, HTTP_X_API_KEY=key._raw_key)
        self.assertEqual(response.status_code, 403)

    def test_invalid_key_fails(self):
        response = self.client.get(self.url, HTTP_X_API_KEY=APIKeyBase.generate_key())
        self.assertEqual(response.status_code, 401)

    def test_service_key_ip_restriction(self):
        skey = ServiceAPIKey.objects.create(name="svc", allowed_ips="1.2.3.4")
        PermissionGrant.objects.create(
            service_api_key=skey,
            rule=self.rule,
            effect=PermissionGrant.ALLOW,
        )
        response = self.client.get(self.url, HTTP_X_API_KEY=skey._raw_key, REMOTE_ADDR="1.2.3.4")
        self.assertEqual(response.status_code, 200)
        response = self.client.get(self.url, HTTP_X_API_KEY=skey._raw_key, REMOTE_ADDR="5.6.7.8")
        self.assertEqual(response.status_code, 401)
