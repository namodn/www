#!/usr/bin/suidperl -wT
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

# maxabooksize - This is the maximum size, in kilobytes, that a user's address
#                book can grow to. This avoids a user filling up your server's
#                hard drive space by spamming garbage addressbook entries.
my $maxabooksize = 50;

# scripturl - The location (Relative to ServerRoot) of the CGI script, used in some
#             error messages to provide a link back to the login page
my $scripturl = '/cgi-bin/email.cgi';

# prefsurl - This is the location (relative to ServerRoot) of the user setup
#            and address book script.
my $prefsurl = '/cgi-bin/email-prefs.cgi';

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
   $sort = 'date';
}

my $folder;
if (param("folder")) {
   $folder = param("folder");
   neomailerror ("No such folder: $folder") unless ( ($folder eq 'INBOX') ||
      ($folder eq 'SENT') || ($folder eq 'SAVED') || ($folder eq 'TRASH') );
} else {
   $folder = "INBOX";
}

my $firsttimeuser = param("firsttimeuser") || ''; # Don't allow cancel if 'yes'

$sessiontimeout = $sessiontimeout/60/24; # convert to format expected by -M

# once we print the header, we don't want to do it again if there's an error
my $headerprinted = 0;

########################## MAIN ##############################
if (defined(param("action"))) {      # an action has been chosen
   my $action = param("action");
   if ($action =~ /^(\w+)$/) {
      $action = $1;
      if ($action eq "saveprefs") {
         saveprefs();
      } elsif ($action eq "addressbook") {
         addressbook();
      } elsif ($action eq "editaddresses") {
         editaddresses();
      } elsif ($action eq "importabook") {
         importabook();
      } elsif ($action eq "addaddress") {
         modaddress("add");
      } elsif ($action eq "deleteaddress") {
         modaddress("delete");
      }
   } else {
      neomailerror("Action has illegal characters!");
   }
} else {            # no action has been taken, display prefs page
   verifysession();

   my @styles;
   printheader();

### Get a list of valid style files
   opendir (STYLESDIR, $stylesdir) or
      neomailerror("Couldn't open $stylesdir directory for reading!");
   while (defined(my $currentstyle = readdir(STYLESDIR))) {
      unless ($currentstyle =~ /\./) {
         push (@styles, $currentstyle);
      }
   }
   @styles = sort(@styles);
   closedir(STYLESDIR) or
      neomailerror("Couldn't close $stylesdir directory!");
   print start_form();
   print '<table border="0" align="center" width="90%" cellpadding="1" cellspacing="1">';

   print '<tr><td colspan="2" bgcolor=',$style{"titlebar"},' align="left">',
         '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>USER PREFERENCES';
   if ($prefs{"realname"}) {
      print ' FOR ', uc($prefs{"realname"});
   }
   print '</b></font></td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">';

   print hidden(-name=>'action',
                -default=>'saveprefs',
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
   print '<B>Real Name:</B></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>',
          textfield(-name=>'realname',
                    -default=>$prefs{"realname"} || 'Your Name',
                    -size=>'40',
                    -override=>'1'),
         '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">',
         '<B>Reply-to:</B></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>',
          textfield(-name=>'replyto',
                    -default=>$prefs{"replyto"} || '',
                    -size=>'40',
                    -override=>'1'),
         '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">',
         '<B>Style:</B></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>';
   print popup_menu(-name=>'style',
                    -"values"=>\@styles,
                    -default=>$prefs{"style"} || 'Default',
                    -override=>'1'),
         '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">',
         '<B>Default sort:</B></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>';
   my %sortlabels = ('date'=>'Date (Newest first)',
                     'date_rev'=>'Date (Oldest first)',
                     'sender'=>'Sender (Alphabetical)',
                     'sender_rev'=>'Sender (Reverse alphabetical)',
                     'size'=>'Size (Largest first)',
                     'size_rev'=>'Size (Smallest first)',
                     'subject'=>'Subject (Alphabetical)',
                     'subject_rev'=>'Subject (Reverse alphabetical)'
                    );
   print popup_menu(-name=>'sort',
                    -"values"=>['date','date_rev','sender','sender_rev',
                              'size','size_rev','subject','subject_rev'],
                    -default=>$prefs{"sort"} || 'date',
                    -labels=>\%sortlabels,
                    -override=>'1'),
         '</td></tr><tr><td valign="middle" align="right" bgcolor=',$style{"window_dark"},' width="75">',
         '<B>Default headers:</B></td><td valign="middle" align="left" bgcolor=',$style{"window_dark"},'>';
   my %headerlabels = ('simple'=>'Simple headers',
                       'all'=>'All headers'
                      );
   print popup_menu(-name=>'headers',
                    -"values"=>['simple','all'],
                    -default=>$prefs{"headers"} || 'simple',
                    -labels=>\%headerlabels,
                    -override=>'1');

   print '</td></tr><tr><td colspan="2" bgcolor=',$style{"window_dark"},'>',
          '<B>Signature (500 characters or less)</B><BR>',
          textarea(-name=>'signature',
                   -default=>$prefs{"signature"} ||
                             "--\nSent using NeoMail, a web-based e-mail client.\nhttp://neomail.sourceforge.net",
                   -rows=>'5',
                   -columns=>'76',
                   -wrap=>'hard',
                   -override=>'1');

   print '</td></tr><tr><td colspan="2" align="center" bgcolor=',$style{"window_dark"},'>',
         '<table><tr><td>', submit("Save"), end_form();
   unless ( $firsttimeuser eq 'yes' ) {
      print startform(-action=>"$scripturl");
         print hidden(-name=>'action',
                      -default=>'displayheaders',
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
                      -override=>'1'),
         '</td><td>',
         submit("Cancel");
      print end_form();
   }
   print '</td></tr></table></td></tr></table>';

   printfooter();
}
###################### END MAIN ##############################

#################### EDITADDRESSES ###########################
sub editaddresses {
   verifysession();
   my %addresses;
   my ($name, $email);

   if ( -f "$userprefsdir$user/addressbook" ) {
      open (ABOOK,"$userprefsdir$user/addressbook") or
         neomailerror("Can't open your address book, but it exists!");
      while (<ABOOK>) {
         ($name, $email) = split(/:/, $_);
         chomp($email);
         $addresses{"$name"} = $email;
      }
      close (ABOOK) or neomailerror("Couldn't close your address book!");
   }
   my $abooksize = ( -s "$userprefsdir$user/addressbook" ) || 0;
   my $freespace = int($maxabooksize - ($abooksize/1024) + .5);

   printheader();
   print '<table border="0" align="center" width="90%" cellpadding="0" cellspacing="0">';

   print '<tr><td colspan="1" bgcolor=',$style{"titlebar"},' align="left">',
   '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>EDIT ADDRESS BOOK</b></font>',
   '</td><td colspan="2" bgcolor=',$style{"titlebar"},' align="right"><font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>',
   $freespace,' KB Available</b></font></td></tr><tr><td colspan="3" bgcolor=',$style{"menubar"},' align="left">';
   print "<a href=\"$scripturl?action=displayheaders&amp;sessionid=$thissession&amp;sort=$sort&amp;firstmessage=$firstmessage&amp;folder=$folder\">Back to $folder</a> | ";
   print "<a href=\"$prefsurl?action=importabook&amp;sessionid=$thissession&amp;sort=$sort&amp;firstmessage=$firstmessage&amp;folder=$folder\">Import</a>";
   print '</td></tr>';
### Spacing
   print '<tr><td colspan="3">&nbsp;</td></tr>';
   print '<tr><td align="center" bgcolor=',$style{"columnheader"},'><B>Name</B> (Click to edit address)</td><td align="center" bgcolor=',$style{"columnheader"},'>
          <B>E-mail Address(es)</B> (click to mail)</td><td align="center" bgcolor=',$style{"columnheader"},'><B>Action</B></td></tr>';

   print startform(-name=>'newaddress');
   print '<tr><td bgcolor=',$style{"tablerow_light"},' width="200">',
          hidden(-name=>'action',
                 -value=>'addaddress',
                 -override=>'1'),
          hidden(-name=>'sessionid',
                 -value=>$thissession,
                 -override=>'1'),
          hidden(-name=>'sort',
                 -default=>$sort,
                 -override=>'1'),
          hidden(-name=>'firstmessage',
                 -default=>$firstmessage,
                 -override=>'1'),
          hidden(-name=>'folder',
                 -default=>$folder,
                 -override=>'1'),
          textfield(-name=>'realname',
                    -default=>'',
                    -size=>'25',
                    -override=>'1'),
         '</td><td bgcolor=',$style{"tablerow_light"},' width="200">',
          textfield(-name=>'email',
                    -default=>'',
                    -size=>'25',
                    -override=>'1'),
         '</td><td align="center" bgcolor=',$style{"tablerow_light"},' width="100">',
         submit('Add/Modify'),'</td></tr>';
   print end_form();

   my $bgcolor = $style{"tablerow_dark"};
   foreach my $key (sort { uc($a) cmp uc($b) } (keys %addresses)) {
      print "<tr><td bgcolor=$bgcolor width=\"200\">",
            "<a href=\"Javascript:Update('$key','",$addresses{$key},"')\">$key</a>",
            "</td><td bgcolor=$bgcolor width=\"200\">",
            "<a href=\"$scripturl?action=composemessage&amp;firstmessage=$firstmessage&amp;sort=$sort&amp;folder=$folder&amp;sessionid=$thissession&amp;composetype=sendto&amp;to=",
            $addresses{$key},'">',$addresses{$key},'</a></td>';

      print start_form();
      print hidden(-name=>'action',
                   -value=>'deleteaddress',
                   -override=>'1');
      print hidden(-name=>'sessionid',
                   -value=>$thissession,
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
      print hidden(-name=>'realname',
                   -value=>$key,
                   -override=>'1');
      print "<td bgcolor=$bgcolor align=\"center\" width=\"100\">",submit("Delete"),
      '</td></tr>';
      print end_form();
      if ($bgcolor eq $style{"tablerow_dark"}) {
         $bgcolor = $style{"tablerow_light"};
      } else {
         $bgcolor = $style{"tablerow_dark"};
      }
   }
   print '</table>';

   print '<script language="JavaScript">
      <!--
      function Update(name,email)
      {
         document.newaddress.realname.value = name;
         document.newaddress.email.value = email;
      }
      //-->
      </script>';
   printfooter();
}
################### END EDITADDRESSES ########################

##################### IMPORTABOOK ############################
sub importabook {
   verifysession();
   my ($name, $email);
   my %addresses;
   my $abookupload = param("abook") || '';
   my $abooktowrite='';
   my $mua = param("mua") || '';
   if ($abookupload) {
      no strict 'refs';
      my $abookcontents = '';
      while (<$abookupload>) {
         $abookcontents .= $_;
      }
      close($abookupload);
      if ($mua eq 'outlookexp5') {
         unless ($abookcontents =~ /^Name,E-mail Address/) {
            neomailerror("Sorry, this file doesn't appear to be an address book
                       exported from Microsoft Outlook Express 5 in CSV format.
                       Make sure that when viewing it in a text editor, the first
                       line starts out \"Name,E-mail Address\", then go
                       <a href=\"$prefsurl?action=importabook&amp;sessionid=$thissession&amp;sort=$sort&amp;folder=$folder&amp;firstmessage=$firstmessage\">back</a>
                       and try again.");
         }
      }
      unless ( -f "$userprefsdir$user/addressbook" ) {
         open (ABOOK, ">>$userprefsdir$user/addressbook"); # Create if nonexistent
         close(ABOOK);
      }
      open (ABOOK,"+<$userprefsdir$user/addressbook") or
         neomailerror("Can't open your address book!");
      unless (flock(ABOOK, 2)) {
         neomailerror("Can't get write lock on address book!");
      }
      while (<ABOOK>) {
         ($name, $email) = split(/:/, $_);
         chomp($email);
         $addresses{"$name"} = $email;
      }
      my @fields;
      my $quotecount;
      my $tempstr;
      my @processed;

      foreach (split(/\r*\n/, $abookcontents)) {
         next if ( ($mua eq 'outlookexp5') && (/^Name,E-mail Address/) );
         $quotecount = 0;
         @fields = split(/,/);
         @processed = ();
         $tempstr = '';
         foreach my $str (@fields) {
            if ( ($str =~ /"/) && ($quotecount == 1) ) {
               $tempstr .= ',' . $str;
               $tempstr =~ s/"//g;
               push (@processed, $tempstr);
               $tempstr = '';
               $quotecount = 0;
            } elsif ($str =~ /"/) {
               $tempstr .= $str;
               $quotecount = 1;
            } elsif ($quotecount == 1) {
               $tempstr .= ',' . $str;
            } else {
               push (@processed, $str);
            }
         }
         if ( ($mua eq 'outlookexp5') && ($processed[0]) && ($processed[1]) ) {
            $processed[0] =~ s/^\s*//;
            $processed[0] =~ s/\s*$//;
            $processed[0] =~ s/://;
            $processed[0] =~ s/</&lt;/g;
            $processed[0] =~ s/>/&gt;/g;
            $processed[1] =~ s/</&lt;/g;
            $processed[1] =~ s/>/&gt;/g;
            $addresses{"$processed[0]"} = $processed[1];
         } elsif ( ($mua eq 'nsmail') && ($processed[0]) && ($processed[6]) ) {
            $processed[0] =~ s/^\s*//;
            $processed[0] =~ s/\s*$//;
            $processed[0] =~ s/://;
            $processed[0] =~ s/</&lt;/g;
            $processed[0] =~ s/>/&gt;/g;
            $processed[6] =~ s/</&lt;/g;
            $processed[6] =~ s/>/&gt;/g;
            $addresses{"$processed[0]"} = $processed[6];
         }
      }

      seek (ABOOK, 0, 0) or
         neomailerror("Couldn't seek to the beginning of your address book!");

      while ( ($name, $email) = each %addresses ) {
         $abooktowrite .= "$name:$email\n";
      }

      if (length($abooktowrite) > ($maxabooksize * 1024)) {
         neomailerror("Sorry, impoting these addresses would take your address
                       book over its size limit of $maxabooksize KB.  Please go
                       <a href=\"$prefsurl?action=importabook&amp;sessionid=$thissession&amp;sort=$sort&amp;folder=$folder&amp;firstmessage=$firstmessage\">back</a>
                       and try again, after freeing up some space.");
      }
      print ABOOK $abooktowrite;
      truncate(ABOOK, tell(ABOOK));
      close (ABOOK) or neomailerror("Couldn't close your address book!");

      print "Location: $prefsurl?action=editaddresses&sessionid=$thissession&sort=$sort&folder=$folder&firstmessage=$firstmessage\n\n";

   } else {
      my %mualabels = ('outlookexp5' => 'Outlook Express 5',
                       'nsmail'      => 'Netscape Mail 4.x');

      my $abooksize = ( -s "$userprefsdir$user/addressbook" ) || 0;
      my $freespace = int($maxabooksize - ($abooksize/1024) + .5);

      printheader();
      print '<table border="0" align="center" width="75%" cellpadding="0" cellspacing="0">';

      print '<tr><td bgcolor=',$style{"titlebar"},' align="left">',
      '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>IMPORT ADDRESS BOOK</b></font>',
      '</td><td bgcolor=',$style{"titlebar"},' align="right"><font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>',
      $freespace,' KB Available</b></font></td></tr>';
      print '<tr><td colspan="2" align="center" bgcolor=',$style{"window_light"},'>';
      print '<table border="0" align="center" width="75%" cellpadding="0" cellspacing="0">';
      print '<tr><td bgcolor=',$style{"window_light"},' align="left">';

      print '<BR> Outlook Express 5 and Netscape Mail can export their address
             books in a format known as CSV, or Comma Separated Values.  NeoMail
             can import these files into your personal address book to save you
             hours of tediously typing them into your adddress book by hand.<ul><li>
             In Netscape, open your address book, and select File-&gt;Export, then
             under "Save as type:" choose "Comma Separated (*.csv)."  <BR><BR><li>For Outlook
             Express, in the main Outlook Express window, choose File-&gt;Export-&gt;Address
             Book, and select the export type "Text file."  Make sure that the Name and E-mail
             address fields come first, which is the default setting.</ul>';
      print '</td></tr></table>';
      print start_multipart_form(),
      hidden(-name=>'action',
             -value=>'importabook',
             -override=>'1'),
      hidden(-name=>'sessionid',
             -value=>$thissession,
             -override=>'1'),
      hidden(-name=>'sort',
             -default=>$sort,
             -override=>'1'),
      hidden(-name=>'firstmessage',
             -default=>$firstmessage,
             -override=>'1'),
      hidden(-name=>'folder',
             -default=>$folder,
             -override=>'1'),
      radio_group(-name=>'mua',
                  -"values"=>['outlookexp5','nsmail'],
                  -default=>'outlookexp5',
                  -labels=>\%mualabels),
      '<BR>',
      filefield(-name=>'abook',
                -default=>'',
                -size=>'30',
                -override=>'1');
      print '</td></tr>';
      print '<tr><td width="50%" align="right" bgcolor=',$style{"window_light"},'>';
      print submit('Import'), ' &nbsp;&nbsp;';
      print '</td>';
      print end_form();
      print start_form(),
      hidden(-name=>'action',
             -value=>'editaddresses',
             -override=>'1'),
      hidden(-name=>'sessionid',
             -value=>$thissession,
             -override=>'1'),
      hidden(-name=>'sort',
             -default=>$sort,
             -override=>'1'),
      hidden(-name=>'folder',
             -default=>$folder,
             -override=>'1'),
      hidden(-name=>'firstmessage',
             -default=>$firstmessage,
             -override=>'1');
      print '<td width="50%" align="left" bgcolor=',$style{"window_light"},'>';
      print ' &nbsp;&nbsp;', submit('Cancel');
      print '</td></tr></table>';
      print end_form();
      printfooter();
   }
}
#################### END IMPORTABOOK #########################

################### MODADDRESS ##############################
sub modaddress {
   verifysession();
   my $mode = shift;
   my ($realname, $address);
   $realname = param("realname") || '';
   $address = param("email") || '';
   $realname =~ s/://;
   $realname =~ s/^\s*//; # strip beginning and trailing spaces from hash key
   $realname =~ s/\s*$//;
   $address =~ s/[#&=\?]//g;

   if (($realname && $address) || (($mode eq 'delete') && $realname) ) {
      my %addresses;
      my ($name,$email);
      if ( -f "$userprefsdir$user/addressbook" ) {
         my $abooksize = ( -s "$userprefsdir$user/addressbook" );
         if ( (($abooksize/1024 + length($realname) + length($address) + 2) >= $maxabooksize) && ($mode ne "delete") ) {
            neomailerror("Sorry, this would exceed the size limit for your
                          address book! Click
                          <a href=\"$prefsurl?action=editaddresses&amp;sessionid=$thissession&amp;sort=$sort&amp;folder=$folder&amp;firstmessage=$firstmessage\">here</a>
                          to return to your address book and delete some entries, then
                          try again.");
         }
         open (ABOOK,"+<$userprefsdir$user/addressbook") or
            neomailerror("Can't open your address book, but it exists!");
         unless (flock(ABOOK, 2)) {
            neomailerror("Can't get write lock on address book!");
         }
         while (<ABOOK>) {
            ($name, $email) = split(/:/, $_);
            chomp($email);
            $addresses{"$name"} = $email;
         }
         if ($mode eq 'delete') {
            delete $addresses{"$realname"};
         } else {
            $addresses{"$realname"} = $address;
         }
         seek (ABOOK, 0, 0) or
            neomailerror("Couldn't seek to the beginning of your address book!");
         while ( ($name, $email) = each %addresses ) {
            print ABOOK "$name:$email\n";
         }
         truncate(ABOOK, tell(ABOOK));
         close (ABOOK) or neomailerror("Couldn't close your address book!");
      } else {
         open (ABOOK, ">$userprefsdir$user/addressbook" ) or
            neomailerror("Can't create your address book!");
         print ABOOK "$realname:$address\n";
         close (ABOOK) or neomailerror("Couldn't close your address book!");
      }
   }
   print "Location: $prefsurl?action=editaddresses&sessionid=$thissession&sort=$sort&folder=$folder&firstmessage=$firstmessage\n\n";
}
################## END MODADDRESS ###########################

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

###################### SAVEPREFS #########################
sub saveprefs {
   verifysession();
   unless ( -d "$userprefsdir$user" ) {
      mkdir ("$userprefsdir$user", oct(700)) or
         neomailerror("Couldn't create your user directory!");
   }
   open (CONFIG,">$userprefsdir$user/config") or
      neomailerror("Couldn't write your configuration file!");
   foreach my $key (qw(realname replyto sort headers style)) {
      my $value = param("$key") || '';
      $value =~ s/[\n|=]//;
      print CONFIG "$key=$value\n";
   }
   close (CONFIG) or neomailerror("Couldn't close your configuration file!");
   open (SIGNATURE,">$userprefsdir$user/signature") or
      neomailerror("Couldn't write your signature file!");
   my $value = param("signature") || '';
   if (length($value) > 500) {  # truncate signature to 500 chars
      $value = substr($value, 0, 500);
   }
   print SIGNATURE $value;
   close (SIGNATURE) or neomailerror("Couldn't close your signature file!");
   printheader();
   print '<BR><BR><BR><BR><BR><BR>';
   print '<table border="0" align="center" width="40%" cellpadding="1" cellspacing="1">';

   print '<tr><td bgcolor=',$style{"titlebar"},' align="left">',
   '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>PREFERENCES SAVED</b></font>',
   '</td></tr><tr><td align="center" bgcolor=',$style{"window_light"},'>';
   print "<BR>Preferences successfully saved.";
   print startform(-action=>"$scripturl");
      print hidden(-name=>'action',
                   -default=>'displayheaders',
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
   print submit("Continue");
   print end_form();
   print '</td></tr></table>';
   printfooter();
}
##################### END SAVEPREFS ######################

#################### ADDRESSBOOK #######################
sub addressbook {
   verifysession();
   print header(-pragma=>'no-cache'),
         start_html(-"title"=>"NeoMail Address Book",
                    -author=>'emiller@hhs.net',
                    -BGCOLOR=>'#FFFFFF',
                    -BACKGROUND=>$bg_url);
   my %addresses;
   my ($name, $email);
   my $field=param("field");
   my $preexisting = param("preexisting") || '';
   $preexisting =~ s/(\s+)?,(\s+)?/,/g;
   print startform(-action=>"javascript:Update('" . $field . "')",
                   -name=>'addressbook'
                  );
   print '<table border="0" align="center" width="90%" cellpadding="0" cellspacing="0">';

   print '<tr><td colspan="2" bgcolor=',$style{"titlebar"},' align="left">',
   '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>',uc($field),': ADDRESS BOOK</b></font>',
   '</td></tr>';

   if ( -f "$userprefsdir$user/addressbook" ) {
      open (ABOOK,"$userprefsdir$user/addressbook") or
         neomailerror("Can't open your address book, but it exists!");
      while (<ABOOK>) {
         ($name, $email) = split(/:/, $_);
         chomp($email);
         $addresses{"$name"} = $email;
      }
      close (ABOOK) or neomailerror("Couldn't close your address book!");

      my $bgcolor = $style{"tablerow_dark"};
      foreach my $key (sort(keys %addresses)) {
         print "<tr><td bgcolor=$bgcolor width=\"20\"><input type=\"checkbox\" name=\"to\" value=\"",
         $addresses{"$key"}, '"';
         if ($preexisting =~ s/$addresses{"$key"},?//g) {
            print " checked";
         }
         print "></td><td width=\"100%\" bgcolor=$bgcolor>$key</td></tr>\n";
         if ($bgcolor eq $style{"tablerow_dark"}) {
            $bgcolor = $style{"tablerow_light"};
         } else {
            $bgcolor = $style{"tablerow_dark"};
         }
      }
   }
   print '</td></tr><tr><td align="center" colspan="2" bgcolor=',$style{"tablerow_dark"},'>';
   print '<input type="hidden" name="remainingstr" value="', $preexisting, '">';
   print '<input type="submit" name="mailto.x" value="OK"> &nbsp;&nbsp;';
   print '<input type="button" value="Cancel" onClick="window.close();">';
   print '</td></tr></table>';
   print '<script language="JavaScript">
      <!--
      function Update(whichfield)
      {
         var e2 = document.addressbook.remainingstr.value;
         for (var i = 0; i < document.addressbook.elements.length; i++)
         {
            var e = document.addressbook.elements[i];
            if (e.name == "to" && e.checked)
            {
               if (e2)
                  e2 += ",";
               e2 += e.value;
            }
         }
         if (whichfield == "to")
            window.opener.document.composeform.to.value = e2;
         else if (whichfield == "cc")
            window.opener.document.composeform.cc.value = e2;
         else
            window.opener.document.composeform.bcc.value = e2;
         window.close();
      }
      //-->
      </script>';
   print end_form();
   print end_html();
}
################## END ADDRESSBOOK #####################

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
