#!/bin/sh
echo
echo "<CENTER>"
echo "Password Accepted"
echo "<BR>"
echo "Click on the links below to perform the corresponding actions."
echo "<BR>"
echo "<HR>"
echo "<P>"
echo "<A HREF="webalizer/index.html">See usage statistics</A>"
echo "</P>"
echo "<P>"
echo "<A HREF="logs/">See raw logs</A>"
echo "</P>"
echo "<P>"
echo "<A HREF="billing/">Billing Info</A>"
echo "</CENTER>"
/usr/bin/webalizer -c /etc/webalizer/artwritingmusic.com.conf > /dev/null
