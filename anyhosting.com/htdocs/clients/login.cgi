#!/bin/sh
#
eval `/usr/local/www//cgi-bin/proccgi`
cat - << \END
Content-Type: text/html

<HTML>
<BODY TEXT="#000000" BGCOLOR="#E8E8E8">
<CENTER>
<FONT SIZE=5>
END

if [ "x$FORM_domain" = "x" ] ; then
FORM_domain=blank
fi 

if [ -x $FORM_domain ] ; then
echo '<H1>'$FORM_domain'</H1>'
echo '<BR>&nbsp<BR>'
echo '<A HREF="'$FORM_domain'">Click here to login</A>'
else
echo Not Found
fi

echo '</FONT>'
echo '</CENTER>'
echo '</BODY>'
echo '</HTML>'
