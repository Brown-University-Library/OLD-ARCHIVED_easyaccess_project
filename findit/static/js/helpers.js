console.log( "starting findit/static/js/helpers.js" );

/* TODO */
// var foo_a = window.location.hostname;
// var foo_b = "//" + foo_a + "/services/book_locator/";
// console.log( "in function locate(); book_locator_url, " + foo_b );

//Will display log messages to console if set to true.
//In IE log messages will be appended to body.
//var debug = true;
//var logging = true;
var e_only = true;
//Number of rss feeds to show for each publication.
var num_feeds = 5;
//how long to show the login prompt
var login_alert_length = 8000;
_has_abstract = false;
_base_url = null;


//global to store open url request or process the embedded coin.
var get_request = function() {
    var r = window.location.search;
    if (r != '') {
        return r;
    }
    else {
        var coin = $('#coin span').attr('title');
        return '?' + coin;
    }
};

function jsonFetch(url, data, callback) {
    $.ajax({
      url: url,
      dataType: 'json',
      data: data,
      success: callback
    });
};

function getExtras() {
    var doi = $('#doi').text();
    var pmid = $('#pmid').text();
    fetchMAS();
    return;
    //fetchJSTOR();
    //if (pmid != "") {
    //    fetchMendeleyByPMID(pmid);
    //};
    //if (doi != "") {
    //    fetchMendeleyByDOI(doi);
    //};
}


function setupTemplates() {
    //http://encosia.com/jquery-templates-composite-rendering-and-remote-loading/
    // Asynchronously load the template definition file.
    var path = window.base_url + 'static/js/_templates.html';
    $.get(path, function(templates) {
      // Inject all those templates at the end of the document.
      $('body').append(templates);
    });
};


//Get holdings from 360link.
function getHoldings() {
    $('#spinner').show();
    var ourl = $('#openurl').text();
    jsonFetch(_base_url + '?' + ourl + '&output=json', {},processHoldings);
}

function processHoldings(held) {
    $('#spinner').hide();
    //var title = $('li.title')
    //var link = $('<a/>');
    //link.attr('href', held.direct_link.link);
    //link.text($(title).text());
    //link.wrap('li').attr('class', 'title');
    //$(title).replaceWith(link);
    $('#holdingsContainer').show();
    if (held['direct_link'] != null) {
        $('#holdingsContainer').html($("#holdingsTemplate").tmpl(held.direct_link));
    } else if (held['online'].length > 0) {
        $('#holdingsContainer').html($('#nonDirectHoldingsTemplate').tmpl(held));
        $('#not-direct-link').show();
    } else if (held['print'].length > 0) {
        //$('#holdingsContainer').html($('#printHoldingsTemplate').tmpl(held));
        //
    };
}

function getBookLocation() {
        /* Still triggered, but no longer calls locate(), below. */

        console.log( "in findit/static/js/helpers.js getBookLocation()" );
        var pholdings = $('ul.print-holdings li span.loc-callnum');
        $.each(pholdings, function(i,item){
                var loc = $(item).find('span.print-location').text();
                var cn = $(item).find('span.print-callnumber').text();

                // locate(loc, cn, item);

        });
}


function locate(location, call_number, spot) {
       /* Was called by getBookLocation(), above, but no longer.
          Book-locator url supplied by template `findit/templates/findit/resolve.html`. */

       console.log( "in findit/static/js/helpers.js locate()" );
       console.log( "call_number, " + call_number );

       //locate the found journal
       var book_locator_url = '//library.brown.edu/services/book_locator/';
       var title = $('.source').text();
       var status = '';
       //book locator wants lower case strings for locations.
       var location = location.toLowerCase();
       console.log( "location initially, " + location );

       //shorten sciences.
       if (location == 'sciences') {
           location = 'sci';
       }
       console.log( "location finally, " + location );

       //logit('locating ' + call_number);
       var locate_request = {
           'callnumber': call_number,
           'location': location,
           'title': title,
           'status': status
       };
       console.log( "locate_request, " + JSON.stringify(locate_request) )

       var base_request_url = book_locator_url + '?' + $.param(locate_request);
       var json_url =  base_request_url + '&callback=?';
       console.log( "json_url, " + json_url );

       var map_url = base_request_url + '&public=true';
       console.log( "map_url, " + map_url );

       var location_spot = spot;
       console.log( "location_spot, " + location_spot.innerHTML );

       var location_label = location.toUpperCase();
      console.log( "location_label, " + location_label );

       i = 0;

       //logit(oclc_number);
       var jqxhr = $.getJSON(json_url, function(bl){
               var bl = bl[location + '-' + call_number]
               if (bl['located'] == true) {
                   var locator_info = "{4} -- {3} -- Level {0}, Aisle {1}{2}".format(
                                                            bl['floor'],
                                                            bl['aisle'],
                                                            bl['side'],
                                                            location_label,
                                                            call_number
                                                            );
                   //$(location_spot).append(locator_info);
                   var locate_link = '<a class="book_locator_map iframe" href="{1}">view map</a>'.format(call_number, map_url, location);
                   var locate_link = locator_info + locate_link;
                   $(location_spot).html(locate_link);
                   $("a.book_locator_map").fancybox({'width':750,'height': 600});
                   i = i +1;
               }
       })
};


function fetchMAS() {
    var ourl = $('#openurl').text();
    jsonFetch(_base_url + 'mas/?' + ourl,{}, processMAS);
}

function processMAS(mas){
    //get extra urls
    var results = mas.response.Publication.Result;
    if (results.length > 0) {
        var pub1 = results[0];
        //masUrls(pub1);
        var ab = pub1.Abstract;
        if ((_has_abstract == false) && (ab != null)) {
            //check for null string
            if (ab == '') {
                return false;
            };
            var d = {
                'header': 'Abstract',
                'abstract': ab + '...',
                'mas_url': 'http://academic.research.microsoft.com/Publication/' + pub1.ID
            }
            $('#abstractContainer').html($("#abstractTemplate").tmpl(d));
            _has_abstract = true;
        };
        var extras = makeMASExtras(pub1)
        //masUrls(pub1);
        $('#masExtrasContainer').html($("#masExtrasTemplate").tmpl(extras));
    }
};

function fetchJSTOR() {
    var ourl = $('#openurl').text();
    jsonFetch(_base_url + 'jstor/?' + ourl,{}, processJSTOR);
};

function processJSTOR(jstor){
    var results = jstor.results;
    if (results.length > 0) {
        var pub1 = results[0];
        var ab = pub1['abstract'];
        if ((_has_abstract == false) && (ab != null)) {
            var d = {
                'header': 'Abstract',
                'abstract': ab + '...',
                'jstor_url': pub1.stable
            }
            $('#abstractContainer').html($("#abstractTemplate").tmpl(d));
            _has_abstract = true;
        };
        var extras = makeJSTORExtras(pub1)
        $('#extrasContainer').html($("#jstorExtrasTemplate").tmpl(extras));
    };
};

function fetchMendeleyByDOI(value) {
    jsonFetch(_base_url + 'mendeley/',
            {'doi': encodeURIComponent(value)},
            processMendeley);
};
function fetchMendeleyByPMID(value) {
    jsonFetch(_base_url + 'mendeley/pmid/' + value,
            {},
            processMendeley);
};

//support for pulling in more urls from mas
//not implmemented at the moment.
function masUrls(pub) {
    //logit(pub);
    $.each(pub.FullVersionURL, function(i,url){
        var p = purl(url);
        var host = p.attr('host');
        if (host == 'arxiv.org') {
            var t = $('.citation li.title');
            $(t).wrap('<a href="' + url + '"></a>');
            $('#request-message').hide();
            //stop now
            return false;
        };
    });
};



function makeMASExtras(pub) {
    var o = Object(
                    {
                        'link': Array(
                            {
                                'label': 'View this item',
                                'url': 'http://academic.research.microsoft.com/Publication/' + pub.ID
                            },
                            {
                                'label': 'Items by ' + pub.Author[0].FirstName + ' ' + pub.Author[0].MiddleName + ' ' + pub.Author[0].LastName,
                                'url': 'http://academic.research.microsoft.com/Author/' + pub.Author[0].ID
                            }
                          )
                    }
    );

     if (pub.ReferenceCount > 0) {
        o['link'].push(
            {
            'label': pub.ReferenceCount + ' items cited by this article.',
            'url': 'http://academic.research.microsoft.com/Detail?entitytype=1&searchtype=2&id=' + pub.ID
            }
        );
     };
     if (pub.CitationCount > 0) {
        o['link'].push(
            {
            'label': pub.CitationCount + ' items that cite this item',
            'url': 'http://academic.research.microsoft.com/Detail?entitytype=1&searchtype=5&id=' + pub.ID
            }
        );
     };
  return o;
}


function processMendeley(mend) {
    if ((_has_abstract == false) && (mend['abstract'] != 0)) {
        mend.header = "Abstract";
        mend.base_url = _base_url;
        $('#abstractContainer').html($("#abstractTemplate").tmpl(mend));
        _has_abstract = true;
    };
    //If we have a mendeley document, do some stuff with it.
    if (mend['error'] == null){
            jsonFetch(_base_url + 'mendeley/related/' + mend.uuid,{},processMendeleyRelated);
            var extras = makeMendeleyExtras(mend)
            $('#mendeleyExtrasContainer').html($("#mendeleyExtrasTemplate").tmpl(extras));
    };
};


//pull some stuff from the mendeley response.
function makeMendeleyExtras(mend) {
    var o = Object(
                    {
                        'link': Array(
                            {
                                'label': 'Overview',
                                'url': mend.mendeley_url
                            },
                            {
                                //http://api.mendeley.com/research-papers/?rec=phylogeny-divergence-time-island-tiger-beetles-genus-cylindera-coleoptera-cicindelidae-east-asia
                                //http://api.mendeley.com/research/phylogeny-divergence-time-island-tiger-beetles-genus-cylindera-coleoptera-cicindelidae-east-asia/
                                'label': 'Related Research',
                                'url': mend.mendeley_url.replace('com/research/',
                                                                 'com/research-papers/?rec=')
                            }
                          )
                    }
    );
  return o;
}


//pull some stuff from the jstor response.

function makeJSTORExtras(jstor) {
    var o = Object({
        'link' : Array({
            'label': 'PDF',
            'url': jstor.pdf
        },{
            'label' : 'Overview',
            'url' : jstor.stable
        }, {
            //http://www.jstor.org/stable/info/2781822?seq=1&type=ref#infoRef
            'label' : 'References',
            'url' : jstor.references
        }, {
            //http://www.jstor.org/stable/info/2781822?seq=1&type=cite#infoCiting
            'label' : 'Items citing this item',
            'url' : jstor.citations
        })
    });
    return o;
}



function processMendeleyRelated(mend) {
        //max related documents to show from Mendeley.
        //they seem to be ranked in order of relevence;
        //2/29/12
        //returning false now since it's providing bogus results at the moment.
        return false;
        var max_related = 3;
        related_research = Object();
        related_research.articles = Array();
        if (mend.documents) {
            $.each(mend.documents, function(d, doc){
                //Only rendering related research with DOIs becase
                //that is all we can reliably resolve.
                if (doc.doi) {
                    //        doc.open_url = base_url + '?id=' + encodeURIComponent(doc.doi);
                    //        related_research.articles.push(doc);
                    //}
                    //logit(doc.uuid + ' - ' + doc.doi + ' - ' + doc.oa_journal);
                    //if (doc.oa_journal == true) {
                    var ou = {
                        'rft.atitle': doc.title,
                        'rft.jtitle': doc.publication_outlet,
                        'rft.date': doc.year,
                        'mend.uuid': doc.uuid
                    };
                    if (doc.doi) {
                        ou['rft_id'] = 'info:doi/' + doc.doi
                    }
                    //ou = base_url + '?rft.atitle' + doc.title;
                    //ou = ou + '&rft.jtitle' + doc.publication_outlet;
                    //ou = ou + '&rft.date' + doc.year;
                    doc.open_url = '?' + $.param(ou)
                    //get document metadata.
                    //doc.open_url = base_url + '?' + fetch_mend_document(doc.uuid);
                    related_research.articles.push(doc);
                    if (d == max_related) {
                        return false;
                    }
                };
           });
        };
        //only render if we found some related research
        if ((related_research.articles != null) && (related_research.articles.length > 0)) {
                related_research.header = "Related Research";
                $('#relatedResearchContainer').html($("#relatedResearchTemplate").tmpl(related_research));
        };
};



//add a few globals
function setupWindow() {
    console.log( "in findit/static/js/helpers.js setupWindow()" );
    var home_path = $('#home-link').text();
    window.base_url = home_path;
    _base_url = home_path;
    var debug_mode = $('#debug').text();
       window.logging = false;
    if (debug_mode == 'true') {
        window.logging = true;
    };
    //see if there is an abastract
    var ab = $('#abstract').text();
    if (ab.length > 0) {
        _has_abstract = true;
    }
};

function requestResource(path) {
    //$('body').append('<span class="spinner"<img src="http://library.brown.edu/find/interface/themes/brown/images/ajax_loading.gif"/></span>');
    //hide the state error if it's three.
    //Bind a click event to handle the request form.
    $("#btnRequest").bind("click", function() {
            $('#spinner').toggle();
           //serialze the form for posting.
           var s = $('#login form').serialize();
           $('#request p').hide();
           $('.info').hide();
           $('#btnRequest').hide();
            var s = $('#request form').serialize();
            //post the values
            $.ajax({
            type: "POST",
                url: path,
                data: s,
                dataType: "json",
                success: function(data) {

                    if (data.session.authenticated == true) {
                      //console.debug(data);
                      var sid = data.session.id;
                      //Handle authentication passes but something fails
                      //on submission.  These should probably just be
                      //passed on to staff for debugging because there
                      //is nothing more the user can do.
                      //See if patron is blocked.
                      if (data.blocked == true) {
                          $('#spinner').hide();
                          $("p.error").text("Your Interlibrary Loan account has been blocked.  You will receive an email with directions for resolving this.").show();
                      }
                      else if (data.submit_status.submitted != true) {
                          //something went wrong
                          message = data.submit_status.message
                          $('#spinner').hide();
                           $(".error").text("Your request could not be processed.  " + message).show();
                      }
                      else {
                          //these are the winners
                          var tracking = data.submit_status.transaction_number;
                          //$(".success").text("Your request has been submitted.  The tracking number is " + tracking + ".").show();
                          $(".success").text("Your request has been submitted. You will receive an email when it has been processed.").show();
                          $("form").hide();
                          $('#spinner').toggle();
                          //hide request box in parent window
                          var pd = parent.document;
                          $(pd).find('#request-message').hide();
                      };
                    }
                },
                error: function(data){
                  //These are post failures which means server side error.
                  $('#spinner').toggle();
                  console.log( "- `findit/static/js/helpers.js` error detected" );
                  $(".error").text("Server side.  Your request could not be processed.  Library staff has been alerted.").show();
                }

            })
        // return false to cancel normal form submit event methods.
        return false;
    });
};



//utility for GET variables
$.extend({
      getUrlVars: function(){
        var vars = [], hash;
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
        for(var i = 0; i < hashes.length; i++)
        {
          hash = hashes[i].split('=');
          vars.push(hash[0]);
          vars[hash[0]] = hash[1];
        }
        return vars;
      },
      getUrlVar: function(name){
        return $.getUrlVars()[name];
      }
});


//utilities
function logit(msg) {
    if (window.logging == true) {
        try
          {
          //Run some code here
            console.debug(msg);
          }
        catch(err)
          {
          //In IE append logging messages to body
            $('body').append(msg + '<br/>');
          }
    }
    else {
        return
    };
};

//String formatter
//per: http://snipplr.com/view.php?codeview&id=8984
String.prototype.format = function(){
  var pattern = /\{\d+\}/g;
  var args = arguments;
  return this.replace(pattern, function(capture){ return args[capture.match(/\d+/)]; });
}

//Cookie Controls
//per: http://www.quirksmode.org/js/cookies.html
function createCookie(name,value,days) {
    if (days) {
        var date = new Date();
        date.setTime(date.getTime()+(days*24*60*60*1000));
        var expires = "; expires="+date.toGMTString();
    }
    else var expires = "";
    document.cookie = name+"="+value+expires+"; path=/";
}

function readCookie(name) {
    var nameEQ = name + "=";
    var ca = document.cookie.split(';');
    for(var i=0;i < ca.length;i++) {
        var c = ca[i];
        while (c.charAt(0)==' ') c = c.substring(1,c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);
    }
    return null;
}

function eraseCookie(name) {
    createCookie(name,"",-1);
}

// jQuery URL Parser plugin (No jQuery version!) - https://github.com/allmarkedup/jQuery-URL-Parser/tree/no-jquery
// Written by Mark Perkins, mark@allmarkedup.com
// License: http://unlicense.org/ (i.e. do what you want with it!)

var purl = (function(undefined) {

    var tag2attr = {
        a       : 'href',
        img     : 'src',
        form    : 'action',
        base    : 'href',
        script  : 'src',
        iframe  : 'src',
        link    : 'href'
    },

    key = ["source","protocol","authority","userInfo","user","password","host","port","relative","path","directory","file","query","fragment"], // keys available to query

    aliases = { "anchor" : "fragment" }, // aliases for backwards compatability

    parser = {
        strict  : /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*):?([^:@]*))?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,  //less intuitive, more accurate to the specs
        loose   :  /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*):?([^:@]*))?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/ // more intuitive, fails on relative paths and deviates from specs
    },

    querystring_parser = /(?:^|&|;)([^&=;]*)=?([^&;]*)/g, // supports both ampersand and semicolon-delimted query string key/value pairs

    fragment_parser = /(?:^|&|;)([^&=;]*)=?([^&;]*)/g; // supports both ampersand and semicolon-delimted fragment key/value pairs

    function parseUri( url, strictMode )
    {
        var str = decodeURI( url ),
            res   = parser[ strictMode || false ? "strict" : "loose" ].exec( str ),
            uri = { attr : {}, param : {}, seg : {} },
            i   = 14;

        while ( i-- )
        {
            uri.attr[ key[i] ] = res[i] || "";
        }

        // build query and fragment parameters

        uri.param['query'] = {};
        uri.param['fragment'] = {};

        uri.attr['query'].replace( querystring_parser, function ( $0, $1, $2 ){
            if ($1)
            {
                uri.param['query'][$1] = $2;
            }
        });

        uri.attr['fragment'].replace( fragment_parser, function ( $0, $1, $2 ){
            if ($1)
            {
                uri.param['fragment'][$1] = $2;
            }
        });

        // split path and fragement into segments

        uri.seg['path'] = uri.attr.path.replace(/^\/+|\/+$/g,'').split('/');

        uri.seg['fragment'] = uri.attr.fragment.replace(/^\/+|\/+$/g,'').split('/');

        // compile a 'base' domain attribute

        uri.attr['base'] = uri.attr.host ? uri.attr.protocol+"://"+uri.attr.host + (uri.attr.port ? ":"+uri.attr.port : '') : '';

        return uri;
    };

    function getAttrName( elm )
    {
        var tn = elm.tagName;
        if ( tn !== undefined ) return tag2attr[tn.toLowerCase()];
        return tn;
    }

    return (function( url, strictMode ) {
        if ( arguments.length === 1 && url === true )
        {
            strictMode = true;
            url = undefined;
        }

        strictMode = strictMode || false;
        url = url || window.location.toString();

        return {

            data : parseUri(url, strictMode),

            // get various attributes from the URI
            attr : function( attr )
            {
                attr = aliases[attr] || attr;
                return attr !== undefined ? this.data.attr[attr] : this.data.attr;
            },

            // return query string parameters
            param : function( param )
            {
                return param !== undefined ? this.data.param.query[param] : this.data.param.query;
            },

            // return fragment parameters
            fparam : function( param )
            {
                return param !== undefined ? this.data.param.fragment[param] : this.data.param.fragment;
            },

            // return path segments
            segment : function( seg )
            {
                if ( seg === undefined )
                {
                    return this.data.seg.path;
                }
                else
                {
                    seg = seg < 0 ? this.data.seg.path.length + seg : seg - 1; // negative segments count from the end
                    return this.data.seg.path[seg];
                }
            },

            // return fragment segments
            fsegment : function( seg )
            {
                if ( seg === undefined )
                {
                    return this.data.seg.fragment;
                }
                else
                {
                    seg = seg < 0 ? this.data.seg.fragment.length + seg : seg - 1; // negative segments count from the end
                    return this.data.seg.fragment[seg];
                }
            }

        };

    });

})();

