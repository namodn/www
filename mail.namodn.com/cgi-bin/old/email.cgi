#!/usr/bin/suidperl
#/usr/bin/perl -wT
#############################################################################
# neomail.pl - Provides a web interface to user mail spools                 #
# Copyright (C) 2000 Ernie Miller                                           #
#                                                                           #
# This program is free software; you can redistribute it and/or             #
# modify it under the terms of the GNU General Public License               #
# as published by the Free Software Foundation; either version 2            #
# of the License, or (at your option) any later version.                    #
#                                                                           #
# This program is distributed in the hope that it will be useful,           #
# but WITHOUT ANY WARRANTY; without even the implied warranty of            #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
# GNU General Public License for more details.                              #
#                                                                           #
# You should have received a copy of the GNU General Public License         #
# along with this program; if not, write to the Free Software Foundation,   #
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.           #
#############################################################################

use strict;
use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser);

CGI::nph();   # Treat script as a non-parsed-header script

$ENV{PATH} = ""; # no PATH should be needed

################# USER-CONFIGURABLE SECTION ##################

# domainname - The value of domainname will be appended to all outgoing
#              messages. The best way to handle multiple outgoing domains
#              is to use multiple copies of this script, configured for
#              each domain.
my $domainname = 'namodn.com';

# sendmail - The location of your sendmail binary, works with both sendmail
#            and exim, which can be run as sendmail and accepts the parameters
#            sent in this script.  Hopefully works with qmail's sendmail
#            compatability mode as well... let me know how it works!
my $sendmail = '/usr/sbin/sendmail';

# passwdfile - This is the location of the file containing both usernames and
#              their corresponding encrypted passwords.  If you're using
#              shadowed passwords, change it to /etc/shadow, and if you're
#              using FreeBSD, you probably want /etc/master.passwd
my $passwdfile = '/etc/shadow';

# timeoffset - This is the offset from GMT, in the notation [-|+]XXXX notation.
#              For example, for EST, the offset is -0500.
my $timeoffset = '-0500';

# neomaildir - This directory should be mode 700 and owned by the user this
#              script will be running as (root in many cases).  It will hold
#              temporary session files containing the IP address of the user
#              currently using each session.
my $neomaildir = '/var/neomail/mail.namodn.com/';

# userprefsdir - This directory will hold individual directories for users
#                to store their personal preferences, signatures, and
#                addressbooks in.
my $userprefsdir = '/var/neomail/mail.namodn.com/users/';

# stylesdir - This directory will hold style specifications that the users can
#             choose from to customize their NeoMail look.
my $stylesdir = '/var/neomail/styles/';

# logfile - This should be set either to 'no' or the filename of a file you'd
#           like to log actions to.
my $logfile = '/var/neomail/neomail.log';

# sessiontimeout - This indicates how many minutes of inactivity pass before
#                  a session is considered timed out, and the user needs to
#                  log in again.  Make sure this is big enough that a user
#                  typing a long message won't get autologged while typing!
my $sessiontimeout = 30;

# numberofheaders - This indicates the maximium number of headers to display
#                   to a user at a time.  Keep this reasonable to ensure
#                   fast load times for slow connection users.
my $numberofheaders = 20;

# mailspooldir - This is where your user mail spools are kept.  This value
#                will be ignored if you're using a system that doesn't
#                store mail spools in a common directory, and you set
#                homedirspools to 'yes'
my $mailspooldir = '/var/spool/mail/';

# scripturl - The location (relative to ServerRoot) of the CGI script, used in some
#             error messages to provide a link back to the login page
my $scripturl = '/cgi-bin/email.cgi';

# prefsurl - This is the location (relative to ServerRoot) of the user setup
#            and address book script.
my $prefsurl = '/cgi-bin/email-prefs.cgi';

# homedirspools - Set this to 'yes' if you're using qmail, and set the next
#                 two variables to the home directory base path for users, and
#                 the filename of the mail spool in their directories.
#                 Appropriate defaults have been supplied.
my $homedirspools = 'no';
my $homedir = '/home/';
my $homedirspoolname = 'Mailbox';

# bg_url - Set this to the location of a graphic you would like to use as a
#          background for all of your mail client pages.
my $bg_url = '/images/neomail-bg.gif';

# logo_url - This graphic will appear at the top of all NeoMail pages.
my $logo_url = '/images/neomail-logo.gif';

# image_url - This points to the relative URL where NeoMail will find its
#             graphics, for buttons, icons, and the like.
my $image_url = '/images/';

############### END USER-CONFIGURABLE SECTION ################

my $version = "0.65";

# %month is used in the getheaders() sub to convert localtime() dates to
# a better format for readability and sorting.
my %month = qw(Jan   1
               Feb   2
               Mar   3
               Apr   4
               May   5
               Jun   6
               Jul   7
               Aug   8
               Sep   9
               Oct   10
               Nov   11
               Dec   12);

my $thissession = param("sessionid") || '';
my $user = $thissession || '';
$user =~ s/\-session\-0.*$//; # Grab userid from sessionid
($user =~ /^(.+)$/) && ($user = $1);  # untaint $user...

my %prefs = %{&readprefs};
my %style = %{&readstyle};

my $firstmessage;
if (param("firstmessage")) {
   $firstmessage = (param("firstmessage") -1);  # -1 deals with "Jump" numbers
} else {
   $firstmessage = 0;
}

my $sort;
if (param("sort")) {
   $sort = param("sort");
} else {
   $sort = $prefs{"sort"} || 'date';
}

my $folder;
if (param("folder")) {
   $folder = param("folder");
   neomailerror ("No such folder: $folder") unless ( ($folder eq 'INBOX') ||
      ($folder eq 'SENT') || ($folder eq 'SAVED') || ($folder eq 'TRASH') );
} else {
   $folder = "INBOX";
}

$sessiontimeout = $sessiontimeout/60/24; # convert to format expected by -M

# once we print the header, we don't want to do it again if there's an error
my $headerprinted = 0;
my $total_size = 0;

########################## MAIN ##############################
if (param()) {      # an action has been chosen
   my $action = param("action");
   if ($action =~ /^(\w+)$/) {
      $action = $1;
      if ($action eq "login") {
         login();
      } elsif ($action eq "displayheaders") {
         displayheaders();
      } elsif ($action eq "readmessage") {
         readmessage();
      } elsif ($action eq "deletemessage") {
         deletemessage();
      } elsif ($action eq "viewattachment") {
         viewattachment();
      } elsif ($action eq "composemessage") {
         composemessage();
      } elsif ($action eq "sendmessage") {
         sendmessage();
      } elsif ($action eq "savemessage") {
         savemessage();
      } elsif ($action eq "logout") {
         logout();
      }
   } else {
      neomailerror("Action has illegal characters!");
   }
} else {            # no action has been taken, display login page
   printheader(),
   print "<p align=\"center\"><img border=\"0\" src=\"$logo_url\"></p>\n";

   print '<table border="0" align="center" width="40%" cellpadding="0" cellspacing="0">';

   print '<tr><td bgcolor=',$style{"titlebar"},' align="left">',
   '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>LOGIN</b></font>',
   '</td></tr><tr><td align="center" valign="middle" bgcolor=',$style{"window_light"},'>';

   print start_form();
   print hidden("action","login");
   print '<BR>';
   print p("UserID: ", textfield(-name=>'userid',
                                 -default=>'',
                                 -size=>'10',
                                 -override=>'1'),
           "<BR>Password: ", password_field(-name=>'password',
                                            -default=>'',
                                            -size=>'10',
                                            -override=>'1'),'<BR>',
                             submit("Login"), reset("Clear"));
   print end_form();
   print '</td></tr></table>';
   print "<p align=\"center\"><FONT SIZE=\"1\"><BR>
          <a href=\"http://neomail.sourceforge.net\">
          NeoMail</a> version $version<BR>Designed by
          <a href=\"mailto:neorants\@users.sourceforge.net\">Ernie Miller</a></FONT></FONT></p>";
   print end_html();
}
###################### END MAIN ##############################

####################### LOGIN ########################
sub login {
   my $userid = param("userid");
   my $password = param("password");
   $userid =~ /^(.+)$/; # accept any characters for userid/pass auth info
   $userid = $1;
   $password =~ /^(.+)$/;
   $password = $1;

# Checklogin() is modularized so that it's easily replaceable with other
# auth methods.
   if (checklogin($userid,$password)) {
      $thissession = $userid . "-session-" . rand(); # name the sessionid
      writelog("Successful login - $thissession");

      cleanupoldsessions(); # Deletes sessionids that have expired

      open (SESSION, '>' . $neomaildir . $thissession) or # create sessionid
         neomailerror("Couldn't open session file!");
      print SESSION "$ENV{REMOTE_ADDR}";
      close (SESSION);
      $user = $userid;
      if ( -d "$userprefsdir$user" ) {
         %prefs = %{&readprefs};
         %style = %{&readstyle};
         $sort = $prefs{"sort"} || 'date';
         displayheaders();
      } else {
         firsttimeuser();
      }
   } else { # Password is INCORRECT
      printheader();
      print '<BR><BR><BR><BR><BR><BR>';
      print '<table border="0" align="center" width="25%" cellpadding="0" cellspacing="0">';

      print '<tr><td bgcolor=',$style{"titlebar"},' align="left">',
            '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>INVALID LOGIN</b></font>',
            '</td></tr>';
      print '<tr><td valign="middle" align="center" bgcolor=',$style{"window_light"},'>';

      print "<BR>Sorry, the password you entered was incorrect! Please
             go back and <a href=\"$scripturl\">try again</a>.<BR><BR>";
      print '</td></tr></table>';
      printfooter();
      exit 0;
   }
}
#################### END LOGIN #####################

#################### LOGOUT ########################
sub logout {
   neomailerror("Session ID has invalid characters!") unless
      (($thissession =~ /^([\w\.\-]+)$/) && ($thissession = $1));
   unlink "$neomaildir$thissession";

   writelog("User logout - $thissession");

   print "Location: $scripturl\n\n";
}
################## END LOGOUT ######################

#################### CHECKLOGIN ####################
sub checklogin {
   my ($username, $password, $usr, $pswd);
   my $passcorrect = 1; # default to correct, see end of sub for reason
   $username = shift;
   $password = shift;

   open (PASSWD, $passwdfile) or neomailerror("Couldn't open $passwdfile!");
   while (defined(my $line = <PASSWD>)) {
      ($usr,$pswd) = (split(/:/, $line))[0,1];
      last if ($usr eq $username); # We've found the user in /etc/passwd
   }
   close (PASSWD);
   if (($usr ne $username) or (crypt($password, $pswd) ne $pswd)) {
      $passcorrect = 0; # User/Pass combo is WRONG!
      writelog("Failed login - $username");
   }
   return $passcorrect;
}
################ END CHECKLOGIN #####################

################ CLEANUPOLDSESSIONS ##################
sub cleanupoldsessions {
   opendir (NEOMAILDIR, "$neomaildir") or
      neomailerror("Couldn't opendir $neomaildir!");
   while (defined(my $sessionid = readdir(NEOMAILDIR))) {
      if ($sessionid =~ /^(\w+\-session\-0\.\d*)$/) {
         $sessionid = $1;
         if ( -M "$neomaildir/$sessionid" > $sessiontimeout ) {
            writelog("Cleaning up old session file - $sessionid");
            unlink "$neomaildir/$sessionid";
         }
      }
   }
   closedir (NEOMAILDIR);
}
############## END CLEANUPOLDSESSIONS ################

############## VERIFYSESSION ########################
sub verifysession {
   if ( -M "$neomaildir/$thissession" > $sessiontimeout || !(-e "$neomaildir/$thissession")) {
      printheader();
      print '<BR><BR><BR><BR><BR><BR>';
      print '<table border="0" align="center" width="25%" cellpadding="0" cellspacing="0">';

      print '<tr><td bgcolor=',$style{"titlebar"},' align="left">',
            '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>INVALID LOGIN</b></font>',
            '</td></tr>';
      print '<tr><td valign="middle" align="center" bgcolor=',$style{"window_light"},'>';

      print "<BR>Sorry, your session seems to have timed out!  Please
             go back and <a href=\"$scripturl\">login</a>.<BR><BR>";
      print '</td></tr></table>';
      printfooter();
      writelog("User attempted to access timed-out session - $thissession");
      exit 0;
   }
   neomailerror("Session ID has invalid characters!") unless
      (($thissession =~ /^([\w\.\-]+)$/) && ($thissession = $1));
   open (SESSION, '>' . $neomaildir . $thissession) or
      neomailerror("Couldn't open session file!");
   print SESSION "$ENV{REMOTE_ADDR}";
   close (SESSION);
   return 1;
}
############# END VERIFYSESSION #####################

################ DISPLAYHEADERS #####################
sub displayheaders {
   verifysession();
   printheader();
   my ($bgcolor, $status, $message_size);
   my @headers = @{&getheaders($user)};
   my $numheaders = $#headers + 1 || 0;
   my $page_total = $numheaders/$numberofheaders || 1;
   $page_total = int($page_total) + 1 if ($page_total != int($page_total));

   if (defined(param("custompage"))) {
      my $pagenumber = param("custompage");
      $pagenumber = 0 if ($pagenumber < 0);
      $pagenumber = $page_total if ($pagenumber > $page_total);
      $firstmessage = ($pagenumber-1)*$numberofheaders;
   }

### Perform verification of $firstmessage, make sure it's within bounds
   if ($firstmessage > $#headers) {
      $firstmessage = $#headers - ($numberofheaders - 1);
   }
   if ($firstmessage < 0) {
      $firstmessage = 0;
   }
   my $lastmessage = $firstmessage + $numberofheaders - 1;
   if ($lastmessage > $#headers) {
       $lastmessage = $#headers;
   }

   my $base_url = "$scripturl?sessionid=$thissession&amp;sort=$sort&amp;folder=$folder";

   my $page_nb;
   if ($#headers > 0) {
      $page_nb = ($firstmessage+1) * ($#headers / $numberofheaders) / $#headers;
      $page_nb = int($page_nb) + 1 if ($page_nb != int($page_nb));
   } else {
      $page_nb = 1;
   }

   if ($total_size > 1048575){
      $total_size = int(($total_size/1048576)+0.5) . " MB";
   } elsif ($total_size > 1023) {
      $total_size =  int(($total_size/1024)+0.5) . " KB";
   } else {
      $total_size = $total_size . " B";
   }


### Begin printing purty header from Olivier :)
   print '<table border="0" align="center" width="95%" cellpadding="1" cellspacing="1">';
### first row - mbox name / message number
   print '<tr><td colspan="6" bgcolor=',$style{"titlebar"},' align="center"><table border="0" width="100%" cellpadding="0" cellspacing="0">',
   '<tr>',
   startform(-name=>'FolderForm'),
      hidden(-name=>'sessionid',
             -value=>$thissession,
             -override=>'1'),
      hidden(-name=>'sort',
             -value=>$sort,
             -override=>'1'),
      hidden(-name=>'action',
             -value=>'displayheaders',
             -override=>'1'),
      hidden(-name=>'firstmessage',
             -value=>$firstmessage,
             -override=>'1'),
    '<td align="left" width="33%">',
    '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},'><B>',
      popup_menu(-name=>'folder',
                 -"values"=>['INBOX','SENT','SAVED','TRASH'],
                 -default=>$folder,
                 -onChange=>'JavaScript:document.FolderForm.submit();',
                 -override=>'1'),
   '</B></font></td>',
   end_form(),
    '<td align=right width="33%"><font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3">',
    "<b>";
   if (defined($headers[0])) {
      print $firstmessage + 1, " - ", $lastmessage + 1, " of ", $#headers+1, " messages - ",
             "Folder size: $total_size</b></font></td></tr></table></td></tr>";
   } else {
      print "No messages</b></font></td></tr></table></td></tr>";
   }

# second row : navigation

   print '<tr><td bgcolor=',$style{"menubar"},' colspan="6"><table border="0" width="100%" cellpadding="0" cellspacing="0">';
   print '<td align=center><font face=',$style{"fontface"},' size=2>';

   print '<table border=0 width="100%">';
   print '<tr><td valign="middle" align="left">';
   print "<a href=\"$base_url&amp;action=composemessage&amp;firstmessage=$firstmessage\">Compose</a> | ";
   print "<a href=\"$prefsurl?sessionid=$thissession&amp;sort=$sort&amp;folder=$folder&amp;firstmessage=$firstmessage\">User prefs</a> | ";
   print "<a href=\"$prefsurl?action=editaddresses&amp;sessionid=$thissession&amp;sort=$sort&amp;folder=$folder&amp;firstmessage=$firstmessage\">Address book</a> | ";
   print "<a href=\"$base_url&amp;action=displayheaders&amp;firstmessage=$firstmessage\">Refresh</a> | ";
   print "<a href=\"$base_url&amp;action=logout&amp;firstmessage=$firstmessage\">Logout</a>";

   print '</td><td valign="middle" align="center">';

   print start_form();
   if ($firstmessage != 0) {
      print "<a href=\"$base_url&amp;action=displayheaders&amp;firstmessage=0\">";
      print "<img src=\"$image_url/first.gif\" border=\"0\" alt=\"&lt;&lt;\"></a>";
   } else {
      print "<img src=\"$image_url/first-grey.gif\" border=\"0\" alt=\"\">";
   }

   if (($firstmessage - $numberofheaders) >= 0) {
      print "<a href=\"$base_url&amp;action=displayheaders&amp;firstmessage=" , ($firstmessage + 1 - $numberofheaders) , "\">";
      print "<img src=\"$image_url/left.gif\" border=\"0\" alt=\"&lt;\"></a>";
   } else {
      print "<img src=\"$image_url/left-grey.gif\" border=\"0\" alt=\"\">";
   }

   print '[Page ';
      print hidden(-name=>'action',
		             -default=>'displayheaders',
		             -override=>'1');
      print hidden(-name=>'sessionid',
		             -default=>$thissession,
		             -override=>'1');
      print hidden(-name=>'sort',
		             -default=>$sort,
		             -override=>'1');
      print textfield(-name=>'custompage',
		                -default=>$page_nb,
		                -size=>'2',
		                -override=>'1');
   print ' of ', $page_total ,']';

   if (($firstmessage + $numberofheaders) <= $#headers) {
      print "<a href=\"$base_url&amp;action=displayheaders&amp;firstmessage=" , ($firstmessage + 1 + $numberofheaders) ,"\">";
      print "<img src=\"$image_url/right.gif\"  border=\"0\" alt=\"&gt;\"></a>";
   } else {
      print "<img src=\"$image_url/right-grey.gif\" border=\"0\" alt=\"\">";
   }

   if (($firstmessage + $numberofheaders) <= $#headers) {
      print "<a href=\"$base_url&amp;action=displayheaders&amp;custompage=",
            "$page_total\">";
      print "<img src=\"$image_url/last.gif\" border=\"0\" alt=\"&gt;&gt;\"></a>";
   } else {
      print "<img src=\"$image_url/last-grey.gif\" border=\"0\" alt=\"\">";
   }

   print '</td>', end_form(), '<td valign="middle" align="right">';
   # delete button
   if ($folder eq 'TRASH') {
      print start_form(-onSubmit=>"return confirm('Are you sure you want to delete the selected messages?')",
	   	              -name=>'Formdel');
   } else {
      print start_form(-onSubmit=>"return confirm('Are you sure you want to send the selected messages to the trash?')",
	   	              -name=>'Formdel');
   }
   print hidden(-name=>'action',
	   -default=>'deletemessage',
	   -override=>'1');
   print hidden(-name=>'sessionid',
	             -default=>$thissession,
	             -override=>'1');
   print hidden(-name=>'firstmessage',
	             -default=>$firstmessage +1,
	             -override=>'1');
   print hidden(-name=>'sort',
                -default=>$sort,
                -override=>'1');
   print hidden(-name=>'folder',
                -default=>$folder,
                -override=>'1');

   print 'Check all: <input name="allbox" type="checkbox" value="1" onClick="CheckAll();"> | ';
   if ($folder eq 'TRASH') {
      print submit('Delete');
   } else {
      print submit('Trash');
   }

   print '</td></tr></table>';
   print '</td><td>&nbsp;</td>';
   print '</tr></table></td></tr>';
### Spacing
   print '<tr><td colspan="6">&nbsp;</td></tr>';
      print '<tr><td valign="middle" width="50" bgcolor=',$style{"columnheader"},'><B>Status</B></td>';
      print '<td valign="middle" width="150" bgcolor=',$style{"columnheader"},'><B>';
      print "<a href=\"$scripturl?action=displayheaders&amp;firstmessage=",
      $firstmessage+1,"&amp;sessionid=$thissession&amp;folder=$folder&amp;sort=";

      if ($sort eq "date") {
         print "date_rev\">Date <IMG SRC=\"$image_url/up.gif\" width=\"12\"
                height=\"12\" border=\"0\" alt=\"^\"></a></B></td>";
      } elsif ($sort eq "date_rev") {
         print "date\">Date <IMG SRC=\"$image_url/down.gif\" width=\"12\"
                height=\"12\" border=\"0\" alt=\"v\"></a></B></td>";
      } else {
         print "date\">Date</a></B></td>";
      }

      print '<td valign="middle" width="150" bgcolor=',$style{"columnheader"},'><B>';
      print "<a href=\"$scripturl?action=displayheaders&amp;firstmessage=",
      $firstmessage+1,"&amp;sessionid=$thissession&amp;folder=$folder&amp;sort=";

      if ($sort eq "sender") {
         print "sender_rev\">Sender <IMG SRC=\"$image_url/down.gif\" width=\"12\"
                height=\"12\" border=\"0\" alt=\"v\"></a></B></td>";
      } elsif ($sort eq "sender_rev") {
         print "sender\">Sender <IMG SRC=\"$image_url/up.gif\" width=\"12\"
                height=\"12\" border=\"0\" alt=\"^\"></a></B></td>";
      } else {
         print "sender\">Sender</a></B></td>";
      }

      print '<td valign="middle" width="350" bgcolor=',$style{"columnheader"},'><B>';
      print "<a href=\"$scripturl?action=displayheaders&amp;firstmessage=",
      $firstmessage+1,"&amp;sessionid=$thissession&amp;folder=$folder&amp;sort=";

      if ($sort eq "subject") {
         print "subject_rev\">Subject <IMG SRC=\"$image_url/down.gif\" width=\"12\"
                height=\"12\" border=\"0\" alt=\"v\"></a></B></td>";
      } elsif ($sort eq "subject_rev") {
         print "subject\">Subject <IMG SRC=\"$image_url/up.gif\" width=\"12\"
                height=\"12\" border=\"0\" alt=\"^\"></a></B></td>";
      } else {
         print "subject\">Subject</a></B></td>";
      }

      print '<td valign="middle" width="50" bgcolor=',$style{"columnheader"},'><B>';
      print "<a href=\"$scripturl?action=displayheaders&amp;firstmessage=",
      $firstmessage+1,"&amp;sessionid=$thissession&amp;folder=$folder&amp;sort=";

      if ($sort eq "size") {
         print "size_rev\">Size <IMG SRC=\"$image_url/up.gif\" width=\"12\"
                height=\"12\" border=\"0\" alt=\"^\"></a></B></td>";
      } elsif ($sort eq "size_rev") {
         print "size\">Size <IMG SRC=\"$image_url/down.gif\" width=\"12\"
                height=\"12\" border=\"0\" alt=\"v\"></a></B></td>";
      } else {
         print "size\">Size</a></B></td>";
      }
      if ($folder eq 'TRASH') {
         print '<td width="50" bgcolor=',$style{"columnheader"},'><B>Delete</B></td></tr><tr>';
      } else {
         print '<td width="50" bgcolor=',$style{"columnheader"},'><B>Trash</B></td></tr><tr>';
      }
      foreach my $messnum ($firstmessage .. $lastmessage) {
### Stop when we're out of messages!
         last if !(defined($headers[$messnum]));

         ${$headers[$messnum]}{subject} =~ s/</&lt;/g;
         ${$headers[$messnum]}{subject} =~ s/>/&gt;/g;

         if ( $messnum % 2 ) {
            $bgcolor = $style{"tablerow_light"};
         } else {
            $bgcolor = $style{"tablerow_dark"};
         }

         $message_size = ${$headers[$messnum]}{messagesize};
### Round message size and change to an appropriate unit for display
         if ($message_size > 1048575){
            $message_size = int(($message_size/1048576)+0.5) . "MB";
         } elsif ($message_size > 1023) {
            $message_size =  int(($message_size/1024)+0.5) . "KB";
         }

         $status = "<B>".($messnum+1)."</B> ";
### Choose status icons based on Status: line and type of encoding
         unless ( ${$headers[$messnum]}{status} =~ /r/i ) {
            $status .= "<img src=\"$image_url/new.gif\">";
         }

         if ( ${$headers[$messnum]}{content_type} =~ /^multipart/i ) {
            $status .= "<img src=\"$image_url/attach.gif\">";
         }

         print "<td valign=\"middle\" width=\"50\" bgcolor=$bgcolor>$status&nbsp;</td>";

         print "<td valign=\"middle\" width=\"150\" bgcolor=$bgcolor>";
         print ${$headers[$messnum]}{date},'</td>';
         print "<td valign=\"middle\" width=\"150\" bgcolor=$bgcolor>",
                ${$headers[$messnum]}{from},'</td>';
         print "<td valign=\"middle\" width=\"350\" bgcolor=$bgcolor>",
               "<a href=\"$scripturl?action=readmessage&amp;firstmessage=",
               $firstmessage+1,"&amp;sessionid=$thissession&amp;status=",
               ${$headers[$messnum]}{status},"&amp;folder=$folder&amp;sort=$sort&amp;headers=",
               ($prefs{"headers"} || 'simple'), "&amp;message_id=",
               ${$headers[$messnum]}{message_id},'">',
               ${$headers[$messnum]}{subject},'</a></td>';

         print "<td valign=\"middle\" width=\"40\" bgcolor=$bgcolor>";
         print $message_size . "</td>";

         print "<td align=\"center\" valign=\"middle\" width=\"50\" bgcolor=$bgcolor>";
         print checkbox(-name=>'message_ids',
                        -value=>${$headers[$messnum]}{message_id},
                        -label=>'');
         print '</td>';

         print '</tr>';
      }

      print end_form();
      print '</table>';

      print '</td></tr></table>';

      print '<script language="JavaScript">
             <!--
             function CheckAll()
             {
                for (var i=0;i<document.Formdel.elements.length;i++)
                {
                   var e = document.Formdel.elements[i];
                   if (e.name != "allbox")
                   e.checked = document.Formdel.allbox.checked;
                }
             }
             //-->

             </script>';

   printfooter();
}
############### END DISPLAYHEADERS ##################

################# READMESSAGE ####################
sub readmessage {
   verifysession();
   printheader();
   my $messageid = param("message_id");
   my %message = %{&getmessage($user,$messageid)};
   my $headers = param("headers") || 'simple';
   unless ($message{status} =~ /r/i) {
      updatestatus($user,$messageid,"R");
   }
   if (%message) {
### these will hold web-ified headers
      my ($from, $replyto, $to, $cc, $subject, $body);
      $from = $message{from} || '';
      $from =~ s/</&lt;/g;
      $from =~ s/>/&gt;/g;
      $replyto = $message{replyto} || '';
      $replyto =~ s/</&lt;/g;
      $replyto =~ s/>/&gt;/g;
      $to = $message{to} || '';
      $to =~ s/</&lt;/g;
      $to =~ s/>/&gt;/g;
      $cc = $message{cc} || '';
      $cc =~ s/</&lt;/g;
      $cc =~ s/>/&gt;/g;
      $subject = $message{subject} || '';
      $subject =~ s/</&lt;/g;
      $subject =~ s/>/&gt;/g;
### Handle mail programs that send the body of a message quoted-printable
      if ( ($message{contenttype} =~ /^text\//i) &&
           ($message{encoding} =~ /^quoted-printable/i) ) {
         $message{"body"} = decode_qp($message{"body"});
      }

      $body = $message{"body"} || '';
      $body =~ s/</&lt;/g;
      $body =~ s/>/&gt;/g;
      $body =~ s/\n/<BR>\n/g;
      $body =~ s/ {2}/ &nbsp;/g;
      $body =~ s/\t/ &nbsp;&nbsp;&nbsp;&nbsp;/g;

   my $base_url = "$scripturl?sessionid=$thissession&amp;firstmessage=" . ($firstmessage+1) .
                   "&amp;sort=$sort&amp;folder=$folder&amp;message_id=$messageid";
   my $base_url_noid = "$scripturl?sessionid=$thissession&amp;firstmessage=" . ($firstmessage+1) .
                   "&amp;sort=$sort&amp;folder=$folder";

##### Set up the message to go to after deletion.
   my $messageafterdelete;
   if (defined($message{"next"})) {
      $messageafterdelete = $message{"next"};
   } elsif (defined($message{"prev"})) {
      $messageafterdelete = $message{"prev"};
   }

   print '<table border="0" align="center" width="75%" cellpadding="1" cellspacing="1">';

### first row - mbox name / message nb

   print '<tr><td bgcolor=',$style{"titlebar"},' align="center"><table border="0" width="100%" cellpadding="0" cellspacing="0">',
   '<tr><td align="left" width="33%"><font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>MESSAGE DISPLAY</b></font>',
   '</td><td align=right width="33%"><font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3">',
   "<b>Message number " . $message{"number"} ."</b></font></td></tr></table></td></tr>";

### second row : navigation

   print '<tr><td bgcolor=',$style{"menubar"},'><table border="0" width="100%" cellpadding="0" cellspacing="0">';
   print '<td align=center><font face=',$style{"fontface"},' size=2>';

   print start_form();

   print '<table border=0 width="100%">';
   print '<tr><td valign="middle" align="left">';
   print "<a href=\"$base_url&amp;action=displayheaders\">Back to $folder</a> | ";
   unless ($folder eq 'SAVED') {
      print "<a href=\"$base_url_noid&amp;action=savemessage&amp&amp;message_ids=$messageid";
      if ($messageafterdelete) {
         print "&amp;messageafterdelete=1&amp;message_id=$messageafterdelete";
      }
      print '">Save</a> | ';
   }
   print "<a href=\"$base_url&amp;action=composemessage&amp;composetype=reply\">Reply</a> | ";
   print "<a href=\"$base_url&amp;action=composemessage&amp;composetype=replyall\">Reply all</a> | ";
   print "<a href=\"$base_url&amp;action=composemessage&amp;composetype=forward\">Forward</a> | ";
   print "<a href=\"$base_url_noid&amp;action=deletemessage&amp;message_ids=$messageid";
   if ($messageafterdelete) {
      print "&amp;messageafterdelete=1&amp;message_id=$messageafterdelete";
   }
   if ($folder eq 'TRASH') {
      print '">Delete</a> | ';
   } else {
      print '">Trash</a> | ';
   }
   print "<a href=\"$base_url&amp;action=logout\">Logout</a>";

   print '</td><td valign="middle" align="center">';

   if (defined($message{"prev"})) {
      print "<a href=\"$base_url_noid&amp;action=readmessage&amp;message_id=" . $message{"prev"}. "\">";
      print "<img src=\"$image_url/left.gif\" border=\"0\" alt=\"&lt;&lt;\"></a>";
   } else {
      print "<img src=\"$image_url/left-grey.gif\" border=\"0\" alt=\"\">";
   }

   print "  " . $message{"number"} . "  ";

   if (defined($message{"next"})) {
      print "<a href=\"$base_url_noid&amp;action=readmessage&amp;message_id=" . $message{"next"}. "\">";
      print "<img src=\"$image_url/right.gif\"  border=\"0\" alt=\"&gt;&gt;\"></a>";
   } else {
      print "<img src=\"$image_url/right-grey.gif\" border=\"0\" alt=\"\">";
   }


   print '</td><td valign="middle" align="right">';

   if ($headers eq "all") {
      print "<a href=\"$base_url&amp;action=readmessage&amp;message_id=$messageid&amp;headers=simple\">Simple headers</a>";
   } else {
      print "<a href=\"$base_url&amp;action=readmessage&amp;message_id=$messageid&amp;headers=all\">All headers</a>";
   }

   print '</td></tr></table>';
   print '</td><td>&nbsp;</td>';
   print '</tr></table></td></tr>';

   print '<tr><td>&nbsp;</td></tr>';

   print '<tr><td width="100%" valign="middle" bgcolor=',$style{"window_dark"},'>';

   if ($headers eq "all") {
      $message{"header"} =~ s/</&lt;/g;
      $message{"header"} =~ s/>/&gt;/g;
      $message{"header"} =~ s/\n/<BR>\n/g;
      $message{"header"} =~ s/ {2}/ &nbsp;/g;
      $message{"header"} =~ s/\t/ &nbsp;&nbsp;&nbsp;&nbsp;/g;
      $message{"header"} =~ s/\n([-\w]+?:)/\n<B>$1<\/B>/g;
      print $message{"header"};
   } else {
      print "<B>Date:</B> $message{date}<BR>\n";
      print "<B>From:</B> $from<BR>\n";
      if ($replyto) {
	      print "<B>Reply-to:</B> $replyto<BR>\n";
      }
      if ($to) {
	      print "<B>To:</B> $to<BR>\n";
      }
      if ($cc) {
	      print "<B>CC:</B> $cc<BR>\n";
      }
      if ($subject) {
	      print "<B>Subject:</B> $subject\n";
      }
   }
   print '</td></tr><tr><td width="100%" bgcolor=',$style{"window_light"},'>';
### Create automatic hyperlinks
   foreach (qw(http ftp nntp news gopher telnet)) {
      $body =~ s/($_:[\d|\w|\/|\.|\-|?|&|=|~]*[\d|\w|\/])([\b|\n| ]*)/<A HREF=\"$1\">$1<\/A>$2/gs;
   }
      $body =~ s/([\b|\n| ]+)(www\.[-\w\.]+\.[-\w]{2,3})([\b|\n| ]*)/$1<a href=\"http:\/\/$2\">$2<\/a>$3/gs;
      print $body;
# Handle the messages generated if sendmail is set up to send MIME error reports
      if ($message{contenttype} =~ /^multipart\/report/i) {
         foreach my $attnumber (0 .. $#{$message{attachment}}) {
            if (defined(${$message{attachment}[$attnumber]}{contents})) {
               ${$message{attachment}[$attnumber]}{contents} =~ s/</&lt;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/>/&gt;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/\n/<BR>\n/g;
               print ${$message{attachment}[$attnumber]}{contents},
                     hr();
            }
         }
      } elsif ($message{contenttype} =~ /^multipart/i) {
         foreach my $attnumber (0 .. $#{$message{attachment}}) {
            if (($attnumber == 0) &&
               (${$message{attachment}[$attnumber]}{contenttype} =~ /^text\/plain$/i)) {
               print hr();
               ${$message{attachment}[$attnumber]}{contents} =~ s/</&lt;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/>/&gt;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/\n/<BR>\n/g;
               foreach (qw(http ftp nntp news gopher telnet)) {
                  ${$message{attachment}[$attnumber]}{contents} =~
                  s/($_:[\d|\w|\/|\.|\-|?|&|=|~]*[\d|\w|\/])([\b|\n| ]*)/<A HREF=\"$1\">$1<\/A>$2/gs;
               }
               print ${$message{attachment}[$attnumber]}{contents},"<BR><BR>";
            } else {
            print "<table border=\"0\" align=\"center\" cellpadding=\"2\">
                   <tr><td colspan=\"2\" valign=\"middle\"
                   bgcolor=",$style{"attachment_dark"}," align=\"center\">Attachment $attnumber
                   </td></tr><td valign=\"middle\" bgcolor=",$style{"attachment_light"},
                   " align=\"center\">";
            print "Type: ",${$message{attachment}[$attnumber]}{contenttype},"<BR>";
            print "Filename: ",${$message{attachment}[$attnumber]}{filename},"<BR>";
            print "Encoding: ",${$message{attachment}[$attnumber]}{encoding};
            print '</td><td valign="middle" bgcolor=',$style{"attachment_light"},' align="center">';
            print start_form();
               print hidden(-name=>'action',
                            -default=>'viewattachment',
                            -override=>'1');
               print hidden(-name=>'sessionid',
                            -default=>$thissession,
                            -override=>'1');
               print hidden(-name=>'message_id',
                            -default=>$messageid,
                            -override=>'1');
               print hidden(-name=>'folder',
                            -default=>$folder,
                            -override=>'1');
               print hidden(-name=>'attachment_number',
                            -default=>$attnumber,
                            -override=>'1');
               print submit("Download");
            print end_form();
            print '</td></tr></table>';
            }
         }
      }

      print '</td></tr></table>';

   } else {
      print "What the heck? Message $messageid seems to be gone!";
   }
   printfooter();
}
############### END READMESSAGE ##################

############### COMPOSEMESSAGE ###################
sub composemessage {
   verifysession();
   my $messageid = param("message_id");
   my %message;
   my $from = $thissession;
   $from =~ s/\-session\-0.*$/\@$domainname/; # create from: address
   if ($prefs{"realname"}) {
      my $realname = $prefs{"realname"};
      $from =~ s/^(.+)$/$realname <$1>/;
   }
   my $escapedfrom = $from;
   $escapedfrom =~ s/</&lt;/g;
   $escapedfrom =~ s/>/&gt;/g;
   my $to = '';
   my $cc = '';
   my $bcc = '';
   my $subject = '';
   my $body = '';
   my $composetype = param("composetype");

   if ($composetype) {
      $to = param("to") || '';
      $subject = param("subject") || '';
      $body = param("body") || '';

      if (($composetype eq "reply") || ($composetype eq "replyall") ||
          ($composetype eq "forward") ) {
         %message = %{&getmessage($user,$messageid)};

### Handle mail programs that send the body of a message quoted-printable
         if ( ($message{contenttype} =~ /^text\//i) &&
            ($message{encoding} =~ /^quoted-printable/i) ) {
            $message{"body"} = decode_qp($message{"body"});
         }
         $body = $message{"body"} || '';
### If the first attachment is text, assume it's the body of a message
### in multi-part format
         if (($message{contenttype} =~ /^multipart/i) &&
            (defined(${$message{attachment}[0]}{contenttype})) &&
            (${$message{attachment}[0]}{contenttype} =~ /^text\/plain/i)) {
            if (${$message{attachment}[0]}{encoding} =~ /^quoted-printable/i) {
               ${$message{attachment}[0]}{contents} =
               decode_qp(${$message{attachment}[0]}{contents});
            }
            $body .= "\n" . ${$message{attachment}[0]}{contents};
         }
# Handle the messages generated if sendmail is set up to send MIME error reports
         if ($message{contenttype} =~ /^multipart\/report/i) {
            foreach my $attnumber (0 .. $#{$message{attachment}}) {
               if (defined(${$message{attachment}[$attnumber]}{contents})) {
                  $body .= ${$message{attachment}[$attnumber]}{contents};
               }
            }
         }
      }

      if (($composetype eq "reply") || ($composetype eq "replyall")) {
         $subject = $message{"subject"} || '';
         $subject = "Re: " . $subject unless ($subject =~ /^re:/i);
         if (defined($message{"replyto"})) {
            $to = $message{"replyto"} || '';
         } else {
            $to = $message{"from"} || '';
         }
         if ($composetype eq "replyall") {
            $to .= "," . $message{"to"} if (defined($message{"to"}));
            $to .= "," . $message{"cc"} if (defined($message{"cc"}));
         }

         $body = "\n" . $body;
         $body =~ s/\n/\n\> /g;
         $body = "\n\n" . $body;
      }

      if ($composetype eq "forward") {
         $subject = $message{"subject"} || '';
         $subject = "Fw: " . $subject unless ($subject =~ /^fw:/i);
         $body = "\n\n------------- Forwarded message follows -------------\n\n$body";
      }

   }
   if (defined($prefs{"signature"})) {
      $body .= "\n\n".$prefs{"signature"};
   }
   printheader();
   print '<table border="0" align="center" width="90%" cellpadding="1" cellspacing="1">';

   print '<tr><td colspan="2" bgcolor=',$style{"titlebar"},' align="left">',
   '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>COMPOSE MESSAGE</b></font>',
   '</td></tr><tr><td colspan="2" bgcolor=',$style{"menubar"},' align="left">';
   print "[ <a href=\"$scripturl?action=displayheaders&amp;sessionid=$thissession&amp;folder=$folder&amp;sort=$sort&amp;firstmessage=$firstmessage\">Back to $folder</a> ]";
   print '</td></tr>';
### Spacing
   print '<tr><td colspan="2">&nbsp;</td></tr>';
   print start_multipart_form(-name=>'composeform');
   print '<tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">';

   print '<B>From:</B></td>
         <td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>', $escapedfrom;
   print '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">';
   print hidden(-name=>'action',
                -default=>'sendmessage',
                -override=>'1');
   print hidden(-name=>'sessionid',
                -default=>$thissession,
                -override=>'1');
   print hidden(-name=>'sort',
                -default=>$sort,
                -override=>'1');
   print hidden(-name=>'firstmessage',
                -default=>$firstmessage,
                -override=>'1');
   print hidden(-name=>'folder',
                -default=>$folder,
                -override=>'1');
   print '<a href="Javascript:GoAddressWindow(',"'to'", ')"><B>To:</B></a></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>',
          textfield(-name=>'to',
                    -default=>$to,
                    -size=>'70',
                    -override=>'1'),
         '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">',
         '<a href="Javascript:GoAddressWindow(',"'cc'", ')"><B>CC:</B></a></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>',
          textfield(-name=>'cc',
                    -default=>$cc,
                    -size=>'70',
                    -override=>'1'),
         '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">',
         '<a href="Javascript:GoAddressWindow(',"'bcc'", ')"><B>BCC:</B></a></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>',
          textfield(-name=>'bcc',
                    -default=>$bcc,
                    -size=>'70',
                    -override=>'1'),
         '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">',
         '<B>Reply-To:</B></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>',
          textfield(-name=>'replyto',
                    -default=>$prefs{"replyto"} || '',
                    -size=>'70',
                    -override=>'1'),
         '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">',
         '<B>Attachment:</B></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>',
          filefield(-name=>'attachment',
                    -default=>'',
                    -size=>'60',
                    -override=>'1'),
         '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">',
         '<B>Subject:</B></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>',
          textfield(-name=>'subject',
                    -default=>$subject,
                    -size=>'70',
                    -override=>'1');
   print '</td></tr><tr><td colspan="2" bgcolor=',$style{"window_light"},'>',
          textarea(-name=>'body',
                   -default=>$body,
                   -rows=>'10',
                   -columns=>'76',
                   -wrap=>'hard',
                   -override=>'1'),'</td></tr><tr><td align="left" valign="top">',
                   submit("Send");

   print '</td>', end_form();

   print start_form();
   if (param("message_id")) {
      print hidden(-name=>'action',
                   -default=>'readmessage',
                   -override=>'1');
      print hidden(-name=>'firstmessage',
                   -default=>$firstmessage +1,
                   -override=>'1');
      print hidden(-name=>'sort',
                   -default=>$sort,
                   -override=>'1');
      print hidden(-name=>'folder',
                   -default=>$folder,
                   -override=>'1');
      print hidden(-name=>'headers',
                   -default=>$prefs{"headers"} || 'simple',
                   -override=>'1');
      print hidden(-name=>'sessionid',
                   -default=>$thissession,
                   -override=>'1');
      print hidden(-name=>'message_id',
                   -default=>param("message_id"),
                   -override=>'1');
   } else {
      print hidden(-name=>'action',
                   -default=>'displayheaders',
                   -override=>'1');
      print hidden(-name=>'firstmessage',
                   -default=>$firstmessage +1,
                   -override=>'1');
      print hidden(-name=>'sort',
                   -default=>$sort,
                   -override=>'1');
      print hidden(-name=>'folder',
                   -default=>$folder,
                   -override=>'1');
      print hidden(-name=>'sessionid',
                   -default=>$thissession,
                   -override=>'1');
   }
   print '<td align="left" valign="top">',
         submit("Cancel"),
         '</td></tr></table>';
   print end_form();
   print '<script language="JavaScript">
   <!--
   if (self.focus != null)
      self.focus();

   function OnLoadHandler()
   {
      document.composeform.to.focus();
   }

   function GoAddressWindow(toccbcc)
   {
	   var url = "',$prefsurl,'?action=addressbook&sessionid=',
	   $thissession,'&field=" + toccbcc;
	   if (toccbcc == "to")
	      url += "&preexisting=" + escape (document.composeform.to.value);
	   else if (toccbcc == "cc")
	      url += "&preexisting=" + escape (document.composeform.cc.value);
	   else if (toccbcc == "bcc")
	      url += "&preexisting=" + escape (document.composeform.bcc.value);	
	
	   var hWnd = window.open(url,"HelpWindow","width=300,height=360,resizable=yes,scrollbars=yes");
	   if ((document.window != null) && (!hWnd.opener))
		   hWnd.opener = document.window;
   }

   //-->
   </script>';
   printfooter();
}
############# END COMPOSEMESSAGE #################

############### SENDMESSAGE ######################
sub sendmessage {
   verifysession();
   my $messagecontents = "From NeoMail-saved-message-creator\n"; # assembled into the message for sent-items
   my $date = localtime();
   my @datearray = split(/ +/, $date);
   $date = "$datearray[0], $datearray[2] $datearray[1] $datearray[4] $datearray[3] $timeoffset";
   my $from = $thissession;
   my $realname = $prefs{"realname"} || '';
   $from =~ s/\-session\-0.*$/\@$domainname/; # create from: address
   $from =~ s/[\||'|"|`]/ /g;  # Get rid of shell escape attempts
   $realname =~ s/[\||'|"|`]/ /g;  # Get rid of shell escape attempts
   if ($realname =~ /^(.+)$/) {
      $realname = '"'.$1.'"';
   }
   my $to = param("to");
   my $cc = param("cc");
   my $bcc = param("bcc");
   my $subject = param("subject");
   my $body = param("body");
   $body =~ s/\r//g;  # strip ^M characters from message. How annoying!
   my $attachment = param("attachment");
### Trim the path info from the filename
   my $attname = $attachment;
   $attname =~ s/^.*\\//;
   $attname =~ s/^.*\///;
   $attname =~ s/^.*://;

   open (SENDMAIL, "|" . $sendmail . " -oem -oi -F '$realname' -f '$from' -t 1>&2") or
      neomailerror("Can't run $sendmail!");
   print SENDMAIL "From: $realname <$from>\n";
   $messagecontents .= "From: $realname <$from>\n";
   print SENDMAIL "To: $to\n";
   $messagecontents .= "To: $to\n";
   if ($cc) {
      print SENDMAIL "CC: $cc\n";
      $messagecontents .= "CC: $cc\n";
   }
   if ($bcc) {
      print SENDMAIL "Bcc: $bcc\n";
      $messagecontents .= "Bcc: $bcc\n";
   }
   if ($prefs{"replyto"}) {
      print SENDMAIL "Reply-To: ",$prefs{"replyto"},"\n";
      $messagecontents .= "Reply-To: ".$prefs{"replyto"}."\n";
   }
   print SENDMAIL "Subject: $subject\n";
   $messagecontents .= "Subject: $subject\n";
   print SENDMAIL "X-Mailer: NeoMail $version\n";
   $messagecontents .= "X-Mailer: NeoMail $version\n";
   print SENDMAIL "X-IPAddress: $ENV{REMOTE_ADDR}\n";
   $messagecontents .= "X-IPAddress: $ENV{REMOTE_ADDR}\n";
   $messagecontents .= "Message-Id: <NeoMail-saved-".rand().">\nDate: ".
                       "$date\nStatus: R\n";
   if ($attachment) {
      no strict 'refs';
      my $boundary = "----=NEOMAIL_ATT_" . rand();
      my $attcontents = '';
      while (<$attachment>) {
         $attcontents .= $_;
      }
      $attcontents = encode_base64($attcontents);
      print SENDMAIL "MIME-Version: 1.0\n";
      print SENDMAIL "Content-Type: multipart/mixed;\n";
      print SENDMAIL "\tboundary=\"$boundary\"\n\n";
      print SENDMAIL "This is a multi-part message in MIME format.\n\n";
      print SENDMAIL "--$boundary\n";
      print SENDMAIL "Content-Type: text/plain; charset=US-ASCII\n\n";
      print SENDMAIL $body;
      $body =~ s/^From />From /gm;
      print SENDMAIL "\n\n--$boundary\n";
      print SENDMAIL "Content-Type: ",${uploadInfo($attachment)}{'Content-Type'} || 'text/plain',";\n";
      print SENDMAIL "\tname=\"$attname\"\nContent-Transfer-Encoding: base64\n\n";
      print SENDMAIL "$attcontents\n--$boundary--";
      $messagecontents .= "MIME-Version: 1.0\nContent-Type: multipart/mixed;\n".
                          "\tboundary=\"$boundary\"\n\nThis is a multi-part message in MIME format.\n\n".
                          "--$boundary\nContent-Type: text/plain; charset=US-ASCII\n\n$body\n\n--$boundary\n".
                          "Content-Type: ".(${uploadInfo($attachment)}{'Content-Type'} || 'text/plain').";\n".
                          "\tname=\"$attname\"\nContent-Transfer-Encoding: base64\n\n".
                          "$attcontents\n--$boundary--\n\n";
   } else {
      print SENDMAIL "\n$body\n";
      $body =~ s/^From />From /gm;
      $messagecontents .= "\n$body\n\n";
   }

   close(SENDMAIL) or senderror();
   open (SENT, ">>$userprefsdir$user/SENT") or
      neomailerror("There was a problem opening your SENT folder!");
      unless (flock(SENT, 2)) {
         neomailerror("Can't get write lock on SENT!");
      }
   print SENT "$messagecontents\n";
   close (SENT) or neomailerror ("Couldn't close SENT!");
   displayheaders();
}

sub senderror {
   printheader();
   print '<BR><BR><BR><BR><BR><BR>';
   print '<table border="0" align="center" width="25%" cellpadding="0" cellspacing="0">';

   print '<tr><td bgcolor=',$style{"titlebar"},' align="left">',
         '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>INVALID LOGIN</b></font>',
         '</td></tr>';
   print '<tr><td valign="middle" align="center" bgcolor=',$style{"window_light"},'>';
   print "Sorry, there was a problem sending your message.  Please
          click your browser's Back button, check your message, and
          try again.  If the problem persists, contact the author at
          neorants\@users.sourceforge.net.";
   print '</td></tr></table>';
   printfooter();
   exit 0;
}
############## END SENDMESSAGE ###################

################ VIEWATTACHMENT ##################
sub viewattachment {
   verifysession();
   my %message = %{&getmessage($user,param("message_id"))};
   if (%message) {
      my $attnumber = param("attachment_number");
      my $attachment;
      if (${$message{attachment}[$attnumber]}{encoding} =~ /^base64$/i) {
         $attachment = decode_base64(${$message{attachment}[$attnumber]}{contents});
      } elsif (${$message{attachment}[$attnumber]}{encoding} =~ /^quoted-printable$/i) {
         $attachment = decode_qp(${$message{attachment}[$attnumber]}{contents});
      } else { ## Guessing it's 7-bit, at least sending SOMETHING back! :)
         $attachment = ${$message{attachment}[$attnumber]}{contents};
      }
      my $length = length($attachment);
      print "Content-Length: $length\n";
      print "Content-Transfer-Coding: binary\n";
      print "Connection: close\n";
      print "Content-Type: ${$message{attachment}[$attnumber]}{contenttype}; name=\"${$message{attachment}[$attnumber]}{filename}\"\n";
      unless (${$message{attachment}[$attnumber]}{contenttype} =~ /^text\//i) {
         print "Content-Disposition: attachment; filename=\"${$message{attachment}[$attnumber]}{filename}\"\n";
      }
      print "\n";
      print $attachment;
   } else {
      printheader();
      print "What the heck? Message seems to be gone!";
      printfooter();
   }
}
##################################################

################## GETHEADERS #######################
sub getheaders {
   my $username = shift;
   my $spool = '';
   my @message = ();
   my $currentheader;
   my $currentfile = '';
   my $messagesize = 0;
   my $spoolfile;
   my $regexpmessnum = $firstmessage + 1;
   if ($folder eq 'INBOX') {
      if ($homedirspools eq "yes") {
         $spoolfile = "$homedir/$username/$homedirspoolname";
      } else {
         $spoolfile = "$mailspooldir/$username";
      }
   } else {
      $spoolfile = "$userprefsdir$user/$folder";
   }

   open (SPOOL, $spoolfile) or return \@message;
   while (<SPOOL>) {
      $spool .= $_;
   }
   close (SPOOL);

   @message = split(/\nFrom /, $spool);

   if ( (defined($message[0])) && ((split(/\n\r*\n/, $message[0]))[0] =~
      /DON'T DELETE THIS MESSAGE.+\nX-IMAP:/s) ) {
      shift @message;  # Remove those pesky IMAP messages :)
   }

   foreach my $messnum (0 .. $#message) {

      my %header = qw(from    N/A
                      date    N/A
                      subject N/A
                      message_id N/A
                      content_type N/A
                     );
      $header{status} = '';
      my $lastline = 'NONE';

      ($currentheader, my $junk) = split(/\n\r*\n/, $message[$messnum]);
      $messagesize = length($message[$messnum]);
      $total_size += $messagesize;

      foreach (split(/\n/, $currentheader)) {
         if (/^\s/) {
            if    ($lastline eq 'FROM') { $header{from} .= $_ }
            elsif ($lastline eq 'DATE') { $header{date} .= $_ }
            elsif ($lastline eq 'SUBJ') { $header{subject} .= $_ }
         } elsif (/^from:\s+(.+)$/ig) {
            $header{from} = $1;
            $lastline = 'FROM';
         } elsif (/^date:\s+(.+)$/ig) {
            $header{date} = $1;
            $lastline = 'DATE';
         } elsif (/^subject:\s+(.+)$/ig) {
            $header{subject} = $1;
            $lastline = 'SUBJ';
         } elsif (/^message-id:\s+(.+)$/ig) {
            $header{message_id} = $1;
            $header{message_id} =~ s/[<>#&=\?]//g;
         } elsif (/^content-type:\s+(.+)$/ig) {
            $header{content_type} = $1;
            $lastline = 'NONE';
         } elsif (/^status:\s+(.+)$/ig) {
            $header{status} = $1;
            $lastline = 'NONE';
         } else {
            $lastline = 'NONE';
         }
      }

      ($header{from} =~ s/^"?(.+?)"?\s+<(.*)>$/<a href="$scripturl\?action=composemessage&amp;sort=$sort&amp;folder=$folder&amp;firstmessage=$regexpmessnum&amp;sessionid=$thissession&amp;composetype=sendto&amp;to=$2">$1<\/a>/) ||
         ($header{from} =~ s/(.+)/<a href="$scripturl\?action=composemessage&amp;sort=$sort&amp;folder=$folder&amp;firstmessage=$regexpmessnum&amp;sessionid=$thissession&amp;composetype=sendto&amp;to=$1">$1<\/a>/);
      my @datearray = split(/\s/, $header{date});
      if ($datearray[0] =~ /[A-Za-z,]/) {
         shift @datearray; # Get rid of the day of the week
      }
      $header{date} = "$month{$datearray[1]}/$datearray[0]/$datearray[2] $datearray[3] $datearray[4]";
      $header{messagesize} = $messagesize;
      $message[$messnum] = \%header;
   }

   if ( $sort eq 'date' ) {
      @message = sort by_date @message;
   } elsif ( $sort eq 'date_rev' ) {
      @message = reverse(sort by_date @message);
   } elsif ( $sort eq 'sender' ) {
      @message = sort by_sender @message;
   } elsif ( $sort eq 'sender_rev' ) {
      @message = reverse(sort by_sender @message);
   } elsif ( $sort eq 'size' ) {
      @message = sort by_size @message;
   } elsif ( $sort eq 'size_rev' ) {
      @message = reverse(sort by_size @message);
   } elsif ( $sort eq 'subject' ) {
      @message = sort by_subject @message;
   } else {
      @message = reverse(sort by_subject @message);
   }

   return \@message;
}

sub by_date {
   (my $datea, my $timea, my $offseta) = split(/\s/, ${$a}{date});
   (my $dateb, my $timeb, my $offsetb) = split(/\s/, ${$b}{date});

   $offseta = substr($offseta,0,3);
   $offsetb = substr($offsetb,0,3);

   my @datearraya = split(/\//, $datea);
   my @timearraya = split(/:/, $timea);
   my @datearrayb = split(/\//, $dateb);
   my @timearrayb = split(/:/, $timeb);

   $timearraya[0] -= $offseta;
   $timearrayb[0] -= $offsetb;

   $datearrayb[2] <=> $datearraya[2]
      or
   $datearrayb[0] <=> $datearraya[0]
      or
   $datearrayb[1] <=> $datearraya[1]
      or
   $timearrayb[0] <=> $timearraya[0]
      or
   $timearrayb[1] <=> $timearraya[1]
      or
   $timearrayb[2] <=> $timearraya[2];
}

sub by_sender {
   my $sendera = ${$a}{from};
   my $senderb = ${$b}{from};

   lc($sendera) cmp lc($senderb);
}

sub by_subject {
   my $subjecta = ${$a}{subject};
   my $subjectb = ${$b}{subject};

   lc($subjecta) cmp lc($subjectb);
}

sub by_size {
   ${$b}{messagesize} <=> ${$a}{messagesize};
}
#################### END GETHEADERS #######################

#################### GETMESSAGE ###########################
sub getmessage {
   my $username = shift;
   my $spool = '';
   my $spoolfile;
   my $currentfile = '';
   my $messageid = shift;

   my %message = ();
   my @attachment = ();

   my ($currentheader, $currentbody, $currentfrom, $currentdate,
       $currentsubject, $currentid, $currenttype, $currentto, $currentcc,
       $currentreplyto, $currentencoding, $currentstatus);
   if ($folder eq 'INBOX') {
      if ($homedirspools eq "yes") {
         $spoolfile = "$homedir/$username/$homedirspoolname";
      } else {
         $spoolfile = "$mailspooldir/$username";
      }
   } else {
      $spoolfile = "$userprefsdir$user/$folder";
   }

   open (SPOOL, $spoolfile) or return \%message;
   while (<SPOOL>) {
      $spool .= $_;
   }
   close (SPOOL);

   foreach my $currmessage (split(/\nFrom /, $spool)) {
      unless ($currmessage =~ /^From /) {
         $currmessage = "From " . $currmessage;
      }
      $currentheader = $currentbody = $currentfrom = $currentdate =
      $currentsubject = $currentid = $currenttype = $currentto =
      $currentcc = $currentreplyto = $currentencoding = 'N/A';
      $currentstatus = '';
      ($currentheader, $currentbody) = split(/\n\r*\n/, $currmessage, 2);
      my $lastline = 'NONE';
      foreach (split(/\n/, $currentheader)) {
         if (/^\s/) {
            if    ($lastline eq 'FROM') { $currentfrom .= $_ }
            elsif ($lastline eq 'REPLYTO') { $currentreplyto .= $_ }
            elsif ($lastline eq 'DATE') { $currentdate .= $_ }
            elsif ($lastline eq 'SUBJ') { $currentsubject .= $_ }
            elsif ($lastline eq 'TYPE') { $currenttype .= $_ }
            elsif ($lastline eq 'ENCODING') { $currentencoding .= $_ }
            elsif ($lastline eq 'TO')   { $currentto .= $_ }
            elsif ($lastline eq 'CC')   { $currentcc .= $_ }
         } elsif (/^from:\s+(.+)$/ig) {
            $currentfrom = $1;
            $lastline = 'FROM';
         } elsif (/^reply-to:\s+(.+)$/ig) {
            $currentreplyto = $1;
            $lastline = 'REPLYTO';
         } elsif (/^to:\s+(.+)$/ig) {
            $currentto = $1;
            $lastline = 'TO';
         } elsif (/^cc:\s+(.+)$/ig) {
            $currentcc = $1;
            $lastline = 'CC';
         } elsif (/^date:\s+(.+)$/ig) {
            $currentdate = $1;
            $lastline = 'DATE';
         } elsif (/^subject:\s+(.+)$/ig) {
            $currentsubject = $1;
            $lastline = 'SUBJ';
         } elsif (/^message-id:\s+(.+)$/ig) {
            $currentid = $1;
            $currentid =~ s/[<>#&=\?]//g;
         } elsif (/^content-type:\s+(.+)$/ig) {
            $currenttype = $1;
            $lastline = 'TYPE';
         } elsif (/^content-transfer-encoding:\s+(.+)$/ig) {
            $currentencoding = $1;
            $lastline = 'ENCODING';
         } elsif (/^status:\s+(.+)$/ig) {
            $currentstatus = $1;
            $lastline = 'NONE';
         } else {
            $lastline = 'NONE';
         }
      }

      last if ($currentid eq $messageid);
   }
   if ($currentid eq $messageid) { # We found the message
      if ($currenttype =~ /^multipart/i) {
         my $boundary = $currenttype;
         $boundary =~ s/.*boundary="?(.+?)"?$/$1/i;
         ($currentbody, my @attachments) = split(/\-\-$boundary/,$currentbody);
         my $attnum = -1;  # So that the first increment gives 0
         my $outerattnum = -1;
         foreach my $bound (0 .. $#attachments) {
            $outerattnum++;
            $attnum++;
            my %temphash;
            my ($attheader, $attcontents) = split(/\n\n/, $attachments[$outerattnum], 2);
            my $lastline='NONE';
            my ($attcontenttype, $attfilename, $attencoding);
            foreach (split(/\n/, $attheader)) {
               if (/^\s/) {
                  if ($lastline eq 'TYPE') { $attcontenttype .= $_ }
               } elsif (/^content-type:\s+(.+)$/ig) {
                  $attcontenttype = $1;
                  $lastline = 'TYPE';
               } elsif (/^content-transfer-encoding:\s+(.+)$/ig) {
                  $attencoding = $1;
                  $lastline = 'NONE';
               } else {
                  $lastline = 'NONE';
               }
            }

# Handle Outlook's funky "multipart inside multipart" encapsulation.  Leave
# it to MS to do something weird. TODO: Possibly implement recursion for
# deeper levels of multipart messages, to reduce code size?  Would have to
# avoid being exploited by someone sucking up all memory by deliberately
# sending messages with hundreds-of-levels deep attachments

            if ($attfilename || $attcontenttype) {
               if ($attcontenttype =~ /^multipart/i) {
                  my $boundary = $attcontenttype;
                  $boundary =~ s/.*boundary="(.*)".*/$1/i;
                  ($attcontents, my @attachments) = split(/\-\-$boundary/,$attcontents);
                  $attnum--; # avoid incrementing $attnum first time
                  foreach my $bound (0 .. $#attachments) {
                     last if ($attachments[$attnum + 1] =~ /^\-\-\n/);
                     $attnum++;
                     my %temphash;
                     my ($attheader, $attcontents) = split(/\n\n/, $attachments[$attnum], 2);
                     my $lastline='NONE';
                     my ($attcontenttype, $attfilename, $attencoding);
                     foreach (split(/\n/, $attheader)) {
                        if (/^\s/) {
                           if ($lastline eq 'TYPE') { $attcontenttype .= $_ }
                        } elsif (/^content-type:\s+(.+)$/ig) {
                           $attcontenttype = $1;
                           $lastline = 'TYPE';
                        } elsif (/^content-transfer-encoding:\s+(.+)$/ig) {
                           $attencoding = $1;
                           $lastline = 'NONE';
                        } else {
                           $lastline = 'NONE';
                        }
                     }
                     if ($attfilename || $attcontenttype) {
                        $attfilename = $attcontenttype;
                        $attcontenttype =~ s/^(.+);.*/$1/g;
                        unless ($attfilename =~ s/^.+name="(.+)".*/$1/ig) {
                           $attfilename = "Unknown.html";
                        }
                        $temphash{filename} = $attfilename;
                        $temphash{contenttype} = $attcontenttype;
                        $temphash{encoding} = $attencoding;
                        $temphash{contents} = $attcontents;
                        $attachment[$attnum] = \%temphash;
                     }
                  }
               } else {
                  $attfilename = $attcontenttype;
                  $attcontenttype =~ s/^(.+);.*/$1/g;
                  unless ($attfilename =~ s/^.+name="(.+)".*/$1/ig) {
                     $attfilename = "Unknown.html";
                  }
                  $temphash{filename} = $attfilename;
                  $temphash{contenttype} = $attcontenttype;
                  $temphash{encoding} = $attencoding;
                  $temphash{contents} = $attcontents;
                  $attachment[$attnum] = \%temphash;
               }
            }
         }
      }

      $message{"header"} = $currentheader;
      $message{"body"} = $currentbody;
      $message{from} = $currentfrom;
      $message{replyto} = $currentreplyto unless ($currentreplyto eq "N/A");
      $message{to} = $currentto unless ($currentto eq "N/A");
      $message{cc} = $currentcc unless ($currentcc eq "N/A");
      $message{date} = $currentdate;
      $message{subject} = $currentsubject;
      $message{status} = $currentstatus;
      $message{messageid} = $currentid;
      $message{contenttype} = $currenttype;
      $message{encoding} = $currentencoding;
      $message{attachment} = \@attachment;

      # Determine message's number and previous and next
      # message IDs.
      my @headers = @{&getheaders($username)};
      foreach my $messagenumber (0..$#headers) {
         if (${$headers[$messagenumber]}{message_id} eq $currentid) {
            $message{"prev"} = ${$headers[$messagenumber-1]}{message_id} if ($messagenumber > 0);
            $message{"next"} = ${$headers[$messagenumber+1]}{message_id} if ($messagenumber < $#headers);
            $message{"number"} = $messagenumber+1;
            last;
         }
      }
      return \%message;
   } else {
      return \%message;
   }
}
#################### END GETMESSAGE #######################

#################### UPDATESTATUS #########################
sub updatestatus {
   my $user = shift;
   my $messageid = shift;
   my $status = shift;

   my $spool = '';
   my $spoolfile;
   if ($homedirspools eq "yes") {
      $spoolfile = "$homedir/$user/$homedirspoolname";
   } else {
      $spoolfile = "$mailspooldir/$user";
   }

   my $currmessage;
   open (SPOOL, "+<$spoolfile") or neomailerror("Can't open $spoolfile!");
   unless (flock(SPOOL, 2)) {
      neomailerror("Can't get write lock on $spoolfile!");
   }
   while (<SPOOL>) {
      $spool .= $_;
   }
   seek (SPOOL, 0, 0) or neomailerror("Couldn't seek to the beginning of $spoolfile!");

   foreach $currmessage (split(/\nFrom /, $spool)) {
      my $currentmessageid = '';
      my ($currentheader, $currentbody) = split(/\n\r*\n/,$currmessage, 2);
      if ($currentheader =~ /^message-id:\s+(.+?)$/im) {
         $currentmessageid = $1;
         $currentmessageid =~ s/[<>#&=\?]//g;
      }
      if ($messageid =~ /^\Q$currentmessageid\E$/) {
         ($currentheader =~ s/^status:\s+(.*?)$/Status: $status$1/im) ||
         ($currentheader .= "\nStatus: $status");
      }
      if ($currentheader =~ /^From /) {
         print SPOOL $currentheader, "\n\n", $currentbody, "\n";
      } else {
         print SPOOL "From $currentheader", "\n\n", $currentbody, "\n";
      }
   }
   truncate(SPOOL, tell(SPOOL));
   close (SPOOL) or neomailerror("Can't close $spoolfile!");
}
################### END UPDATESTATUS ######################

#################### SAVEMESSAGE ########################
sub savemessage {
   verifysession();
   my @messageids = param("message_ids");
   my $messageids = join("\n", @messageids);
   my $spool = '';
   my $spoolfile;
   neomailerror ("You shouldn't be trying to save here!") if ($folder eq 'SAVED');

   if ($folder eq 'INBOX') {
      if ($homedirspools eq "yes") {
         $spoolfile = "$homedir/$user/$homedirspoolname";
      } else {
         $spoolfile = "$mailspooldir/$user";
      }
   } else {
      $spoolfile = "$userprefsdir$user/$folder";
   }

   my $currmessage;
   open (SPOOL, "+<$spoolfile") or neomailerror("Can't open $spoolfile!");
   unless (flock(SPOOL, 2)) {
      neomailerror("Can't get write lock on $spoolfile!");
   }
   while (<SPOOL>) {
      $spool .= $_;
   }
   seek (SPOOL, 0, 0) or neomailerror("Couldn't seek to the beginning of $spoolfile!");

   foreach $currmessage (split(/\nFrom /, $spool)) {
      my $currentmessageid = '';
      if ($currmessage =~ /^message-id:\s+(.+?)$/im) {
         $currentmessageid = $1;
         $currentmessageid =~ s/[<>#&=\?]//g;
      }
      if ($messageids =~ /^\Q$currentmessageid\E$/m) {
         open (SAVED, ">>$userprefsdir$user/SAVED") or
            neomailerror ("Couldn't open SAVED!");
            unless (flock(SAVED, 2)) {
               neomailerror("Can't get write lock on SAVED!");
            }
         if ($currmessage =~ /^From /) {
            print SAVED "$currmessage\n";
         } else {
            print SAVED "From $currmessage\n";
         }
         close (SAVED) or neomailerror("Can't close SAVED!");
      } else {
         if ($currmessage =~ /^From /) {
            print SPOOL "$currmessage\n";
         } else {
            print SPOOL "From $currmessage\n";
         }
      }
   }
   truncate(SPOOL, tell(SPOOL));
   close (SPOOL) or neomailerror("Can't close $spoolfile!");
   $messageids =~ s/\n/, /g;
   writelog("User saved messages - $messageids");
   if (param("messageafterdelete")) {
      readmessage();
   } else {
      displayheaders();
   }
}
#################### END SAVEMESSAGE #######################


#################### DELETEMESSAGE ########################
sub deletemessage {
   verifysession();

   my @messageids = param("message_ids");

   my $messageids = join("\n", @messageids);

   my $spool = '';
   my $spoolfile;
   if ($folder eq 'INBOX') {
      if ($homedirspools eq "yes") {
         $spoolfile = "$homedir/$user/$homedirspoolname";
      } else {
         $spoolfile = "$mailspooldir/$user";
      }
   } else {
      $spoolfile = "$userprefsdir$user/$folder";
   }

   my $currmessage;
   open (SPOOL, "+<$spoolfile") or neomailerror("Can't open $spoolfile!");
   unless (flock(SPOOL, 2)) {
      neomailerror("Can't get write lock on $spoolfile!");
   }
   while (<SPOOL>) {
      $spool .= $_;
   }
   seek (SPOOL, 0, 0) or neomailerror("Couldn't seek to the beginning of $spoolfile!");

   foreach $currmessage (split(/\nFrom /, $spool)) {
      my $currentmessageid = '';
      if ($currmessage =~ /^message-id:\s+(.+?)$/im) {
         $currentmessageid = $1;
         $currentmessageid =~ s/[<>#&=\?]//g;
      }
      if ($messageids =~ /^\Q$currentmessageid\E$/m) {
         unless ($folder eq 'TRASH') {
            open (TRASH, ">>$userprefsdir$user/TRASH") or
               neomailerror ("Couldn't open TRASH!");
               unless (flock(TRASH, 2)) {
                  neomailerror("Can't get write lock on TRASH!");
               }
            if ($currmessage =~ /^From /) {
               print TRASH "$currmessage\n";
            } else {
               print TRASH "From $currmessage\n";
            }
            close (TRASH) or neomailerror("Can't close TRASH!");
         }
      } else {
         if ($currmessage =~ /^From /) {
            print SPOOL "$currmessage\n";
         } else {
            print SPOOL "From $currmessage\n";
         }
      }
   }
   truncate(SPOOL, tell(SPOOL));
   close (SPOOL) or neomailerror("Can't close $spoolfile!");
   $messageids =~ s/\n/, /g;
   writelog("User deleted messages - $messageids");
   if (param("messageafterdelete")) {
      readmessage();
   } else {
      displayheaders();
   }
}
#################### END DELETEMESSAGE #######################

###################### ENCODING/DECODING ##############################
# Blatantly snatched from AtDot, which got this from Base64.pm
# Had to load $_[0] into my $unencoded to keep this from freezing the
# browser with attachments when running perl 5.005_3... worked fine
# on perl 5.004_4 without that change. Anyone know what happened?
sub encode_base64 ($;$)
{
    my $unencoded = $_[0];
    my $res = "";
    my $eol = $_[1];
    $eol = "\n" unless defined $eol;
    while ($unencoded =~ /(.{1,45})/gs) {
        $res .= substr(pack('u', $1), 1);
        chop($res);
    }
    $res =~ tr|` -_|AA-Za-z0-9+/|;               # `# help emacs
    # fix padding at the end
    my $padding = (3 - length($_[0]) % 3) % 3;
    $res =~ s/.{$padding}$/'=' x $padding/e if $padding;
    # break encoded string into lines of no more than 76 characters each
    if (length $eol) {
        $res =~ s/(.{1,76})/$1$eol/g;
    }
    $res;
}

sub decode_base64 ($)
{
    local($^W) = 0; # unpack("u",...) gives bogus warning in 5.00[123]

    my $str = shift;
    my $res = "";

    $str =~ tr|A-Za-z0-9+=/||cd;            # remove non-base64 chars
    $str =~ s/=+$//;                        # remove padding
    $str =~ tr|A-Za-z0-9+/| -_|;            # convert to uuencoded format
    while ($str =~ /(.{1,60})/gs) {
        my $len = chr(32 + length($1)*3/4); # compute length byte
        $res .= unpack("u", $len . $1 );    # uudecode
    }
    $res;
}

sub decode_qp ($)
{
    my $res = shift;
    $res =~ s/[ \t]+?(\r?\n)/$1/g;  # rule #3 (trailing space must be deleted)
    $res =~ s/=\r?\n//g;            # rule #5 (soft line breaks)
    $res =~ s/=([\da-fA-F]{2})/pack("C", hex($1))/ge;
    $res;
}
################### END ENCODING/DECODING ##########################

##################### FIRSTTIMEUSER ################################
sub firsttimeuser {
   printheader();
   print '<BR><BR><BR><BR><BR><BR>';
   print '<table border="0" align="center" width="40%" cellpadding="1" cellspacing="1">';

   print '<tr><td bgcolor=',$style{"titlebar"},' align="left">',
   '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>WELCOME TO NEOMAIL!</b></font>',
   '</td></tr><tr><td align="center" bgcolor=',$style{"window_light"},'>';
   print "<BR>Welcome to NeoMail!  It appears that this is your first time
          using NeoMail, so we need to gather some information about you
          to better configure NeoMail to suit your needs.  Please click
          continue to proceed to the NeoMail configuration screen.";
   print startform(-action=>"$prefsurl");
   print hidden(-name=>'sessionid',
                -default=>$thissession,
                -override=>'1');
   print hidden(-name=>'firsttimeuser',
                -default=>'yes',
                -override=>'1');
   print submit("Continue");
   print end_form();
   print '</td></tr></table>';
   printfooter();
}
################### END FIRSTTIMEUSER ##############################

###################### READPREFS #########################
sub readprefs {
   my ($key,$value);
   my %prefshash;
   if ( -f "$userprefsdir$user/config" ) {
      open (CONFIG,"$userprefsdir$user/config") or
         neomailerror("Can't open your user config file, but it exists!");
      while (<CONFIG>) {
         ($key, $value) = split(/=/, $_);
         chomp($value);
         if ($key eq 'style') {
            $value =~ s/\.//g;  ## In case someone gets a bright idea...
         }
         $prefshash{"$key"} = $value;
      }
      close (CONFIG) or neomailerror("Couldn't close your config file!");
   }
   if ( -f "$userprefsdir$user/signature" ) {
      $prefshash{"signature"} = '';
      open (SIGNATURE, "$userprefsdir$user/signature") or
         neomailerror("Can't open your signature, but file exists!");
      while (<SIGNATURE>) {
         $prefshash{"signature"} .= $_;
      }
      close (SIGNATURE) or neomailerror("Couldn't close your signature file!");
   }
   return \%prefshash;
}
##################### END READPREFS ######################

###################### READSTYLE #########################
sub readstyle {
   my ($key,$value);
   my $stylefile = $prefs{"style"} || 'Default';
   my %stylehash;
   unless ( -f "$stylesdir$stylefile") {
      $stylefile = 'Default';
   }
   open (STYLE,"$stylesdir$stylefile") or
      neomailerror("Can't open the style file: $stylefile!");
   while (<STYLE>) {
      if (/###STARTSTYLESHEET###/) {
         $stylehash{"css"} = '';
         while (<STYLE>) {
            $stylehash{"css"} .= $_;
         }
      } else {
         ($key, $value) = split(/=/, $_);
         chomp($value);
         $stylehash{"$key"} = $value;
      }
   }
   close (STYLE) or neomailerror("Couldn't close your style file!");
   return \%stylehash;
}
##################### END READSTYLE ######################

##################### WRITELOG ############################
sub writelog {
   unless ($logfile eq 'no') {
      open (LOGFILE,">>$logfile") or neomailerror("Couldn't open $logfile!");
      my $timestamp = localtime();
      my $logaction = shift;
      print LOGFILE "$timestamp - [$$] ($ENV{REMOTE_ADDR}) $logaction\n";
      close (LOGFILE);
   }
}
#################### END WRITELOG #########################

##################### NEOMAILERROR ##########################
sub neomailerror {
   printheader();
   print '<BR><BR><BR><BR><BR><BR>';
   print '<table border="0" align="center" width="40%" cellpadding="1" cellspacing="1">';

   print '<tr><td bgcolor=',$style{"titlebar"},' align="left">',
   '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>NEOMAIL ERROR</b></font>',
   '</td></tr><tr><td align="center" bgcolor=',$style{"window_light"},'>';
   print shift;
   print '</td></tr></table>';
   printfooter();
   exit 0;
}
################### END NEOMAILERROR #######################

##################### PRINTHEADER #########################
sub printheader {
   unless ($headerprinted) {
      $headerprinted = 1;
      my $background = $style{"background"};
      $background =~ s/"//g;
      print header(-pragma=>'no-cache'),
            start_html(-"title"=>"NeoMail version $version",
                       -author=>'emiller@hhs.net',
                       -BGCOLOR=>$background,
                       -BACKGROUND=>$bg_url);
      print '<style type="text/css">';
      print $style{"css"};
      print '</style>';
      print "<FONT FACE=",$style{"fontface"},">\n";
   }
}
################### END PRINTHEADER #######################

################### PRINTFOOTER ###########################
sub printfooter {
   print "<p align=\"center\"><FONT SIZE=\"1\"><BR>
          <a href=\"http://neomail.sourceforge.net\">
          NeoMail</a> version $version<BR>
          </FONT></FONT></p></BODY></HTML>";
}
################# END PRINTFOOTER #########################
