#!/bin/sh
echo Content-type: text/html
echo
/usr/local/bin/webalizer -c /usr/local/etc/webalizer_linque.conf > /dev/null
echo '<HTML>'
echo '<BODY TEXT="#000000" BGCOLOR="#E8E8E8">'
echo '<FONT SIZE=5>'
echo '<CENTER>'
echo Access statistics have been generated.
echo '<BR>&nbsp<BR>'
echo '<A HREF="usage/index.html">'
echo 'Click here for results</A>'
echo '</CENTER>'
echo '</BODY>'
echo '</HTML>'
