.. smartlinks documentation master file, created by
   sphinx-quickstart on Mon Dec 12 15:57:25 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SMARTLINKS: Documentation
=========================

Smartlinks bring easy, but powerful wiki-style internal links to Django websites.

Smartlinks give content editors a way to make quick, easy links to other pages, which will
continue to work even if the target page moves, and will degrade gracefully if the target
page disappears. With smartlinks, it is even possible to create conditional links to content
that doesn’t yet exist, but may one day exist - when the target content is published,
the link automatically activates!

Use cases
---------


.. highlight:: html+django

Before diving into the configuration details here is a brief overview of what smartlinks library can
do for you.

  - Links to a Django model. ``[[ Mad Max ]]`` renders to::

    <a href="/movies/mad_max/" title="Mad Max: Beyond Thunderdome">Mad Max</a>

  - Furthermore, verbose text can be specified, as well as the custom model::

    [[ event->Mad Max | Fan convention ]]

  - Smartlinks can be used to get an image, or any other media from a model.

    ``{{ Mad Max | image }}`` will render to::

    <img src="/media/movies/mad_max.jpg" title="Mad Max: Beyond Thunderdome title image "/>

  - Options can be passed for the media we wish to get::

    {{ Mad Max | image | size=300 | align=north }}

    Will render to::

    <img src="/media/cache/300/200/mad_max.jpg" title="Mad Max: Beyond Thunderdome title image" />

  - Smartlinks can be also used to provide glossary lookups inside the text. For instance,

    ``{{ YMCA | glossary_definition }}`` can be rendered to::

    <abbr title="Young Men Christian Association">YMCA</a>


Installation and Configuration
------------------------------

Add ``smartlinks`` and ``django.contrib.contenttypes`` to
of ``INSTALLED_APPS`` in your settings.

Do ``./manage.py syncdb`` to initialize those.

.. highlight:: python

Create the initial configuration anywhere in the module which is guaranteed to be
imported::

  from smartlinks import register
  from smartlinks.index_conf import IndexConf

  from myapp.models import Movie, Event

  register(
    (('m', 'movie',), IndexConf(Movie.objects)),
    (('e', 'event',), IndexConf(Event.objects))
  )

If the legacy data is present in the smartlinked models,
the index should be refreshed using management command: ``./manage.py reset_smartlinks_index``.

.. highlight:: html+django

After that, smartlinks can be used in templates either using filter::

  {% load smartlinks %}
  {{ page.content|smartlinks }}

Or a templatetag ``filter`` (this one is convenient in your ``base.html``)::

  {% load smartlinks %}
  
  {% filter smartlinks %}
      {% block content %}{% endblock %}
  {% endfilter %}


which will substitute the references to smartlinks with a corresponding html code.

Go to the :ref:`configuration` section for more details.

Resolution mechanism
--------------------

:ref:`resolution`

Misc
====

* :ref:`search`

