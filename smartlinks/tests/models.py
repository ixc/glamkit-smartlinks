from django.db import models

# Test models for tests.
from django.utils.safestring import SafeString

from smartlinks.fields import SmartLinkField

class PublicMoviesManager(models.Manager):
    def get_query_set(self):
        return super(PublicMoviesManager, self).get_query_set().filter(
            public=True
        )

# Now, the only remaining problem, really, is to make this model
# work inside the tests
class Movie(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)

    year = models.IntegerField(max_length=5)

    # We don't want to be able to smartlink to secret movies.
    public = models.BooleanField(default=True)

    objects = PublicMoviesManager()

    def __unicode__(self):
        return "%s released in %s" % (self.title, self.year)

    def image(self):
        return SafeString("<img />")