# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import template
register = template.Library()



def book(context):
    """
    Make a template tag for display citations on the various pages.
    """
    #Clean up print citations.
    #Take the first ISSN we can find,
#    try:
#        issn = citation.get('issn', {}).values()[0]
#    except (IndexError, AttributeError):
#        issn = citation.get('issn', '')
#    try:
#        del citation['issn']
#    except KeyError:
#        pass
#    citation['issn'] = issn
    return {'bib': context['bib']}
register.inclusion_tag('snippets/book.html', takes_context=True)(book)



def raw(parser, token):
    """
    http://www.holovaty.com/writing/django-two-phased-rendering/
    """
    # Whatever is between {% raw %} and {% endraw %} will be preserved as
    # raw, unrendered template code.
    text = []
    parse_until = 'endraw'
    tag_mapping = {
        template.TOKEN_TEXT: ('', ''),
        template.TOKEN_VAR: ('{{', '}}'),
        template.TOKEN_BLOCK: ('{%', '%}'),
        template.TOKEN_COMMENT: ('{#', '#}'),
    }
    # By the time this template tag is called, the template system has already
    # lexed the template into tokens. Here, we loop over the tokens until
    # {% endraw %} and parse them to TextNodes. We have to add the start and
    # end bits (e.g. "{{" for variables) because those have already been
    # stripped off in a previous part of the template-parsing process.
    while parser.tokens:
        token = parser.next_token()
        if token.token_type == template.TOKEN_BLOCK and token.contents == parse_until:
            return template.TextNode(u''.join(text))
        start, end = tag_mapping[token.token_type]
        text.append(u'%s%s%s' % (start, token.contents, end))
    parser.unclosed_block_tag(parse_until)
raw = register.tag(raw)


