
function lookupsFinished() {
    var available = isAvailable();
    var requested_item; //hold requested item.
    if (available == false) {
        if (isAuthenticated() == true) {
            requested_item = existingRequests();
            if (requested_item == false) {
                $('#request').show();
            } else {
                if (isConfirmationScreen() == false) {
                    $('#requestContainer').html($('#existingRequestTemplate').tmpl(requested_item));
                    $('#requestContainer').show();
                };
            };
        } else {
            $('#request').show();
        };
    };
    //don't show mulit-volume check box if this item isn't a book.
    if (window.bib.type != 'book') {
        $('#multi-volume').hide()
    };
};


function checkNotDirectLink() {
    var notDirect = []; //array to hold number of non-full text, but considered available links.
    notDirect = $("#onlineJournalsContainer li.not-direct");
    if ((notDirect) && (notDirect.length > 0)) {
        $('#not-direct-link-warning').show();
        return true;
    };
    return false;
}

function printJournalAvailability() {
    var print = [];  //aray to hold number of print holdins for articles.
    var profile; //object to hold user profile.
    var out = {}; //object indicating info about the print item.
    out['requestable'] = false;
    out['available'] = false;
    print = $("#bookHoldingsContainer tr.held-item");
    if ((print) && (print.length > 0)){
        out['available'] = true;
        profile = userProfile();
        if (profile['can_request_print'] == true) {
            out['requestable'] = true;
            //change the label of the button
            $('#request form input[type="submit"]').attr('value', "Request for delivery");
        };
    };
    return out;
};

function onlineJournalAvailability() {
    var direct = []; //array to hold number of direct links to text found.
    var notDirect = false; //boolean indicating if non-direct links are available.
    var out; //object to hold output
    notDirect = checkNotDirectLink();
    //direct length
    direct = $(".online-holdings li.direct");
    if ((direct) && (direct.length > 0)) {
        return true;
    } else if (notDirect == true) {
        return true;
    } else {
        return false;
    };
};

// check the call numbers to see if this is a multivolume work
// relies on string matching
function isMultiVolume() {
    var re = /^[A-Z].*\sv\..*/;
    var multi = _.filter($('#bookHoldingsContainer .callnumber'), function(item) {
        var cnum = $(item).text();
        if (cnum.match(re) != null) {
            return true;
        }
    });
    if (multi.length > 0) {
        return true;
    } else {
        return false;
    }
}

function isAvailable() {
    var direct = []; //array to hold number of direct links to text found.
    var print;  //object to hold number of print holdins for articles.
    var online; //object to hold online availability.
    if ( (bib.type == 'article') || (bib.type == 'inbook') ) {
        print = printJournalAvailability();
        online = onlineJournalAvailability();
        if (online == true) {
            return true;
        //direct length
        } else if ((print['available'] == true) && (print['requestable'] == false)){
            //this needs to be sensitive to the type of user logged in.
            return true;
        } else {
            return false;
        }
    } else {
        var localItems = $('.is-available');
        if (localItems.length > 0) {
            var notAvail = _.filter(localItems, function(item) {
                 return $(item).text() == 'false';
            });
            // return the request button if any attached local item is not available.
            if ((notAvail.length > 0) && (isMultiVolume() == true)) {
                return false;
            } else {
                return true;
            }
        }
        // If we are here, there are no local items.
        return false;
    };
};

//make sure we have enough metadata to process the request
//http://illiad.brown.edu/illiad/illiad.dll?Action=10&Form=29&other=bob&notes=worldcat&citedin=worldcat&citedvolume=bob
//line feed %0A
function validateArticleBib(){
    var valid; //boolean to hold value of whether this can be processed.
    valid = true;
    var attrs = ['title', 'journal', 'start_page', 'year']

    //articleUpdateTemplate
    if ((bib.hasOwnProperty('journal') == true) && (bib['journal'].hasOwnProperty('name') == true)) {
        //valid
    } else {
        bib['_needs_journal'] = true;
        bib['journal'] = {'name': null};
        valid = null;
        $('#journal-update-container').html($("#articleUpdateTemplate").tmpl(bib));
    };
    if (bib.hasOwnProperty('start_page') == false) {
        bib['start_page'] = null;
        valid = null;
    };
    //if (bib.hasOwnProperty('title') == false)
    $('#journal-update-container').html($("#articleUpdateTemplate").tmpl(bib));
    $("input[type='text']").change(function () {
        //alert('holler');
        attr = $(this).attr('name');
        val = $(this).val();
        if (attr == 'journal') {
            bib['journal'] = {'name': val};
        } else {
            bib[attr] = val;
        };
        //regenerate
        //validateArticleBib();
    });
    return valid;
}


function isAuthenticated() {
    if($('#authenticated').length > 0) {
        return true;
    } else {
        return false;
    }
}

function isConfirmationScreen() {
    var confirm; //boolean
    confirm = false;
    if ($('#request-confirmation').length > 0) {
        confirm = true;
    };
    return confirm
}

//fetch by OCLC
function fetchByOCLC() {
    try {
        var oclcs = _.filter(window.bib['identifier'], function(num){ return num.type == 'oclc'; });
        getLocalAvailability(oclcs[0].id, 'oclc');
    }
    catch (err) {
        return;
    }
    //get related oclcs
    //jsonFetch('http://xisbn.worldcat.org/webservices/xid/oclcnum/' + oclcs[0].id + '?method=getEditions&format=json&fl=oclcnum&callback=?',
    //    {},
    //    processRelatedOCLC);
};

//pull isbn from bib json
function fetchByISBN() {
    //isbns
    var isbns = _.filter(window.bib['identifier'], function(num){ return num.type == 'isbn'; });
    //first isbn only right now.
    try {
        var isbn = isbns[0].id;
        //try to get a match on the orig isbn;
        getLocalAvailability(isbn, 'isbn');
        getRelatedISBNs(isbn);
        return;
    }
    catch (err) {
        return;
    }
};

function getRelatedISBNs(isbn) {
    //return false;
    if (isbn != '') {
        jsonFetch('//library.brown.edu/easyborrow/xisbn/isbn/' + isbn + '/?callback=?', {}, processRelatedISBNs);
    };
};

function processRelatedISBNs(srv) {
        var alt = srv.response.filtered_alternates;
        //try to get local availability for each alternate isbn found with xisbn.
        _.each(alt, function(doc, count){
           _.each(doc.isbn, function(this_isbn) {
                    getRelatedLocalAvailability(doc.isbn, 'isbn', doc.ed, doc.year);
          });
        });
    };


function displayItemInfo(items) {
    _.each(items, function(thisItem){
         //Pull call number and location pairs from displayed items.
        var call = thisItem.callnumber;
        var seen = [];
        _.each($('#bookHoldingsContainer tr.held-item'), function(item) {
            var pt;
            pt = $(item).find('td.callnumber').text();
            seen.push(pt);
        });
        //Only add this location, callnumber pair if it's not already listed.
        if (jQuery.inArray(call, seen) == -1) {
            $('#bookHoldingsContainer').show();
            $('#bookHoldingsContainer table tbody').append($("#josiahHoldingsTemplate").tmpl(thisItem));
        };
    });
};

function processLocalHoldings(holdings) {
        var bib = holdings.id;
        if (holdings.items.length > 0) {
            //Filter items to only show those available.  This is not the same
            //as being 'available' in terms of allowing request via easyBorrow.
            //We might want to show that an item is located on campus - reserver, annex
            //but still allow it to be requested.
            //var avail = _.filter(holdings.items, function(item) {
            //    return jQuery.inArray($.trim(item.availability), available_text) > -1;
            //});
            var avail = holdings.items;
            //Don't show multiple detail links.  This is somewhat arbitrary
            //in what link will be shown.
            if ($('.detail-link').length < 1) {
                $('ul.citation').append('<li class="detail-link"><a href="http://library.brown.edu/find/Record/' + bib + '">View more details.');
            };
            //see if copies are available
            if (avail.length > 0 ) {
                displayItemInfo(avail);
                //call locator
                callBookLocator()
            } else {
                $('#holdings-debug').append(holdings.query.type + ':  ' + holdings.query.value + ' the library has this item but no copies are available at the library.<br/>')
            };
        } else {
            $('div#holdings-debug').append(holdings.query.type + ':  ' + holdings.query.value + ' not available at the library.<br/>');
        };
};


function processRelatedLocalHoldings(holdings) {
        if (holdings.items.length > 0) {
            //see if we have an available item
            var avail = _.filter(holdings.items, function(item) {
                return jQuery.inArray($.trim(item.availability), available_text) > -1;
            });
            //see if copies are available
            if (avail.length > 0 ) {
                //Go ahead and fetch related items.
                $('#relatedBookHoldingsContainer').show();
                $('#relatedBookHoldingsContainer table tbody').append($("#josiahHoldingsTemplate").tmpl(avail));
                //call locator
                callBookLocator()

            } else {
                $('#holdings-debug').append(holdings.query.type + ':  ' + holdings.query.value + ' the library has this item but no copies are available at the library.<br/>')
            };


        } else {
            $('div#holdings-debug').append(holdings.query.type + ':  ' + holdings.query.value + ' not available at the library.<br/>');
        };
};

//check Josiah availability
function getLocalAvailability(value, index) {
    //only send requests if we don't have an available copy yet.
    //if (isAvailable() != true) {
    jsonFetch('//library.brown.edu/services/availability/' + index + '/' + value + '/?callback=?', {}, processLocalHoldings);
    //};
};

function getRelatedLocalAvailability(value, index, edition, year) {
    //We want to get other editions even if we have found an available copy already.
    jsonFetch('//library.brown.edu/services/availability/' + index + '/' + value + '/?callback=?', {}, function(holdings){
        if (holdings.items.length > 0) {
            //see if we have an available item
            var avail = _.filter(holdings.items, function(item) {
                return jQuery.inArray($.trim(item.availability), available_text) > -1;
            });
            //see if copies are available
            if (avail.length > 0 ) {
                //Don't add more holdings if we've found an available copy already.
                //This prevents duplicates.
                //if (window.available == true) {
                //    return false;
                // }
                //window.available = true;
                //$('#bookHoldingsContainer').show();
                //add editons.
                var add_edition = _.each(avail, function(item){item.edition = year + ', ' + edition; return item;});
                var add_bib = _.each(avail, function(item){item.bib = holdings.id; return item;});
                $('#relatedBookHoldingsContainer').show();
                $('#relatedBookHoldingsContainer table tbody').append($("#relatedJosiahHoldingsTemplate").tmpl(avail));
                //call locator
                callBookLocator()

            } else {
                $('#holdings-debug').append(holdings.query.type + ':  ' + holdings.query.value + ' the library has this item but no copies are available at the library.<br/>')
            };


        } else {
            $('div#holdings-debug').append(holdings.query.type + ':  ' + holdings.query.value + ' not available at the library.<br/>');
        };

    });
};

//Get holdings from 360link.
function getElectronicHoldings() {
    var ourl = $('#openurl').text();
    jsonFetch(base_url + 'link360/?' + ourl + '&output=json', {},process360LinkHoldings);
};

function process360LinkHoldings(holdings) {
    //call merge to add any found metdata
    //mergeBibJSON(holdings['bibjson']);
    //check online
    if (holdings['links'] != null) {
        //do direct links
        if (holdings['links']['direct'] != null) {
            window.available = true;
            $('#onlineHoldingsContainer').show();
            $('#onlineHoldingsContainer').html($('#onlineWrapperTemplate').tmpl())
            $('#onlineHoldingsContainer ul.online-holdings').append($('#directOnlineTemplate').tmpl(holdings['links']['direct']));
        //do other links
        } else if (holdings['links']['other'] != null) {
            var access = _.filter(holdings['links']['other'], function(item) {
                return item;
            });
            if (access.length > 0) {
                $('#onlineJournalsContainer').show();
                if (bib.type == 'book') {
                    $('#onlineJournalsContainer').append($("#onlineBookTemplate").tmpl(access));
                } else {
                    $('#onlineJournalsContainer').append($("#onlineJournalsTemplate").tmpl(access));
                };
            };
        } else {
            if (window.debug) {
                $('div#holdings-debug').append('360Link returned no direct or fuzzy links.<br/>');
            };
        };
    };
    //do print - add (window.available == false) to hide print when online is available.
    if ((holdings['print']) && (holdings['print'].length > 0)) {
        //do the print.
        window.available = true;
        $('#bookHoldingsContainer').show();
        $('#bookHoldingsContainer table tbody').append($("#josiahHoldingsTemplate").tmpl(holdings['print']));
        callBookLocator();
    } else {
        if (window.debug) {
            $('div#holdings-debug').append('360Link returned no print holdings.<br/>');
        };
    }
};

function mergeBibJSON(newBib) {
  //should also post this to a service that will transform this bib object to a new openurl.
  //extend the existing bibjson object with the new one, then compact to remove
  var n = _.extend(window.bib, newBib);
  //re-render metadata if there isn't a title already - probably a PMID
  var title = $('.title').text().trim();
  if (title.length == 0){
    //massage the new bib for rendering.
    _.each(n.identifier, function(item){if (item.type == 'pmid'){n.pmid = item.id};});
    //fire a render of the metadata
    $('#easy-main ul').html($("#bibTemplate").tmpl(n));
  };
};


function processRelatedOCLC(srv) {
    var oclcs = _.flatten(_.pluck(srv.list, 'oclcnum'));
    //lookup each oclcnumber
    _.each(oclcs, function(o) {
                if (window.available != true) {
                    getRelatedLocalAvailability(o, 'oclc');
                };
            });
};


function callBookLocator() {
    _.each($('#bookHoldingsContainer tr.held-item'), function (n) {
                    var loc = $(".location", n).text();
                    var call = $(".callnumber", n).text();
                    var status = $(".status", n).text();
                    bookLocate(loc, call, status, $('.location', n));
                });
     //do related too
     _.each($('#relatedBookHoldingsContainer tr.held-item'), function (n) {
                    var loc = $(".location", n).text();
                    var call = $(".callnumber", n).text();
                    var status = $(".status", n).text();
                    bookLocate(loc, call, status, $('.location', n));
                });
};
function bookLocate(location, call_number, status, spot) {
       //locate the found journal
       var book_locator_url = '//library.brown.edu/services/book_locator/';
       var title = $.trim($('li.title').text());
       //Science library swith
       if (location == 'Sciences') {
         location = 'SCI';
       };
       //book locator wants lower case strings for locations.
       var location = location.toLowerCase();
       //logit('locating ' + call_number);
       var locate_request = {
           'callnumber': call_number,
           'location': location,
           'title': title,
           'status': status
       };
       var base_request_url = book_locator_url + '?' + $.param(locate_request);
       var json_url =  base_request_url + '&callback=?';
       var map_url = base_request_url + '&public=true';
       var location_label = location.toUpperCase();
       //call book locator
       var jqxhr = $.getJSON(json_url, function(bl){
               var bl = bl[location + '-' + call_number]
               if (bl['located'] == true) {
                   bl['map'] = map_url;
                   var out = {};
                   out['map'] = map_url;
                   out['location'] = location_label;
                   out['floor'] = bl['floor'];
                   out['aisle'] = bl['aisle'];
                   out['side'] = bl['side'];
                   //$(location_spot).append(locator_info);
                   $(spot).html($("#bookLocatorTemplate").tmpl(out));
               };
       });
};

function bindForm() {
    $("form#test-form").submit(function() {
            var qtype = $('#test-form select').val();
            var q = $("#test-form input:first").val();
            var base = window.location.origin + window.location.pathname;
            if (qtype == 'query') {
                var url = base + '?' + q;

            }
            else if (qtype == 'pmid') {
                var url = '?pmid=' + q;
            }
            else if (qtype == 'doi') {
                var url = '?doi=' + q;
            };
            window.location.href = url;
            return false;
            //var q = $("input:first").val();
            //var url = window.location.href + '?' + q;
            //window.location.href = url;
            //return false;
         });
};


$("#request form").submit(processRequest);

function processRequest() {
    //<input type="hidden" name="bib" value="{{ bib }}"/>
    if (isAuthenticated() != true) {
        window.location = $('#login-link').attr('href') + '&shibboleth=true';
    };
    $('#spinner').show();
    //var bib; //bibsjon
    //bib = window.bib;
    //Add the volume note to the bib.
    bib['_volume_note'] = $('#volume-note').val();
    bib = JSON.stringify(bib);
    $("#request form input[name='bib']").val(bib);
    return
};

//setup permalink creation.
$("#permalink a").click(function() {
  //alert("Handler for .click() called.");
  makePermalink('permalink');
});

function makePermalink(requestType) {
    var s = {
        'bib' : JSON.stringify(window.bib),
        'csrfmiddlewaretoken' : window.token,
        'url' : window.location.href
    };
    var perm = $.ajax({
        type : "POST",
        url : './permalink',
        data : s,
        dataType : "json",
        async : 'false',
        success : function(data) {
            if (window.debug == true) {
                $('#debug h5').after('<br/>' + JSON.stringify(data));
            };
            //pass on to permalink
            if (requestType == 'permalink') {
                return window.location = data.permalink;
            } else if (requestType == 'problem'){
                //Handle the report a problem links.
                if (window.bib.type != 'book') {
                    var prob = 'https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dEhXOXNEMnI0T0pHaTA3WFFCQkJ1ZHc6MQ'
                    //permalink will be a full path on dev/production.
                    prob = prob + '&entry_3=' + window.location.origin + data.permalink + '&entry_4=' + data.ip;
                } else {
                    var prob = 'https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dFhxbEV6SE0yX2lwOVp1WW92SlBRTWc6MQ&entry_2='
                    prob = prob + window.location.origin + data.permalink + '&entry_3=' + data.ip;
                };
                //Add email address if we can.
                if (data.email) {
                        if (bib['type'] == 'book') {
                            prob = prob + '&entry_1=' + data.email;
                        } else {
                            prob = prob + '&entry_2=' + data.email;
                        };
                };
                return window.location = prob;
            } else if (requestType == 'ris'){
                return window.location = data.permalink + '?export=ris'
            };
        },
        error : function(data) {
            //These are post failures which means server side error.
            $('#spinner').toggle();
            //$(".error").text("Couln't crete permalink.  Staff has been notified.").show();
        }
    });
    return permalink;
}

function easyRequest() {
    $('#spinner').show();
    //Add the volume note to the bib.
    window.bib['_volume_note'] = $('#volume-note').val();
    var s = {
        'bib' : JSON.stringify(window.bib),
        'csrfmiddlewaretoken' : window.token,
        'url' : window.location.href
    };
    $.ajax({
        type : "POST",
        url : base_url + 'request',
        data : s,
        dataType : "json",
        async : 'false',
        success : function(data) {
            if (window.debug == true) {
                $('#debug h5').after('<br/>' + JSON.stringify(data));

                if (window.bib.type == 'article') {
                   $('#debug h5').after('<br/><a href="' + data['illiad'] + '">Illiad url</a>.');
                };
            };
            $('#requestContainer').html($('#confirmationTemplate').tmpl(data));
            $('#multi-volume').hide();
        },
        error : function(data) {
            //These are post failures which means server side error.
            $('#spinner').toggle();
            $(".error").text("You're request could not be processed.  Library staff has been alerted.").show();
        }
    });
    return false;
};

//Begins the item location process.
function fetchResources() {
    fullText = []; //holder
    fullText = $('#full-text');
    //do we already have full text - could be we looked up the record.
    if ((fullText) && (fullText.length > 0)) {
      //no need to proceed.
      $('#spinner').hide();
    } else {
        if (bib.type == 'article') {
            //pass
        } else {
            fetchByISBN();
            fetchByOCLC();
        };
        getElectronicHoldings();
   };
};


function existingRequests() {
    var confirm; //holder for confirmation check.
    var query; //hold current query;
    var existing; //boolean for existing request status.
    var item; //to hold the requested item details.
    confirm = $('#request-confirmation');
    item = false;
    if (isAuthenticated() == true) {
        $.ajax({
              url: base_url + 'user-info/?' + bib['_query'],
              dataType: 'json',
              async: false,
              global: false,  //this turns off ajaxStart and ajaxStop, preventing an infinite loop
              success: function(data) {
                if (data.requested == true) {
                    item = data.requests[0];
                };
             }
        });
    };
    return item;
};


//setup permalink creation.
$(".report-problem").click(function() {
    //https://docs.google.com/a/brown.edu/spreadsheet/viewform?formkey=dEhXOXNEMnI0T0pHaTA3WFFCQkJ1ZHc6MQ&entry_3=http://library.brown.edu/easyarticle/get/eaZ/
    makePermalink('problem');
    return false;
});


//setup permalink creation.
$("#ris-export").click(function() {
   //call makePermalink to get the text of the permanent url
   //then redirect user to the RIS export view.
   makePermalink('ris');
});


function userProfile() {
    //Pull information about the user if we can.
    var out;
    out = {'can_request_print': false};  //this key is expected.
    if (isAuthenticated() == true) {
        $.ajax({
              url: base_url + 'user-info/',
              dataType: 'json',
              async: false,
              global: false,  //this turns off ajaxStart and ajaxStop, preventing an infinite loop
              success: function(data) {
                out = data;
             }
        });
    } else {
        //show the login prompt.
        var lp = $('#login-prompt')
        $(lp).show();
        $(lp).attr('class', 'alert-box');
    };
    return out;
};


