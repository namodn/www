#!/usr/bin/perl

# randpic.pl
# A simple random picture generator
# Robert Niles, rniles@selah.net
#
# Another simple hack to randomly pick an
# image and display it. Neat for those little
# advert banners.
# I saw something like this that Matt Wright had done
# and then decided to do my own. The idea came from him
# but the code is mine.

# This script is called with SSI (Server Side Includes)
# with a command of:
# <!--#exec cgi="/cgi-bin/randpic.pl"-->
# ....of course, change the path to the script if needed

# Each of the following sections define a portion of the 
# returned image and links. They are as follows:

# pics = path to the image files
# url  = the address and URI to link to (no http: here!)
# alt  = The ALT text for those not displaying graphics
# comment = A short little comment to accompany the graphic.

# In this example there are five images defined. You can add or
# subtrack to this as you wish.

@pics= ("http://www.namodn.com/bug/dancing.gif",
        "http://www.namodn.com/bug/adrsun.gif",
	"http://www.namodn.com/bug/eye.gif",
	"http://www.namodn.com/bug/angel.gif",
	"http://www.namodn.com/bug/hand.jpg",
	"http://www.namodn.com/bug/escape.jpg");

# Now we pick a random number and assign it to $picnum
srand(time ^ $$);
$picnum = rand(@pics);

# Now we display it. I've used tables here to format the output nicely.

print "Content-type: text/html\n\n";
print "<IMG SRC=\"$pics[$picnum]\" alt=\"$alt[$picnum]\" border=0>";
exit;
