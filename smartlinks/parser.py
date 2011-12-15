import re

from django.utils.safestring import mark_safe
from django.template.context import Context

from smartlinks.models import IndexEntry
from smartlinks.index_conf import IndexConf

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
        Replace the smartlinks with their values inside the text.
        """
        return mark_safe(self.finder.sub(self.parse, value))

    def parse(self, match):
        """
        :param match: Regexp match object.

        :returns:
        :rtype: SafeString
        """
        model = match.group("ModelName")
        query = match.group("Query").strip()

        verbose_text = (match.groupdict().get('VerboseText',
                None) or match.group('Query')).strip()

        # Sets self.object and self.template, or bails early.

        # If model is specified, let's try to find it.
        if model and not model in self.smartlinks_conf:
            # Model is specified, but it does not exist in configuration
            # -> error.

            # Just pick the template from the first configuration,
            # ``model_unresolved_template`` should be the same in all
            # configurations anyway.
            return self.smartlinks_conf.values()[
                   0
                ].model_unresolved_template.render(Context({
                    'smartlink_text': match.group(0),
                    'verbose_text': verbose_text,
                    'query': query
                }))

        try:
            if model:
                conf = self.smartlinks_conf[model]
                obj = conf.find_object(query)

            else:
                # Model is not specified, let's try to find it.
                # Note that because we are using OrderedDict all models
                # are tried in the specified order.

                seen = []
                for conf in self.smartlinks_conf.values():

                    # Many configuration occur in .values()
                    # multiple times.
                    if conf in seen:
                        continue

                    try:
                        obj = conf.find_object(query)
                        break
                    except IndexEntry.DoesNotExist:
                        continue
                    seen.append(conf)
                else:
                    return IndexConf.model_unresolved_template.render(
                        Context(dict(
                            verbose_text=verbose_text
                        ))
                    )

            template = conf.template

        except IndexEntry.DoesNotExist:
            return conf.unresolved_template.render(
                Context(dict(
                    verbose_text=verbose_text
                ))
            )

        except IndexEntry.MultipleObjectsReturned:
            return conf.ambiguous_template.render(
                Context(dict(
                    verbose_text=verbose_text
                ))
            )

        self.conf = conf
        self.obj = obj
        self.template = template
        self.verbose_text = verbose_text


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

        return self.template.render(Context(context))


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