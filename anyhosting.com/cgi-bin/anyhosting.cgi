#!/bin/sh
#
cat - << \END
Content-Type: text/html

<html><head>
<title>Thank You</title>
</head>
<BODY text="#000000" bgcolor="E8E8E8" background="" vlink="#FFFFFF">
<h2 align="center">Thank you. Your request is being processed.</h2>
<p>
<HR>
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
 echo "From: $FORM_FirstName $FORM_LastName <$FORM_Email>"
  echo "Subject: [AnyHosting Client]"
  echo "X-Info: Sent by NamodnSubscribe"
  echo
  echo "<-->"
  echo "    From:  $FORM_FirstName $FORM_LastName"
  echo "   Email:  $FORM_Email"
  echo "  Domain:  $FORM_domain" 
  echo " Company:  $FORM_Company"
  echo "    Type:  $FORM_Type"
  echo " Address:  $FORM_Street"
  echo " City,St:  $FORM_City, $FORM_State $FORM_Zip"
  echo "   Phone:  $FORM_Phone"
  echo "    Host:  $REMOTE_ADDR $REMOTE_HOST"
  echo " Broswer:  $HTTP_USER_AGENT"
  echo "<-->"
  echo
  echo Comments : 
  echo "$FORM_Comments" | tr '\015' '\012'
  echo
) | /usr/sbin/sendmail -f"$FORM_email" -F"$FORM_name" admin 
#
if [ $? = "0" ] ; then
        echo "We will contact you as soon as possible."
	echo "<BR>"
	echo "<P></P>" 
 	echo "If you have comments or questions about this service, send email to <A HREF="mailto:admin@namodn.com">admin@namodn.com</A>"
	echo "<BR>"
	echo "<HR>"
else
        echo "Oops, I could not send the mail. Sendmail failed for some"
        echo "reason. Please send an email to"
        echo "<i>&lt;admin@namodn.com&gt;</i>."
fi
#
echo "<BR>"
echo "<H3><A HREF="http://www.AnyHosting.com">Back to AnyHosting.com</A></H3>"
echo "<p>"
echo "</body> </html>"
exit 0
