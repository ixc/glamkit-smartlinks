from django.db import models
from django.utils.safestring import SafeString

from smartlinks.fields import SmartLinkField

#: Test models for tests.

class PublicMoviesManager(models.Manager):
    def get_query_set(self):
        return super(PublicMoviesManager, self).get_query_set().filter(
            public=True
        )

class LinkModel(models.Model):
    link = SmartLinkField(max_length=200, blank=True)


class Movie(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)

    year = models.IntegerField(max_length=5)

    # We don't want to be able to smartlink to secret movies.
    public = models.BooleanField(default=True)

    objects = PublicMoviesManager()

    def __unicode__(self):
        return u"%s released in %s" % (self.title, self.year)

    def image(self):
        return SafeString(u"<img />")

    def get_absolute_url(self):
        return u"/movies/%s/" % self.slug

# .-notation test for smartlinks.
class Teacher(models.Model):
    position = models.CharField(max_length=100)
    person = models.OneToOneField('Person')

class Person(models.Model):
    name = models.CharField(max_length=100)

class Movie2(models.Model):
    """
    Movie object without custom queryset.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)

    year = models.IntegerField(max_length=5)

    def __unicode__(self):
        return u"%s released in %s" % (self.title, self.year)

    def image(self):
        return SafeString(u"<img />")

    def get_absolute_url(self):
        return u"/movies/%s/" % self.slug
