"""
Load a mirror database with Serial Solutions holdings for querying.
"""
import csv
import os
import sys
import tempfile

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils import simplejson
from optparse import make_option

from datetime import datetime

CURRENT_YEAR = datetime.now().year

class Command(BaseCommand):
    help = "For loading SerSol exports."
    option_list = BaseCommand.option_list + (
        make_option('--file', '-f', dest='export_file',
                    help='Specify file in SerSol holdings format.'),

    )
    
    def handle(self, **options):
        self.process(options['export_file'])
#        if (options['marc_file']) and (options['solr']):
#            self.process_solr(options['marc_file'])
#        elif options['marc_file']:
#            self.process(options['marc_file'])
#        else:
#          print>>sys.stderr, 'no file specified'

    def load_fixture(self, db_fixture):
        """
        Create temp file with fixture and use call_command to load 
        it into the db.   
        
        http://stackoverflow.com/questions/887627/programmatically-using-djangos-loaddata
        
        """
        #Write fixture to temporary file.
        f = open('phfix.json', 'wb')
        name = f.name
        out = simplejson.dumps(db_fixture)
        f.write(out)
        f.close()
        #Load fixture.
        call_command(
            'loaddata',
            name,
            verbosity=1,
            commit=True,
        )
        #Remove temp file.
        os.remove(name)

    def process(self, export_file):
        """
        Handle the file.
        
        Title (Required)        Type (Required) Default URL     Publisher       Publication Date (Book)    Public Note     Display Public Note     Location Note   Display Location Note      ISSN (Journal)  Coverage Date From (Journal)    Coverage Date To (Journal) ISBN (Book)     Author (Book)   Editor (Book)   Edition (Book)  Language IDAlphabetization
        Economic review /       Journal http://library.brown.edu/find/Search/Results?lookfor=0000-0027&type=ISN                            No      Rock    Yes     0000-0027 1975     1995

        """
        #Load the db with x items at a time.
        commit_freq = 1000
        sersol = csv.DictReader(open(export_file), delimiter='\t')
        #Map the CSV export fields to solr fields.  
        
        fixture = []
        for count, row in enumerate(sersol):
            issn = row.get('ISSN (Journal)')
            start = row.get('Coverage Date From (Journal)')
            end = row.get('Coverage Date To (Journal)')
            if end == '':
                #print>>sys.stderr, row
                end = CURRENT_YEAR
            location, call_number = row.get('Location Note').split(' - ')
            
            fixd = {}
            fixd['model'] = "findit.printtitle"
            fixd['pk'] = "%s%s" % (issn.replace('-', ''),
                                   start)
            fields = {}
            fields['issn'] = issn
            fields['start'] = int(start)
            fields['location'] = location
            fields['call_number'] = call_number[:49]
            try:
                fields['end'] = int(end)
            except ValueError:
                fields['end'] = None
            fixd['fields'] = fields
            #ToDo: add location and call number.  
            fixture.append(fixd)
            #print issn, start, end
            if count != 0:
                if count % commit_freq == 0:
                    self.load_fixture(fixture)
                    print>>sys.stderr, 'Committing set at %s.' % count
                    fixture = []
        
        #One last commit           
        print>>sys.stderr, "Committing final set."
        self.load_fixture(fixture)
            
        
        
        