#!/bin/sh
#
# Example CGI program that displays the time in plain ASCII text.
#
# Sid Bytheway
# Administrative Computing Services
# August 1995
#
echo "Content-type: text/plain"                                  
echo ""

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
echo "Today's date is: $DATE"
echo " The time is: $TIME"

exit 0
