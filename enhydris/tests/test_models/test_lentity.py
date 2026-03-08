from django.test import TestCase

from model_bakery import baker

from enhydris import models


class PersonTestCase(TestCase):
    def test_create(self):
        person = models.Person(last_name="Brown", first_name="Alice", initials="A.")
        person.save()
        self.assertEqual(models.Person.objects.get().last_name, "Brown")

    def test_update(self):
        baker.make(models.Person)
        person = models.Person.objects.get()
        person.first_name = "Bob"
        person.save()
        self.assertEqual(models.Person.objects.get().first_name, "Bob")

    def test_delete(self):
        baker.make(models.Person)
        person = models.Person.objects.get()
        person.delete()
        self.assertEqual(models.Person.objects.count(), 0)

    def test_str(self):
        person = baker.make(
            models.Person, last_name="Brown", first_name="Alice", initials="A."
        )
        self.assertEqual(str(person), "Brown A.")

    def test_ordering_string(self):
        baker.make(models.Person, last_name="Brown", first_name="Alice", initials="A.")
        person = models.Person.objects.get()
        self.assertEqual(person.ordering_string, "Brown Alice")


class OrganizationTestCase(TestCase):
    def test_create(self):
        organization = models.Organization(name="Crooks Intl", acronym="Crooks")
        organization.save()
        self.assertEqual(models.Organization.objects.get().name, "Crooks Intl")

    def test_update(self):
        baker.make(models.Organization)
        organization = models.Organization.objects.get()
        organization.acronym = "Crooks"
        organization.save()
        self.assertEqual(models.Organization.objects.get().acronym, "Crooks")

    def test_delete(self):
        baker.make(models.Organization)
        organization = models.Organization.objects.get()
        organization.delete()
        self.assertEqual(models.Organization.objects.count(), 0)

    def test_str(self):
        org = baker.make(models.Organization, name="Crooks Intl", acronym="Crooks")
        self.assertEqual(str(org), "Crooks")

    def test_ordering_string(self):
        baker.make(models.Organization, name="Crooks Intl", acronym="Crooks")
        organization = models.Organization.objects.get()
        self.assertEqual(organization.ordering_string, "Crooks Intl")
