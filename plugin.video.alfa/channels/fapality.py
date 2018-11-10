# -*- coding: utf-8 -*-
#------------------------------------------------------------
import urlparse,urllib2,urllib,re
import os, sys
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools
from core import tmdb
from core import jsontools

host = 'https://fapality.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append( Item(channel=item.channel, title="Nuevas" , action="peliculas", url=host + "/newest/"))
    itemlist.append( Item(channel=item.channel, title="Mas Vistas" , action="peliculas", url=host + "/popular/"))
    itemlist.append( Item(channel=item.channel, title="Mejor valorada" , action="peliculas", url=host + "/top/"))
    itemlist.append( Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/channels/"))
    itemlist.append( Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append( Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "/search/?q=%s" % texto
    try:
        return peliculas(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<div class="item"><a href="([^"]+)" title="([^"]+)">.*?<img src="([^"]+)">.*?<div class="right">([^"]+)</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = scrapedtitle.replace("movies", "") + " (" + cantidad + ")"
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append( Item(channel=item.channel, action="peliculas", title=scrapedtitle , url=scrapedurl , thumbnail=scrapedthumbnail , plot=scrapedplot , folder=True) )
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron  = '<li class="masonry-item item ".*?<a href="([^"]+)" class="kt_imgrc popfire" title="([^"]+)" >.*?<img src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail  in matches:
        title = scrapedtitle
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        year = ""
        itemlist.append( Item(channel=item.channel, action="play" , title=title , url=scrapedurl, thumbnail=thumbnail, plot=plot, contentTitle = contentTitle, infoLabels={'year':year} ))
    next_page_url = scrapertools.find_single_match(data,'<li itemprop="url" class="current">.*?<a href="([^"]+)"')
    if next_page_url!="":
        next_page_url = urlparse.urljoin(item.url,next_page_url)
        itemlist.append( Item(channel=item.channel , action="peliculas" , title="Página Siguiente >>" , text_color="blue", url=next_page_url , folder=True) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = scrapertools.cachePage(item.url)
	#<source id="video_source_1" src="https://fapality.com/get_file/1/f82551e4920151d30f5cf7ffd0307e44/23000/23869/23869.mp4/?br=2052" type="video/mp4" data-is-hd="true" title="720p"><source id="video_source_2" src="https://fapality.com/get_file/1/2bcbf0efc756b6abfbf999c0a788c743/23000/23869/23869_480p.mp4/?br=1271" type="video/mp4" title="480p"><source id="video_source_3" src="https://fapality.com/get_file/1/d7be2e24a8a6bd6d1e10237c10adefb0/23000/23869/23869_240p.mp4/?br=516" type="video/mp4" title="240p"></video><div class="fluid-end-related" id="main_video_fluid_end_related" style='display:none'><div class="fluid-end-related-bg"><div class="fluid-end-tabs"><ul class="fluid-end-tabs-container"><li class="r_share">Share</li><li class="r_related active" onclick="myFP.getRelated('related','/related_videos_html.php?video_id=23869&mode_related=3');">Related Videos</li><li class="r_toprated" onclick="myFP.getRelated('toprated','/related_videos_html.php?video_id=23869&sort_by=rating&mode_related=3');">Related Top Rated Videos</li><li class="r_mostviewed" onclick="myFP.getRelated('mostviewed','/related_videos_html.php?video_id=23869&sort_by=video_viewed&mode_related=3');">Related Popular Videos</li><li class="r_channels" onclick="myFP.getRelated('channels','/related_videos_html.php?video_id=23869&mode_related=1&sort_by=last_time_view_date');">More from Nubiles-Porn</li><li class="r_models" onclick="myFP.getRelated('models','/related_videos_html.php?video_id=23869&mode_related=4&sort_by=last_time_view_date');">More Models Videos</li></ul></div><div class="fluid-end-related-body"><span class="fluid-end-related-close-btn" onclick="myFP.hideRelated(true);"><i class="fa fa-times"></i></span><div class="fluid-end-tab-content"><div id="r_share" class="fluid-end-tab-page"><div class="fluid-end-share-row"><div class="fluid-end-share-title">Share</div><div class="fluid-end-share-content"><div id="share_social" class="fluid-end-social" data-url="https://fapality.com/23869/" data-title="Amia Miley fucks GYM buddy and jiggles her big fake boobs" data-description="Amia Miley is a sporty brunette with ripped six pack and silicone implants in ass and titties. She works out at the GYM with her beefy boy, getting her pussy licked and fucked missionary style on the bench. Her big fake boobs and her round booty jiggle during doggystyle pounding. Amia rides it like a cowgirl and takes cum on face." data-media="https://i.fapality.com/videos_screenshots/23000/23869/preview_480p.mp4.jpg"></div></div></div><div class="fluid-end-share-row"><div class="fluid-end-share-title">Video Url:</div><div class="fluid-end-share-content"><input type="text" onclick="this.select();" id="current_url" readonly="readonly" value="https://fapality.com/23869/"/></div></div><div class="fluid-end-share-row"><div class="fluid-end-share-title">Embed code:</div><div class="fluid-end-share-content"><textarea onclick="this.select();" readonly="readonly" id="share_embed" rows="3"></textarea></div></div></div><div id="r_related" class="fluid-end-tab-page fluid-end-video-thumbs active-page"></div><div id="r_toprated" class="fluid-end-tab-page fluid-end-video-thumbs"></div><div id="r_mostviewed" class="fluid-end-tab-page fluid-end-video-thumbs"></div><div id="r_channels" class="fluid-end-tab-page fluid-end-video-thumbs"></div><div id="r_models" class="fluid-end-tab-page fluid-end-video-thumbs"></div></div></div></div></div></div><script src="/player/fplayers/fplayer.js"></script><link href="/player/fplayers/fplayer.css" rel="stylesheet" type="text/css"><script>var is_playlist = document.querySelector('.watch-list') ? true : false;var allow_download = is_playlist ? false : true;video_id = 23869;if(document.getElementById('video_source_2')) {document.getElementById('video_source_2').setAttribute('data-default','true');} else {document.getElementById('video_source_1').setAttribute('data-default','true');}function getEmbed() {var embedCode = '<iframe width="924" height="521" src="https://fapality.com/embed/23869" frameborder="0" allowfullscreen webkitallowfullscreen mozallowfullscreen oallowfullscreen msallowfullscreen>';embedCode += '</iframe>';return embedCode;}document.getElementById('share_embed').value = getEmbed();var adList = [];if(fluidPlayerClass.getCookie('pb_vast')==1) {adList.push({roll: 'preRoll',vastTag: "https://syndication.exosrv.com/splash.php?idzone=3180702",});} else {adList.push({roll: 'preRoll',vastTag: "https://syndication.exosrv.com/splash.php?idzone=2946968",});}adList.push({roll: 'midRoll',vastTag: 'https://syndication.exosrv.com/splash.php?idzone=2947082',size : '728x90',cookieTime : 1,timer:10,});htmlOnPauseBlock = {html : '<div class="fluid-b"><div class="fluid-b-title">Advertisement</div><div class="fluid-b-content"><iframe src="/b/inplayer.html" width="300" height="250" frameborder="0"  scrolling="no" allowtransparency="true" marginheight="0" marginwidth="0"></iframe></div><div class="fluid-b-footer"><span onclick="myFP.play()" class="fluid-b-btn">Continue Play</span></div><span onclick="myFP.play()" class="fluid-b-close-btn"><i class="fa fa-times"></i></span></div>',height: 277,width:304,onBeforeShow : function() {}};var myFP = fluidPlayer('main_video',{layoutControls: {timelinePreview: {file: 'https://fapality.com/thumbnails.vtt?id=23869&i=5&d=420&format=inplayer',type: 'VTT'},allowTheatre: true,allowDownload: allow_download,primaryColor:'#fb5350',shareCs:{url : 'https://fapality.com/cs/nubiles-porn/',title : 'View full video at Nubiles-Porn',},playbackRateEnabled: true,htmlOnPauseBlock: htmlOnPauseBlock,controlBar: {autoHide: true,autoHideTimeout: 3,animated: true,},},vastOptions: {adList: adList,vastAdvanced: {vastLoadedCallback: (function() {if(fluidPlayerClass.getCookie('pb_source')=="1") {fluidPlayerClass.setCookie('pb_vast',1,6);}}),noVastVideoCallback:      (function() {}),vastVideoSkippedCallback: (function() {}),vastVideoEndedCallback:   (function() {})},adCTAText: false,vastTimeout: 5000,}});var player_obj = myFP;</script><div class="cs"><noindex><a href="https://fapality.com/cs/nubiles-porn/" rel="nofollow" target="_blank" title="Nubiles-Porn"><img src="https://fapality.com/contents/content_sources/112/c1_nubiles-porn.png" alt="Nubiles-Porn"></a></noindex></div></div><meta itemprop="duration" content="T7M00S" /><meta itemprop="thumbnailUrl" content="https://i.fapality.com/videos_screenshots/23000/23869/preview_480p.mp4.jpg" /><meta itemprop="embedUrl" content="https://fapality.com/embed/23869/"><meta itemprop="requiresSubscription" content="false"><meta itemprop="uploadDate" content="2018-11-01"><meta itemprop="encodingFormat" content="mpeg4"><div class="simple-toolbar"><div class="btn-group right"><a class="btn toggle" data-toggle-id="#shares"><i class="fa fa-share-alt"></i> Share or Embed <i class="fa fa-caret-down"></i></a></div><div class="btn-group right"><span data-tooltip aria-haspopup="true" title="Report Inappropriate Content" id="report_button" data-dropdown="report" aria-controls="report" aria-expanded="false" class="btn radius"><i class="fa fa-flag"></i></span></div><form id="report" data-abide class="f-dropdown small" data-dropdown-content class="f-dropdown" aria-hidden="true" tabindex="-1"><div class="box"><div class="title">Report Inappropriate Content</div><div class="content"><label for="flag-1"><input type="radio" id="flag-1" value="flag_inappropriate_video" name="flag_id"> Inappropriate Video</label><label for="flag-2"><input type="radio" id="flag-2" value="flag_error" name="flag_id"> Error (no video, no sound)</label><label for="flag-3"><input type="radio" id="flag-3" value="copyrighted_video" name="flag_id"> Copyright material</label><textarea required name="flag_message" id="report_text" rows="3" placeholder="Please tell us the reason"></textarea><small class="error">The field is required</small><input type="hidden" name="action" value="flag"><input type="hidden" name="mode" value="async"><input type="hidden" name="video_id" value="23869"></div><div class="bottom"><span id="send_report" class="btn">Send Report</span></div></div></form><div class="btn-group right"><a href="https://fapality.com/login.php?action=not_allowed" data-reveal-id="login_wrapper" data-reveal-ajax="/login.php?m=1&action=not_allowed" class="btn"><i class="fa fa-plus-circle"></i> Add to Faplist</a></div><div class="btn-group right"><a data-tooltip aria-haspopup="true" href="https://fapality.com/login.php?action=not_allowed" title="Save in favourites" data-reveal-id="login_wrapper" data-reveal-ajax="/login.php?m=1&action=not_allowed" class="btn"><i class="fa fa-heart"></i><i class="fa fa-plus"></i></a><span class="btn btn-content">0</span></div><div class="btn-group likes" itemprop="aggregateRating" itemscope itemtype="http://schema.org/AggregateRating"><span class="btn" id="like" data-tooltip aria-haspopup="true" title="I Like It"><i class="fa fa-thumbs-up"></i> <span class="g_hidden">I Like It</span></span><meta itemprop="bestRating" content="100"><meta itemprop="worstRating" content="0"><span class="btn btn-content"><span class="rating-info"><span id="rating_value" itemprop="ratingValue">94</span>% (<span class="tiny" id="rating_amount" itemprop="ratingCount">3</span>)</span><span class="rating-line"><span style="width:93.334px"></span></span></span><span class="btn" id="dislike" data-tooltip aria-haspopup="true" title="I Dislike It"><i class="fa fa-thumbs-down"></i> <span class="g_hidden">I Dislike It</span></span></div><div class="btn-group"><a href="https://fapality.com/login.php?action=not_allowed" data-reveal-id="login_wrapper" data-reveal-ajax="/login.php?m=1&action=not_allowed" class="btn downloadVideos"><i class="fa fa-download"></i> Download (105.22 Mb)</a></div><i class="fa fa-spin fa-spinner ajax-loader g_hidden"></i><div class="share toolbox row" id="shares"><div class="columns large-6"><label>Embed code:</label><textarea id="embed_code" readonly class="copy_click" rows="3"></textarea></div><div class="columns large-6"><label>Share video:</label><div class="addthis_sharing_toolbox"></div><input type="text" readonly id="current_url" class="copy_click" value="https://fapality.com/23869/"></div></div></div><div class="simple-footer"><div class="description" itemprop="description">Amia Miley is a sporty brunette with ripped six pack and silicone implants in ass and titties. She works out at the GYM with her beefy boy, getting her pussy licked and fucked missionary style on the bench. Her big fake boobs and her round booty jiggle during doggystyle pounding. Amia rides it like a cowgirl and takes cum on face.</div><div class="right content_source" itemprop="productionCompany" itemscope itemtype="http://schema.org/Organization"><a data-view="/ajax.php?mode=async&function=get_block&block_id=content_source_view_get_channel&cs_id=112" data-dropdown-width="small" class="button" href="https://fapality.com/channels/nubiles-porn/" title="Nubiles-Porn videos"><i class="fa fa-video-camera"></i> Nubiles-Porn</a><meta itemprop="name" content="Nubiles-Porn"><meta itemprop="url" content="https://fapality.com/channels/nubiles-porn/"><script>var addonView = {'name' : 'channel','url'  : '/ajax.php?mode=async&function=get_block&block_id=list_content_sources_channel&q=Nubiles-Porn',}</script></div><div class="right content_source"><a class="button info" data-view="/ajax.php?mode=async&function=get_block&block_id=model_view_get_model&model_id=929" data-dropdown-width="small" href="https://fapality.com/pornstars/amia-miley/" title="Amia Miley videos" itemscope itemprop="actor" itemtype="http://schema.org/Person"><i class="fa fa-female"></i> Amia Miley<meta itemprop="name" content="Amia Miley"><meta itemprop="url" content="https://fapality.com/pornstars/amia-miley/"></a><script>var addonView = {'name' : 'model','url'  : '/ajax.php?mode=async&function=get_block&block_id=list_models_model&model_id=929&q=Amia+Miley',}</script></div><ul class="meta"><li>Added: <span>4 days ago</span> <span>by</span> <a href='/users/1/' data-view='/ajax.php?mode=async&function=get_block&block_id=member_profile_view_get_profile&user_id=1'>Admin</a></li><li>Duration: <span>7:00</span></li><li>Viewed: <span>1,499</span></li></ul><meta itemprop="genre" content="Big tits"><ul class="tags_list"><li>Categories</li><li><a class="main" href="https://fapality.com/categories/big-tits/" title="Big tits videos">Big tits</a></li><li><a href="https://fapality.com/categories/big-tits/workout/" title="Big tits workout videos">workout</a></li><li><a href="https://fapality.com/categories/big-tits/gym/" title="Big tits GYM videos">GYM</a></li><li><a href="https://fapality.com/categories/big-tits/sporty/" title="Big tits sporty videos">sporty</a></li><li><a href="https://fapality.com/categories/big-tits/tanned/" title="Big tits tanned videos">tanned</a></li><li><a href="https://fapality.com/categories/big-tits/athletic/" title="Big tits athletic videos">athletic</a></li><li><a href="https://fapality.com/categories/big-tits/fake-tits/" title="Big tits fake tits videos">fake tits</a></li><li><a href="https://fapality.com/categories/big-tits/fake-ass/" title="Big tits fake ass videos">fake ass</a></li><li><a href="https://fapality.com/categories/big-tits/pussy-licking/" title="Big tits pussy licking videos">pussy licking</a></li><li><a href="https://fapality.com/categories/big-tits/missionary/" title="Big tits missionary videos">missionary</a></li><li><a href="https://fapality.com/categories/big-tits/orgasm/" title="Big tits orgasm videos">orgasm</a></li><li><a href="https://fapality.com/categories/big-tits/doggystyle/" title="Big tits doggystyle videos">doggystyle</a></li><li><a href="https://fapality.com/categories/big-tits/riding/" title="Big tits riding videos">riding</a></li><li><a href="https://fapality.com/categories/big-tits/cumshot/" title="Big tits cumshot videos">cumshot</a></li><li><a href="https://fapality.com/categories/big-tits/tattoos/" title="Big tits tattoos videos">tattoos</a></li></ul></div></div></div>
		
	
    patron  = '<source id="video_source_1" src="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl  in matches:
        url =  scrapedurl
    itemlist.append(item.clone(action="play", title=url, fulltitle = item.title, url=url))
    return itemlist

