#!/bin/sh
#
cat - << \END
Content-Type: text/html

<html><head>
<title>Subscription Sent</title>
</head>
<BODY text="#000000" bgcolor="EEEEEE" link="#AA0000" vlink="#AA0000">
<h2 align="center">Subscription Sent, Thank you.</h2>
<p>
<HR>
END
#
# process form data
#
#eval `/usr/usersb2/w93/fp/CGI/ProcCGIInput`
#eval `/usr/local/www//cgi-bin/proccgi`
eval `/var/www/anyhosting.com/cgi-bin/proccgi`
#
# Compose email message
#
echo "Thank you $FORM_name."
(
  echo "From: $FORM_name <$FORM_email>"
  echo "Subject: [Virtual Domain Subscriber]"
  echo "X-Info: Sent by NamodnSubscribe"
  echo
  echo "<-->"
  echo "           From:  $FORM_name"
  echo "	Company:  $FORM_company"
  echo "          Email:  $FORM_email"
  echo "        Service:  W3 - Virtual Domain Hosting" 
  echo "           Host:  $REMOTE_ADDR ($REMOTE_HOST)"
  echo "        Broswer:  $HTTP_USER_AGENT"
  echo "    Domain Name:  $FORM_domain"
  echo "Pre-Registered?:  $FORM_DAR"
  echo "<-->"
  echo
  echo Billing Address:
  echo "$FORM_address" | tr '\015' '\012'
  echo
  echo Where did you hear about us?:
  echo "$FORM_from" | tr '\015' '\012'
  echo
  echo Business Use Comments: 
  echo "$FORM_comments" | tr '\015' '\012'
  echo
) | /usr/sbin/sendmail -f"$FORM_email" -F"$FORM_name" admin 
#
if [ $? = "0" ] ; then
	echo "<BR>"
        echo "We will return your email as soon as possible."
	echo "<BR>"
	echo "<P></P>" 
 	echo "If you have comments or questions about this service, send email to <A HREF="mailto:admin@anyhosting.com">admin@anyhosting.com</A>"
	echo "<BR>"
	echo "<HR>"
else
        echo "Oops, I could not send the mail."
        echo "Please send an email to"
        echo "<i>&lt;admin@anyhosting.com&gt;</i>."
fi
#
echo "<BR>"
echo "<H3><A HREF="http://anyhosting.com" target="_top">Back to anyhosting.com</A></H3>"
echo "<p>"
echo "</body> </html>"
exit 0
