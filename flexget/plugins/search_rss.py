from __future__ import unicode_literals, division, absolute_import
import logging
import urllib

from flexget import plugin
from flexget.event import event
from flexget.task import Task
from flexget.utils.search import normalize_unicode

log = logging.getLogger('search_rss')


class SearchRSS(object):
    """A generic search plugin that can use rss based search feeds. Configure it like rss
    plugin, but include {{{search_term}}} in the url where the search term should go."""

    schema = {'$ref': '/schema/plugin/rss'}

    def search(self, task, entry, config=None):
        from flexget.utils.template import environment
        from flexget.manager import manager
        search_strings = [urllib.quote(normalize_unicode(s).encode('utf-8'))
                          for s in entry.get('search_strings', [entry['title']])]
        rss_plugin = plugin.get_plugin_by_name('rss')
        entries = set()
        rss_config = rss_plugin.instance.build_config(config)
        template = environment.from_string(rss_config['url'])
        rss_config['all_entries'] = True
        for search_string in search_strings:
            # Create a fake task to pass to the rss plugin input handler
            task = Task(manager, 'search_rss_task', config={})
            rss_config['url'] = template.render({'search_term': search_string})
            # TODO: capture some other_fields to try to find seed/peer/content_size numbers?
            try:
                results = rss_plugin.phase_handlers['input'](task, rss_config)
            except plugin.PluginError as e:
                log.error('Error attempting to get rss for %s: %s', rss_config['url'], e)
            else:
                entries.update(results)
        return entries


@event('plugin.register')
def register_plugin():
    plugin.register(SearchRSS, 'search_rss', groups=['search'], api_ver=2)
