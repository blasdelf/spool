#Spool

I wrote this for the beta Google AppEngine API to have a free one-click-install of a group chat/blog on AppSpot, even including a "Get Your Own Spool" button in the header a pastiche of the original Blogspot template. It's based loosely on the structure of the long-defunct http://2lmc.org/spool/ — blog posts have the flavor of a chat-log, composed solely of comments, with no primacy given to the first one.

This was originally hosted on Google Code before GitHub was a thing and I didn't migrate before that was shut down so the original commit history is lost.

##Novelties:

* Good archive pages: nearly all webapps with reverse-chronological presentation count up from the present, with numbered pages where the content on "page 1" constantly changes as things are posted. Spool counts down instead, and paginates by month instead of having two similar sets of archive pages.

* An atom feed for threads, with two ways to generate it: ordered on recently added comments, or on recent started threads.

* Clever user input escaping: uses a BeautifulSoup parser to whitelist allowed tags/attributes and strip comments, none of the attacks listed at http://ha.ckers.org/xss.html get past it. It also escapes wild ampersands without butchering terminated entities (why does nobody do that?).

* Unicode allowed everywhere, even in URLs (as percent-encoded UTF-8).

* Threads are uniquely identified in the datastore (and URLs) using an incrementing key_name on the db.Model. I didn't use the URL titles as key names because you can't change them and there would be name collisions, I didn't use db.Model ids because they come from a shared pool and would not be contiguous. Since key_names can't start with a number, I had to use a prefix character to store it, so I figured I might as well be cute and use "x" as the prefix and hexadecimal for the incrementing numbers. Keeping the prefix char in the URL ends up simplifying URL routing as a bonus.

* Some things are memcached: generated Atom feeds, getting comments for a thread from the datastore, and authenticating users.

* Friendly to being combined with other programs in one AppEngine app.