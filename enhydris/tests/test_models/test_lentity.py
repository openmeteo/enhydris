from django.test import TestCase

from model_bakery import baker

from enhydris import models


class PersonTestCase(TestCase):
    def test_create(self):
        person = models.Person(last_name="Brown", first_name="Alice", initials="A.")
        person.save()
        self.assertEqual(models.Person.objects.first().last_name, "Brown")

    def test_update(self):
        baker.make(models.Person)
        person = models.Person.objects.first()
        person.first_name = "Bob"
        person.save()
        self.assertEqual(models.Person.objects.first().first_name, "Bob")

    def test_delete(self):
        baker.make(models.Person)
        person = models.Person.objects.first()
        person.delete()
        self.assertEqual(models.Person.objects.count(), 0)

    def test_str(self):
        person = baker.make(
            models.Person, last_name="Brown", first_name="Alice", initials="A."
        )
        self.assertEqual(str(person), "Brown A.")

    def test_ordering_string(self):
        baker.make(models.Person, last_name="Brown", first_name="Alice", initials="A.")
        person = models.Person.objects.first()
        self.assertEqual(person.ordering_string, "Brown Alice")


class OrganizationTestCase(TestCase):
    def test_create(self):
        organization = models.Organization(name="Crooks Intl", acronym="Crooks")
        organization.save()
        self.assertEqual(models.Organization.objects.first().name, "Crooks Intl")

    def test_update(self):
        baker.make(models.Organization)
        organization = models.Organization.objects.first()
        organization.acronym = "Crooks"
        organization.save()
        self.assertEqual(models.Organization.objects.first().acronym, "Crooks")

    def test_delete(self):
        baker.make(models.Organization)
        organization = models.Organization.objects.first()
        organization.delete()
        self.assertEqual(models.Organization.objects.count(), 0)

    def test_str(self):
        org = baker.make(models.Organization, name="Crooks Intl", acronym="Crooks")
        self.assertEqual(str(org), "Crooks")

    def test_ordering_string(self):
        baker.make(models.Organization, name="Crooks Intl", acronym="Crooks")
        organization = models.Organization.objects.first()
        self.assertEqual(organization.ordering_string, "Crooks Intl")
