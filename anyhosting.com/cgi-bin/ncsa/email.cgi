#!/bin/sh
#
cat - << \END
Content-Type: text/html

<html><head>
<title>Frank's Email By Web</title>
</head><body>
<h1 align="center">Frank's Email By Web</h1>
<p>
END
#
# process form data
#
#eval `/usr/usersb2/w93/fp/CGI/ProcCGIInput`
eval `/usr/local/www//cgi-bin/proccgi`
#
# Compose email message
#
(
  echo "From: $FORM_name <$FORM_email>"
  echo "Subject: [EBW] $FORM_subject"
  echo "X-Info: Sent by SendAComment"
  echo
  echo "<-->"
  echo "    From: $FORM_name"
  echo "   Email: $FORM_email"
  echo " Subject: $FORM_subject"
  echo "    Host: $REMOTE_ADDR ($REMOTE_HOST)"
  echo "   Agent: $HTTP_USER_AGENT"
  echo "<-->"
  echo
  echo "$FORM_text" | tr '\015' '\012'
  echo
  echo "`date`"
) | /usr/sbin/sendmail -f"$FORM_email" -F"$FORM_name" robert
#
if [ $? = "0" ] ; then
        echo "Your comment was sent. I just hope your email address was"
        echo "correct. If it wasn't, I have no choice but to ignore you."
        echo "<p>"
        echo "Also, please be patient with me. I answer most of my emails,"
        echo "but this takes quite some time. I am especially slow if I"
        echo "feel that your question is well answered by the other"
        echo "documents I have on the Web. Most of the Mail is read at"
        echo "home, where I do not have a live Internet connection, so"
        echo "questions requiring some Web search will naturally take"
        echo "longer, too."
        echo "<p>"
        echo "Local Time is `date`."
else
        echo "Oops, I could not send the mail. Sendmail failed for some"
        echo "reason. Please send an email to"
        echo "<i>&lt;fp@informatik.uni-frankfurt.de&gt;</i>."
fi
#
echo "<p>"
echo "<hr>"
echo "<address><a href=\"http://www.uni-frankfurt.de/~fp/Frank.html\">Frank Pilhofer</a> &lt;fp@informatik.uni-frankfurt.de&gt; <a href=\"http://www.uni-frankfurt.de/~fp/uudeview/\">Back to Frank's Homepage</a></address>"
echo "</body> </html>"
exit 0
