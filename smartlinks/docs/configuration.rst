.. _configuration:

Configuration and registration
==============================

Registration
------------

.. highlight:: python

Smartlinks are registered using either :py:func:`register` or :py:func:`register_smart_link`.

.. automodule:: smartlinks
    :members:

Configuration
-------------

Smartlinks are configured using instances of :class:`SmartLinkConf`.
The recommended project setup is to define a subclass of :class:`SmartLinkConf`, and use it for
registration::

  class MyProjectSmartLinkConf(SmartLinkConf):
    template = "... my smartlink template ..."

  register_smart_link('o', MyProjectSmartLinkConf(MyObject.objects))

The quicker ad hoc way is to pass attributes to :class:`SmartLinkConf` which define it's behavior::

  register_smart_link('0', SmartLinkConf(MyObject.objects, template="..my smartlink template.."))


.. automodule:: smartlinks.index_conf
    :members:

