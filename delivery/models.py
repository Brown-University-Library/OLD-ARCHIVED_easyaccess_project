import json, pprint, requests
from django.db import models
from django.contrib.auth.models import User
from jsonfield import JSONField
from datetime import datetime, timedelta

#logging
from django.conf import settings
from django.utils.log import dictConfig
import logging
dictConfig(settings.LOGGING)
alog = logging.getLogger('access')
#logging illiad.
ilog = logging.getLogger('illiad')

#===============================================================================
# User profiles.
#===============================================================================
class LibraryProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User)
    # Other fields here
    barcode = models.CharField(max_length=25, blank=True, null=True, default=None)
    is_faculty = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    #More granular status pulled from Shib headers
    membership = models.CharField(max_length=25, blank=True, null=True, default='unknown')
    #Store ILLiad registration date for initial registration and updating.
    illiad_registration_date = models.DateField(blank=True, null=True)
    #http://djangosnippets.org/snippets/1017/
    date_created = models.DateTimeField()
    date_modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if self.date_created == None:
            self.date_created = datetime.now()
        self.date_modified = datetime.now()
        super(LibraryProfile, self).save()

    def primary_affiliation(self):
        """
        Used for the Illiad registration piece.  Will attempt to populate
        with information from the membership field.  If not, will return
        the first valid affiliation.
        """
        if self.membership != 'unknown':
            return self.membership
        if self.is_faculty == True:
            return "Faculty"
        elif self.is_staff == True:
            return "Staff"
        elif self.is_student == True:
            return "Student"
        else:
            return "Unknown"

    def can_request_print(self):
        """
        Helper for determine if a user can request print document
        delivery for locally held items.
        """
        if self.is_faculty is True:
            return True
        if "medical" in self.membership.lower():
            return True
        #6/30/14 adding grad students per Bart.
        if "grad" in self.membership.lower():
            return True
        return False

    def illiad(self):
        d = {}
        d['username'] = self.user.username.replace('@brown.edu', '')
        d['first_name'] = self.user.first_name
        d['last_name'] = self.user.last_name
        d['email'] = self.user.email
        #Set status.
        d['status'] = self.primary_affiliation()
        return d

    def __unicode__(self):
        return "%s" % self.user.username

#===============================================================================
# Messages sent to users.
#===============================================================================
MESSAGE_TYPE_CHOICES = (
    ('blocked','blocked'),
    ('confirmation','confirmation'),
    ('incomplete', 'incomplete'),
)

helper = """
This will be the body of the message.  Confirmation emails will be followed by
the permanent link to the requested article.
"""

class UserMessage(models.Model):
    type = models.CharField(max_length=30, choices=MESSAGE_TYPE_CHOICES)
    subject = models.CharField(max_length=50, help_text="Email subject.")
    text = models.TextField(help_text=helper)

    date_created = models.DateTimeField(editable=False)
    date_modified = models.DateTimeField(editable=False)

    def save(self, *args, **kwargs):
        if self.date_created == None:
            self.date_created = datetime.now()
        self.date_modified = datetime.now()
        super(UserMessage, self).save()

    def __unicode__(self):
        return "%s" % (self.type)

#===============================================================================
# Supports permalinking.  Will also be created when a user requests an item.
#===============================================================================
class Resource(models.Model):
    query = models.TextField()
    referrer = models.CharField(max_length=200, blank=True, null=True)
    #http://djangosnippets.org/snippets/1017/
    date_created = models.DateTimeField()
    date_modified = models.DateTimeField()

    def save(self, *args, **kwargs):
        if self.date_created == None:
            #These are new objects
            self.date_created = datetime.now()
        self.date_modified = datetime.now()
        super(Resource, self).save()

    @models.permalink
    def get_absolute_url(self, request_view=False):
        from shorturls.baseconv import base62
        tiny = base62.from_decimal(self.id)
        if not request_view:
            return ('delivery:short', (),
                {'tiny': tiny})
        else:
            return ('delivery:request-short', (),
                    {'tiny': tiny})

    def __unicode__(self):
        return unicode(self.id)

#===============================================================================
# Holds request information.  Processes the request in the appropriate system -
# easyBorrow or easyArticle.
#===============================================================================
class Request(models.Model):
    item = models.ForeignKey(Resource)
    # user = models.ForeignKey(User, related_name='patron')
    user = models.OneToOneField(User, related_name='patron')  # <http://deathofagremmie.com/2014/05/24/retiring-get-profile-and-auth-profile-module/>
    bib = JSONField()
    #from bibjson
    type = models.CharField(max_length=25, blank=True, null=True)
    transaction_number = models.CharField(max_length=50, blank=True, null=True)
    #http://djangosnippets.org/snippets/1017/
    date_created = models.DateTimeField()
    date_modified = models.DateTimeField()

    def get_item(self, query, referrer):
        #Get the item if we have q query like this already, else make it.
        item = Resource.objects.filter(query=query,
                                       referrer=referrer)
        if item.exists():
            return item[0]
        else:
            item = Resource()
            item.query = query
            item.referrer = referrer
            item.save()
            return item

    def save(self, *args, **kwargs):
        #Handle the submission to the various services.
        #Create or get the related item.
        #import pdb; pdb.set_trace()
        if kwargs.get('submit') is True:
            self.item = self.get_item(self.bib.get('_query'),
                                      self.bib.get('_rfr'))
            #get the type
            bib_type = self.bib.get('type')
            #set the type
            self.type = bib_type
            #do easy borrow
            if bib_type == 'book':
                eb = prep_book_request(self)
                tn = eb.get('transaction_number')
                self.transaction_number = tn
            elif (bib_type == 'inbook') or (bib_type == 'article'):
                #submit to Illiad.
                ill = illiad_client(self, make_request=True)
                #Don't save failed Illiad requests.
                if ill.get('submitted') is not True:
                    #Email admins
                    _send_admin_message(self)
                    _send_message('incomplete', self)
                    #Dummy transaction number for now.
                    self.transaction_number = 'p%s' % self.item.id
            else:
                self.transaction_number = 'ea1345'

        #Do dates
        if self.date_created == None:
            self.date_created = datetime.now()
        self.date_modified = datetime.now()
        super(Request, self).save()

    def __unicode__(self):
        return "%s-%s" % (self.item, self.user)

#===============================================================================
# Manages josiah-availability.
# Checks availability & updates ezb db if necessary.
#===============================================================================
class JosiahAvailabilityManager(object):

    def __init__(self):
        self.available = False  # set by check_josiah_availability(); used by views.ResolveView.get()
        self.search_dict = {}  # set by check_josiah_availability(); used by update_ezb_availability()

    def check_josiah_availability( self, bibj ):
        """Checks josiah availability for books."""
        ## worth checking? (don't if not a book, or no good identifiers)
        worth_checking = False
        if bibj[u'type'] == u'book':
            search_dict = { u'isbn': u'', u'oclc': u'' }
            for entry in bibj[u'identifier']:
                if entry[u'type'] == u'isbn':
                    search_dict[u'isbn'] = entry[u'id']
                elif entry[u'type'] == u'oclc':
                    search_dict[u'oclc'] = entry[u'id']
            if search_dict[u'isbn'] or search_dict[u'oclc']:
                worth_checking = True
                self.search_dict = search_dict
        alog.debug( u'in JosAvManager.check_josiah_availability(); worth_checking: %s' % worth_checking )
        ## the check
        if worth_checking:
            url_base = u'http://library.brown.edu/services/availability'
            for key,value in search_dict.items():
                url = u'%s/%s/%s/' % ( url_base, key, value )
                alog.debug( u'in JosAvManager.check_josiah_availability(); url to try: %s' % url )
                availability_dict = { u'items': [] }
                try:
                    r = requests.get( url, timeout=5 )
                    availability_dict = json.loads( r.content.decode(u'utf-8', u'replace') )
                    alog.debug( u'in JosAvManager.check_josiah_availability(); availability_dict: %s' % pprint.pformat(availability_dict) )
                except Exception as e:
                    alog.error( u'in JosAvManager.check_josiah_availability(); exception: %s' % repr(e).decode(u'utf-8', u'replace') )
                for item in availability_dict[u'items']:
                    if item[u'is_available'] == True:
                        self.available = u'via_%s' % key.lower()
                        break
                if self.available:
                    break
        alog.debug( u'in JosAvManager.check_josiah_availability(); self.available: %s' % self.available )
        return

    def update_ezb_availability( self, bibj ):
        """Updates ezborrow requests table if item is available."""
        from django.core.cache import cache
        from easyborrow_models import EasyBorrowRequest
        assert self.available  # set in check_josiah_availability()
        alog.debug( u'in JosAvManager.update_ezb_availability(); self.search_dict: %s' % pprint.pformat(self.search_dict) )
        ## really update? (don't if a recent entry was added)
        do_update = False
        if cache.get( unicode(self.search_dict) ):  # key is unicode(dict); value doesn't matter
            alog.debug( u'in JosAvManager.update_ezb_availability(); cache found' )
            pass
        else:
            do_update = True
            cache.set( unicode(self.search_dict), u'last_set: %s' % datetime.now(), 60*60 )  # 1 hour; set value doesn't matter
            alog.debug( u'in JosAvManager.update_ezb_availability(); cache set with value, %s' % cache.get(unicode(self.search_dict)) )
        ## the update
        if do_update:
            try:
                req = EasyBorrowRequest(
                    created=datetime.now(),
                    title=bibj[u'title'],
                    isbn=self.search_dict[u'isbn'],
                    wc_accession=self.search_dict[u'oclc'],
                    request_status=u'in_josiah_%s' % self.available,
                    volumes=u'', sfxurl=u'', eppn=u'', name=u'', firstname=u'', lastname=u'', barcode=u'', email=u'' )
                req.save( using=u'ezborrow' )
                alog.debug( u'in JosAvManager.update_ezb_availability(); ezb db updated' )
            except Exception as e:
                alog.error( u'in JosAvManager.update_ezb_availability(); exception updating ezb table: %s' % repr(e).decode(u'utf-8', u'replace') )
        return

    # end class JosiahAvailabilityManager()


def prep_book_request(request):
    """
    Map the incoming bibjson object to the ezborrow request.
    """
    from easyborrow_models import EasyBorrowRequest
    from datetime import datetime
    bib = request.bib
    user = request.user
    #Helper to pull out first ID of a given type.
    def _first_id(id_type):
        try:
            return [id['id'] for id in bib.get('identifier', []) if id['type'] == id_type][0]
        except IndexError:
            return ''
            if id_type == 'isbn':
                return ''
            else:
                return None
    #import pdb; pdb.set_trace();
    #Register the user with illiad if necessary.
    registration = illiad_client(request)
    req = EasyBorrowRequest()
    req.created = datetime.now()
    req.title = bib.get('title')
    isbn = _first_id('isbn')
    if isbn is not None:
        req.isbn = isbn.replace('-', '').strip()
    try:
        oclc = int(_first_id('oclc'))
        req.wc_accession = oclc
    except (TypeError, ValueError):
        pass
    req.volumes = bib.get('_volume_note', '')
    #This sersol url is required at the moment for the controller code.
    req.sfxurl = 'http://%s.search.serialssolutions.com/?%s' % ( os.environ['EZACS__BUL_LINK_SERSOL_KEY'], bib.get('_query') )
    req.eppn = user.username.replace('@brown.edu', '')
    req.name = "%s %s" % (user.first_name, user.last_name)
    req.firstname = user.first_name
    req.lastname = user.last_name
    #Pull barcode from profile.
    profile = user.libraryprofile
    req.barcode = profile.barcode
    req.email = user.email
    #import pdb; pdb.set_trace();
    req.save(using='ezborrow')
    #This is a workaround to return the id of the object created above.
    #Since this is an existing database, I would prefer just to hit the db
    #again and get this users latest request id rather than try to alter the
    #schema to make it return an id.
    #This causes a second hit to the database to fetch the id of the item just requested.
    latest = EasyBorrowRequest.objects.using('ezborrow').filter(email=user.email).order_by('-created')[0]
    return {'transaction_number': latest.id}


def illiad_client(request, make_request=False):
    """
    Register the given user with Illiad if not registered already.
    Move this to the user profile at some point.
    """
    from illiad.account import IlliadSession
    from utils import make_illiad_url
    user = request.user
    profile = user.libraryprofile
    illiad_profile = profile.illiad()
    ill_username = illiad_profile['username']
    #dict to store output
    out = {}
    #Get an illiad instance
    illiad = IlliadSession(settings.FINDIT_ILLIAD_REMOTE_AUTH_URL,
                           settings.FINDIT_ILLIAD_REMOTE_AUTH_HEADER,
                           ill_username)
    illiad_session = illiad.login()
    ilog.info('User %s established Illiad session: %s.' % (ill_username,
                                                          illiad_session['session_id']))
    out['session'] = illiad_session

    #Exit if we can't authenticate the user.
    if not illiad_session['authenticated']:
        out['session_error'] = 'Failed login.'
        ilog.error("Illiad login failed for %s" % ill_username)
        illiad.logout()
        return out

    #Register users if neccessary.
    if not illiad.registered:
        ilog.info('Registering %s with Illiad as %s.' % (ill_username,
                                                         illiad_profile['status'])
                  )
        reg = illiad.register_user(illiad_profile)
        ilog.info('%s registration response: %s' % (ill_username, reg))
        out['was_registered'] = False
    else:
        ilog.debug('%s is already registered.' % (ill_username))
        out['was_registered'] = True
    #Handle the request if the kwargs exist.
    if make_request is True:
        query = make_illiad_url(request.bib)
        ilog.debug("Illiad url to submit is: %s" % query)
        illiad_post_key = illiad.get_request_key(query)
        ilog.info(illiad_post_key)
        #If blocked comes back in the post key, stop here with appropriate status.
        blocked = illiad_post_key.get('blocked', None)
        errors = illiad_post_key.get('errors', None)
        #for mocking errors
        #errors = True
        if blocked:
            out['blocked'] = blocked
            ilog.info("%s is blocked in Illiad." % ill_username)
            _send_message('blocked', request)
        elif errors:
            out['errors'] = True
            msg = illiad_post_key.get('message')
            ilog.info("Request errors during Illiad submission: %s %s" %\
                        (ill_username,
                         msg))
            out['message'] = msg
        else:
            submit_status = illiad.make_request(illiad_post_key)
            #Mock a request for testing.
#            submit_status = {
#                           'transaction_number': '1234',
#                           'submitted': True,
#                           'error': False,
#                           'message': None
#                           }
            out['submit_status'] = submit_status
            #Write the request to the requests table.
            if submit_status['submitted']:
                illiad_tn = submit_status['transaction_number']
                request.transaction_number = illiad_tn
                out['submitted'] = True
                _send_message('confirmation', request)
                ilog.info("%s request submitted for %s with transaction %s." %\
                        (ill_username,
                         request.id,
                         illiad_tn))
            else:
                ilog.error("%s request failed with message %s." %\
                           (ill_username,
                           submit_status['message']))
    illiad.logout()
    return out


def _send_message(message_type, request):
    from django.core.urlresolvers import reverse
    from django.core.mail import send_mail
    from django.contrib.sites.models import Site
    from app_settings import EMAIL_FROM
    addr = request.user.email
    message = UserMessage.objects.get(type=message_type)
    message_from = EMAIL_FROM
    request_link = 'http://%s%s' % (Site.objects.get_current().domain,
                                    request.item.get_absolute_url())
    if message_type == 'confirmation':
        msg = message.text.replace('{{ILLIAD_TN}}', request.transaction_number)
        body = "%s\n%s" % (msg,
                           request_link)
    elif message_type == 'blocked':
        body = "%s\n%s" % (message.text, request_link)
    elif message_type == 'incomplete':
        body = message.text.replace('{{QUERY}}', request.bib['_query'])
    else:
        body = message.text
    #sendit
    send_mail(message.subject,
              body,
              message_from,
              [addr],
              fail_silently=True)

def _send_admin_message(request):
    admin_email_addresses = [email for name, email in settings.ADMINS]
    from django.core.mail import send_mail
    from django.contrib.sites.models import Site
    request_link = 'http://%s%s' % (Site.objects.get_current().domain,
                                    request.item.get_absolute_url())
    btext = u''
    for k,v in request.bib.iteritems():
        btext += u"%s=>%s\n" % (k, v)
    body = "Request failed for request %s\n%s" % (request.item, btext)
    body += '\n\n%s' % request_link
    #sendit
    send_mail("easyAccess request failure",
              body,
              'easyAccess@library.brown.edu',
              admin_email_addresses,
              fail_silently=True)

