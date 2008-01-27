#!/bin/sh
#

# process form data
eval `/var/www/anyhosting.com/cgi-bin/proccgi`

cat - << \END
Content-Type: text/html

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
"http://www.w3.org/TR/html4/strict.dtd">
<html>
  <head>
    <title>AnyHosting - Registration receieved.</title>
    <link type="text/css" title="normal" rel="stylesheet" href="/normal.css">
  </head>
  <body>
  <div id="main">
    <h1>AnyHosting Services</h1>
    <h2>Registration receieved.</h2>
END
#
# Compose email message
#
(
  echo "From: $FORM_name <$FORM_email>"
  echo "Subject: [Virtual Domain Subscriber]"
  echo "X-Info: Sent by AHSubscribe"
  echo
  echo "<-->"
  echo "           From:  $FORM_name"
  echo "	Company:  $FORM_company"
  echo "          Email:  $FORM_email"
  echo "          Phone:  $FORM_phone"
  echo "        Service:  W3 - Virtual Domain Hosting" 
  echo "           Host:  $REMOTE_ADDR ($REMOTE_HOST)"
  echo "        Broswer:  $HTTP_USER_AGENT"
  echo "    Domain Name:  $FORM_domain"
  echo "<-->"
  echo
  echo Billing Address:
  echo "$FORM_address" | tr '\015' '\012'
  echo
) | /usr/sbin/sendmail -f"$FORM_email" -F"$FORM_name" admin 
#
if [ $? = "0" ] ; then
echo "<p>Thank you ${FORM_name}."
cat - << \END
    We will contact you shortly.
    </p>
END
else
cat - << \END
    <p>Oops, I could not send the mail.
    <br>
    Please send an email to
    <a href="mailto:admin@anyhosting.com">admin@anyhosting.com</a>
    </p>
END
fi
cat - << \END
    <p><a href="/">Return to anyhosting.com</a><br>
    <a href="/contact">Contact us</a></p>
  </div>
  <p>&copy;2008 AnyHosting</p>
  </body>
</html>
END
exit 0
