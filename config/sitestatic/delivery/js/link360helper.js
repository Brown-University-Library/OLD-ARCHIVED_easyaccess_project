
if(jQuery('#CitationResults') !=null){
   jQuery('#CitationResults').hide();
   jQuery("div.SS_LocaleWidget").hide();
   jQuery("body").append("<div>redirecting.....</div>");
   var sections=window.location.href.split("?");
   var params = document.location.search.substring(1).split('&');
   //redirect Google Scholar referrals to easyArticle.  
   if ((sections.length>0) && (params.indexOf("sid=google")) > -1){
      window.location.href="http://library.brown.edu/easyarticle/?"+sections[1];
   }
};
  

