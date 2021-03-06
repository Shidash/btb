from django.conf.urls.defaults import *

from correspondence.views import CorrespondenceList, Letters, Mailings, NeededLetters

letter_id = "(?P<letter_id>\d+)"
mailing_id = "(?P<mailing_id>\d+)"
user_id = "(?P<user_id>\d+)"


urlpatterns = patterns('correspondence.views',
    url(r'^correspondence.json(/{0})?$'.format(user_id), CorrespondenceList.as_view()),
    url(r'^letters.json(/{0})?'.format(letter_id), Letters.as_view()),
    url(r'^mailings.json(/{0})?'.format(mailing_id), Mailings.as_view()),
    url(r'^needed_letters.json', NeededLetters.as_view()),
    url(r'^mass_mailing_spreadsheet/(?P<who>.*)', 'mass_mailing_spreadsheet',
        name='correspondence.mass_mailing_spreadsheet'),
    url(r'^envelope/{0}?(/(?P<reverse>return))?$'.format(user_id), 'print_envelope', 
        name='correspondence.print_envelope'),
    url(r'^letter/{0}?$'.format(letter_id), 'show_letter', 
        name='correspondence.show_letter'),
    url(r'^comments/{0}$'.format(letter_id), 'recent_comments_letter', 
        name='correspondence.recent_comments_letter'),
    url(r'^preview_letter/$', 'preview_letter', 
        name='correspondence.preview_letter'),

    url(r'^collate_mailing/{0}?$'.format(mailing_id), 'get_mailing_file', 
        name='correspondence.collate_mailing'),
    url(r'^clear_cache/{0}?$'.format(mailing_id), 'clear_mailing_cache',
        name='correspondence.clear_mailing_cache'),
)
