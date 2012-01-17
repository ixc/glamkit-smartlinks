import re

from django.utils.safestring import mark_safe
from django.template.context import Context

from smartlinks.models import IndexEntry

class Parser(object):
    """
    Abstract base class for smartlink-type functionality.
    """

    # To be overriden by subclasses.
    finder = None

    def __init__(self, smartlinks_conf):
        self.smartlinks_conf = smartlinks_conf

    def process_smartlinks(self, value):
        """
        :param value: Str or Unicode.
        :rtype: SafeString

        Replace the smartlinks with their values inside the text.
        """
        return mark_safe(self.finder.sub(self.parse, value))

    def get_smartlinked_object(self, value):
        """
        :param value: Str or Unicode.
        :rtype: Django model instance

        Get the object smartlinked to.

        :raises: same as :py:meth:`self._find_object`.
        """
        return self._find_object(self.finder.match(value))

    def parse(self, match):
        """
        :param match: Regexp match object.

        :returns:
        :rtype: SafeString
        """
        query = match.group("Query").strip()

        verbose_text = (match.groupdict().get('VerboseText',
                                             '') or query).strip()

        # Sets self.obj, self.conf and self.verbose_text or bails early.
        try:

            # Self.conf is also set by ``self._find_object``
            self.obj = self._find_object(match)
        except NoSmartLinkConfFoundException:

            if not self.smartlinks_conf:

                # No configurations => bail.
                raise

            return self.smartlinks_conf.values()[
                   0
            ].model_unresolved_template.render(Context({
                'smartlink_text': match.group(0),
                'verbose_text': verbose_text,
                'query': query
            }))

        except IndexEntry.DoesNotExist:
            return self.conf.unresolved_template.render(
                Context(dict(
                    verbose_text=verbose_text
                ))
            )

        except IndexEntry.MultipleObjectsReturned:
            return self.conf.ambiguous_template.render(
                Context(dict(
                    verbose_text=verbose_text
                ))
            )

        self.verbose_text = verbose_text

    def _find_object(self, match):
        """
        Find the object smartlinked to, sets ``self.conf``.

        :param match: Regexp match.
        :return: Found object corresponding to the smartlink.
        :rtype: Django model instance.
        :raises: IndexEntry.DoesNotExist, IndexEntry.MultipleObjectsReturned,
        NoSmartLinkConfFoundException
        """
        model = match.group("ModelName")
        query = match.group("Query").strip()

        # Empty configuration -> error.
        if not self.smartlinks_conf:
            raise NoSmartLinkConfFoundException()

        # If model is specified, let's try to find it.
        if model and not model in self.smartlinks_conf:
            # Model is specified, but it does not exist in configuration
            # -> error.

            # Show that the conf is not found.
            raise NoSmartLinkConfFoundException()

        if model:
            self.conf = self.smartlinks_conf[model]
            return self.conf.find_object(query)

        else:
            # Model is not specified, let's try to find it.
            # Note that because we are using OrderedDict all models
            # are tried in the specified order.

            seen = []
            for self.conf in self.smartlinks_conf.values():

                # Many configuration occur in .values()
                # multiple times.
                if self.conf in seen:
                    continue

                try:
                    return self.conf.find_object(query)
                except IndexEntry.DoesNotExist:
                    continue
                seen.append(self.conf)

        # If we have not returned yet, it means that the object does not exist.
        raise IndexEntry.DoesNotExist()

class SmartLinkParser(Parser):
    finder = re.compile(r"""
        (?<![\\])    # do NOT match smartlinks preceded by a slash
        \[\[
            \s*
            ((?P<ModelName>\w+)\s*\->)?    # Optional model name at the start
                                        # [[ Event->Mad Max ]]
                                        # vs [[ Movie->Mad Max ]]
            (?P<Query>[^\]\|]+)
            
            (\|(?P<VerboseText>[^\]]+))?
            \s*
        \]\]
    """, re.VERBOSE)


    def parse(self, match):
        ret = super(SmartLinkParser, self).parse(match)

        # Bail early if our parent tells us to.
        if ret: return ret
            
        context = dict(
            verbose_text=self.verbose_text,
            obj=self.obj,
        )

        return self.conf.template.render(Context(context))


class SmartEmbedParser(Parser):
    finder = re.compile(r"""
        (?<![\\])    # do NOT match smartlinks preceded by a slash
        \{\{
            \s*
            ((?P<ModelName>\w+)\s*\->)?  # Optional model name at the start
            (?P<Query>[^\]\|]+)
            \|\s*(?P<AttrName>\w+) # Attribute we are getting
                                 # from the object.
                                 # eg {{ Mad max | Image }}
                                 # or {{ Mad max | Video }}

            (?P<Options>         # Options passed to the attribute
              (\s*\|\s*

              ((\w+\s*=\s*\w+) | (\w+))
                                    # {{ Event->Siesta | Image | 300 | My image }}
                                    # Named options can be used as well
                                    # {{ Siesta | Image | size=300 |
                                    #    caption=My image }}
                                    # Combination of named and unnamed options
                                    # is also acceptable:
                                    # {{ Siesta | Image | size=300 | My image }}

              )+
            )?
            \s*
        \}\}
    """, re.VERBOSE)

    def parse(self, match):
        ret = super(SmartEmbedParser, self).parse(match)

        if ret: return ret

        attr = match.group("AttrName").strip()

        # Due to security reasons only the attributes specified in
        # 'embeddable_attributes' tuple can be accessed using the smartlink.
        if not attr in self.conf.embeddable_attributes:
            return self.conf.disallowed_embed_template.render(Context({
                'smartlink_text': match.group(0)
            }))

        options = match.group("Options")

        # Arguments for calling the required function.
        kwargs = {}
        args = []

        if options:
            # Additional options are passed for the method call.
            for option in options.strip("| ").split("|"):
                option = option.strip()
                if "=" in option:
                    key, value = option.split("=")
                    kwargs[key.strip()] = value.strip()
                else:
                    args.append(option)

        return getattr(self.obj, attr)(*args, **kwargs)

class NoSmartLinkConfFoundException(Exception):
    pass