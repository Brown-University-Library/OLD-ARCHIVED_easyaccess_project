# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging, pprint

from django import template
from django.template.base import TOKEN_TEXT, TOKEN_VAR, TOKEN_BLOCK, TOKEN_COMMENT, TextNode  # django 1.9


log = logging.getLogger('access')
register = template.Library()


## TODO: remove after tests are working on newer citation form
def citation_form(context, this_form):
    return {'this_form': this_form}


register.inclusion_tag(
    'snippets/citation_form.html',
    takes_context=True )(citation_form)


def citation_display(context, citation, format, direct_link):
    """
    Make a template tag for display citations on the various pages.
    """
    log.debug( 'citation_display context, ```%s```' % pprint.pformat(context) )
    log.debug( 'citation_display citation, ```%s```' % citation )
    log.debug( 'citation_display format, ```%s```' % format )

    ## Clean up print citations.
    ## Take the first ISSN we can find,
    try:
        issn = citation.get('issn', {}).values()[0]
    except (IndexError, AttributeError):
        issn = citation.get('issn', '')
    try:
        del citation['issn']
    except KeyError:
        pass
    citation['issn'] = issn
    return {'citation': citation,
            'format': format,
            'direct_link': direct_link}
def citation_display_josiah(context, citation, format, direct_link):
    """
    Make a template tag for display citations on the various pages.
    """
    log.debug( 'citation_display context, ```%s```' % pprint.pformat(context) )
    log.debug( 'citation_display citation, ```%s```' % citation )
    log.debug( 'citation_display format, ```%s```' % format )

    ## Clean up print citations.
    ## Take the first ISSN we can find,
    try:
        issn = citation.get('issn', {}).values()[0]
    except (IndexError, AttributeError):
        issn = citation.get('issn', '')
    try:
        del citation['issn']
    except KeyError:
        pass
    citation['issn'] = issn
    return {'citation': citation,
            'format': format,
            'direct_link': direct_link}

register.inclusion_tag(
    'snippets/citation_display.html',
    takes_context=True )(citation_display)
register.inclusion_tag(
    'snippets/citation_display_josiah.html',
    takes_context=True )(citation_display_josiah)


def request_link(context):
    return context


register.inclusion_tag(
    'snippets/request_link.html',
    takes_context=True)(request_link)


def raw(parser, token):
    """
    http://www.holovaty.com/writing/django-two-phased-rendering/
    """
    ## Whatever is between {% raw %} and {% endraw %} will be preserved as
    ## raw, unrendered template code.
    text = []
    parse_until = 'endraw'
    tag_mapping = {
        TOKEN_TEXT: ('', ''),
        TOKEN_VAR: ('{{', '}}'),
        TOKEN_BLOCK: ('{%', '%}'),
        TOKEN_COMMENT: ('{#', '#}'),
    }
    ## By the time this template tag is called, the template system has already
    ## lexed the template into tokens. Here, we loop over the tokens until
    ## {% endraw %} and parse them to TextNodes. We have to add the start and
    ## end bits (e.g. "{{" for variables) because those have already been
    ## stripped off in a previous part of the template-parsing process.
    while parser.tokens:
        token = parser.next_token()

        # if token.token_type == template.TOKEN_BLOCK and token.contents == parse_until:
        #     return template.TextNode(u''.join(text))

        if token.token_type == TOKEN_BLOCK and token.contents == parse_until:
            return TextNode(u''.join(text))

        start, end = tag_mapping[token.token_type]
        text.append(u'%s%s%s' % (start, token.contents, end))
    parser.unclosed_block_tag(parse_until)


raw = register.tag(raw)
