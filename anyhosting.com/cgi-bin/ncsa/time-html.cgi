<html>
<head>
<title>Source code for the time-html.sh CGI Program</title>
</head>
<body>
<h1>Source code for the <tt>time-html.sh</tt> CGI Program</h1>
<hr>
<pre>
#!/bin/sh
#
# Example CGI program that displays the time in an HTML document.
#
# Sid Bytheway
# Administrative Computing Services
# August 1995
#

# Set Time zone variable so time is adjusted to Utah, rather than Greenwich.
# --------------------------------------------------
TZ=&quot;MST7MDT&quot;
export TZ

# Get the current date and time.
# --------------------------------------------------
DATE=`/bin/date +'%B %d, %Y'`
TIME=`/bin/date +'%T'`

# Send the data to the client.
# --------------------------------------------------
/usr/bin/cat &lt;&lt;EOF
Content-type: text/html

&lt;html&gt;
&lt;head&gt;
&lt;title&gt;The Current Date and Time&lt;/title&gt;
&lt;/head&gt;
&lt;body&gt;
&lt;h1&gt;The Current Date and Time&lt;/h1&gt;
&lt;hr&gt;
Today's date is: &lt;b&gt;$DATE&lt;/b&gt;&lt;br&gt;
The Current time is: &lt;b&gt;$TIME&lt;/b&gt;
&lt;/body&gt;
&lt;/html&gt;
EOF

exit 0

</pre></body></html>
