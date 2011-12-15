.. smartlinks documentation master file, created by
   sphinx-quickstart on Mon Dec 12 15:57:25 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SMARTLINKS: Documentation
=========================

.. toctree::
  configuration.rst
  resolution.rst
  

Smartlinks are an extension of wikilinks syntax for linking to arbitrary Django models
from the blob of text. When editing a blob of text, it is a nuisance to have to look up
URL of an other page, or URL of a particular image of a particular object in the database.
Furthermore, hardcoding such URLs will not be resistant to URL schema changes.

Smartlinks application provides a ``|smartlinks`` filter which finds smartlinks in the document
and replaces them with appropriate URLs.

Use cases
---------

Before diving into the configuration details here is a brief overview of what smartlinks library can
do for you.

  - Links to a Django model. `[[ Mad Max ]]` renders to::

    <a href="/movies/mad_max/" title="Mad Max: Beyond Thunderdome">Mad Max</a>

  - Furthermore, verbose text can be specified, as well as the custom model::

    [[ event->Mad Max | Fan convention ]]

  - Smartlinks can be used to get an image, or any other media from a model.
  ``{{ Mad Max | image }}`` will render to::

    <img src="/media/movies/mad_max.jpg" title="Mad Max: Beyond Thunderdome title image "/>

  - Options can be passed for the media we wish to get::

    {{ Mad Max | image | size=300 | align=north }}

  will render to::

    <img src="/media/cache/300/200/mad_max.jpg" title="Mad Max: Beyond Thunderdome title image" />

  - Smartlinks can be also used to provide glossary lookups inside the text. For instance,
  ``{{ YMCA | glossary_definition }}`` can be rendered to::

    <abbr title="Young Men Christian Association">YMCA</a>


Installation and Configuration
------------------------------

Just add ``smartlinks`` to a list of ``INSTALLED_APPS`` in your ``settings.py``.

After initial configuration .. code-block:: html+django

  from smartlinks import register
  from smartlinks.index_conf import IndexConf

  from myapp.models import Movie, Event

  register(
    (('m', 'movie',), IndexConf(Movie.objects)),
    (('e', 'event',), IndexConf(Event.objects))
  )

Then you'll need to create the index: ``./manage.py reset_smartlinks_index``.

After that, smartlinks can be used in templates::

  {% load smartlinks %}
  {{ page.content|smartlinks }}

which will substitute the references to smartlinks with a corresponding html code.

Go to the `Configuration`_ section for more details.

Resolution mechanism
--------------------

`Resolution`_

Misc
====

* :ref:`search`

