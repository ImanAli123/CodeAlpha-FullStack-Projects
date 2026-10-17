
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Project


class ProjectTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="TestPassword123!"
        )

    def test_project_creation(self):
        project = Project.objects.create(
            name="Test Project",
            description="Testing project creation",
            creator=self.user
        )
        project.members.add(self.user)

        self.assertEqual(project.name, "Test Project")
        self.assertTrue(
            project.members.filter(pk=self.user.pk).exists()
        )
