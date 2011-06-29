from django.db import models

class Topic(models.Model):
    name = models.CharField(max_length=128)
    name_alt = models.CharField(max_length=128, blank=True)
    order = models.IntegerField(default=0)
    slug = models.CharField(max_length=80, unique=True)
    def __unicode__(self):
        return self.name

class Item(models.Model):
    question = models.TextField()
    answer = models.TextField()
    question_alt = models.TextField(blank=True)
    answer_alt = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    published = models.BooleanField(default=False)
    topic = models.ForeignKey(Topic)
    def __unicode__(self):
        return self.question
