#!/usr/bin/perl -T
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
no strict 'vars';
push (@INC, '/var/neomail/mail.namodn.com/');
use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser);

CGI::nph();   # Treat script as a non-parsed-header script

$ENV{PATH} = ""; # no PATH should be needed

require "neomail.conf";

my $version = "1.14";

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

my %timezones = qw(ACDT +1030
                   ACST +0930
                   ADT  -0300
                   AEDT +1100
                   AEST +1000
                   AHDT -0900
                   AHST -1000
                   AST  -0400
                   AT   -0200
                   AWDT +0900
                   AWST +0800
                   AZST +0400
                   BAT  +0300
                   BDST +0200
                   BET  -1100
                   BST  -0300
                   BT   +0300
                   BZT2 -0300
                   CADT +1030
                   CAST +0930
                   CAT  -1000
                   CCT  +0800
                   CDT  -0500
                   CED  +0200
                   CET  +0100
                   CST  -0600
                   EAST +1000
                   EDT  -0400
                   EED  +0300
                   EET  +0200
                   EEST +0300
                   EST  -0500
                   FST  +0200
                   FWT  +0100
                   GMT  +0000
                   GST  +1000
                   HDT  -0900
                   HST  -1000
                   IDLE +1200
                   IDLW -1200
                   IST  +0530
                   IT   +0330
                   JST  +0900
                   JT   +0700
                   MDT  -0600
                   MED  +0200
                   MET  +0100
                   MEST +0200
                   MEWT +0100
                   MST  -0700
                   MT   +0800
                   NDT  -0230
                   NFT  -0330
                   NT   -1100
                   NST  +0630
                   NZ   +1100
                   NZST +1200
                   NZDT +1300
                   NZT  +1200
                   PDT  -0700
                   PST  -0800
                   ROK  +0900
                   SAD  +1000
                   SAST +0900
                   SAT  +0900
                   SDT  +1000
                   SST  +0200
                   SWT  +0100
                   USZ3 +0400
                   USZ4 +0500
                   USZ5 +0600
                   USZ6 +0700
                   UT   +0000
                   UTC  +0000
                   UZ10 +1100
                   WAT  -0100
                   WET  +0000
                   WST  +0800
                   YDT  -0800
                   YST  -0900
                   ZP4  +0400
                   ZP5  +0500
                   ZP6  +0600);

my $thissession = param("sessionid") || '';
my $user = $thissession || '';
$user =~ s/\-session\-0.*$//; # Grab userid from sessionid
($user =~ /^(.+)$/) && ($user = $1);  # untaint $user...

my $setcookie = undef;

my ($login, $pass, $uid, $gid, $homedir);
if ($user) {
   if (($homedirspools eq 'yes') || ($homedirfolders eq 'yes')) {
      ($login, $pass, $uid, $gid, $homedir) = (getpwnam($user))[0,1,2,3,7] or
         neomailerror("User $user doesn't exist!");
         $gid = getgrnam('neomail');
   }
}

my %prefs = %{&readprefs};
my %style = %{&readstyle};

my $lang = $prefs{'language'} || $defaultlanguage;
($lang =~ /^(..)$/) && ($lang = $1);
require "lang/$lang";

my $numberofheaders = $prefs{'numberofmessages'} || $numberofheaders;

my $firstmessage;
if (param("firstmessage")) {
   $firstmessage = param("firstmessage");
} else {
   $firstmessage = 1;
}

my $sort;
if (param("sort")) {
   $sort = param("sort");
} else {
   $sort = $prefs{"sort"} || 'date';
}

my $hitquota = 0;

my $folderdir;
if ( $homedirfolders eq 'yes') {
   $folderdir = "$homedir/mail";
} else {
   $folderdir = "$userprefsdir/$user";
}

my $folder;
my @validfolders;
if ($user) {
   my $isvalid = 0;
   @validfolders = @{&getfolders()};
   if (param("folder")) {
      $folder = param("folder");
      foreach my $checkfolder (@validfolders) {
         if ($folder eq $checkfolder) {
            $isvalid = 1;
            last;
         }
      }
      ($folder = 'INBOX') unless ( $isvalid );
   } else {
      $folder = "INBOX";
   }
}

my $printfolder = $lang_folders{$folder} || $folder || '';
my $escapedfolder = CGI::escape($folder);

$sessiontimeout = $sessiontimeout/60/24; # convert to format expected by -M

# once we print the header, we don't want to do it again if there's an error
my $headerprinted = 0;
my $total_size = 0;
my $savedattsize;
my $validsession = 0;

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
      } elsif ($action eq "emptytrash") {
         emptytrash();
      } elsif ($action eq "viewattachment") {
         viewattachment();
      } elsif ($action eq "composemessage") {
         composemessage();
      } elsif ($action eq "sendmessage") {
         sendmessage();
      } elsif ($action eq "movemessage") {
         movemessage();
      } elsif ($action eq "logout") {
         logout();
      } else {
         neomailerror("Action $lang_err{'has_illegal_chars'}");
      }
   } else {
      neomailerror("Action $lang_err{'has_illegal_chars'}");
   }
} else {            # no action has been taken, display login page
   printheader(),
   my $html='';
   my $temphtml;
   open (LOGIN, "$neomaildir/templates/$lang/login.template") or
      neomailerror("$lang_err{'couldnt_open'} login.template!");
   while (<LOGIN>) {
      $html .= $_;
   }
   close (LOGIN);

   $html = applystyle($html);

   $temphtml = startform(-action=>$scripturl,
                         -name=>'login');
   $temphtml .= hidden("action","login");
   $html =~ s/\@\@\@STARTFORM\@\@\@/$temphtml/;
   $temphtml = textfield(-name=>'userid',
                         -default=>'',
                         -size=>'10',
                         -override=>'1');
   $html =~ s/\@\@\@USERIDFIELD\@\@\@/$temphtml/;
   $temphtml = password_field(-name=>'password',
                              -default=>'',
                              -size=>'10',
                              -override=>'1');
   $html =~ s/\@\@\@PASSWORDFIELD\@\@\@/$temphtml/;
   $temphtml = submit("$lang_text{'login'}");
   $html =~ s/\@\@\@LOGINBUTTON\@\@\@/$temphtml/;
   $temphtml = reset("$lang_text{'clear'}");
   $html =~ s/\@\@\@CLEARBUTTON\@\@\@/$temphtml/;
   $temphtml = end_form();
   $html =~ s/\@\@\@ENDFORM\@\@\@/$temphtml/;
   print $html;
}
###################### END MAIN ##############################

####################### LOGIN ########################
sub login {
   my $userid = param("userid") || '';
   my $password = param("password") || '';
   $userid =~ /^(.*)$/; # accept any characters for userid/pass auth info
   $userid = $1;
   $password =~ /^(.*)$/;
   $password = $1;

# Checklogin() is modularized so that it's easily replaceable with other
# auth methods.
   if ($userid eq 'root') {
      writelog("ATTEMPTED ROOT LOGIN");
      neomailerror ("$lang_err{'norootlogin'}");
   }

   if ( ( -x "$neomaildir/checklogin.pl" ) && 
        (eval { open (CHECKLOGIN,"| $neomaildir/checklogin.pl");
                print CHECKLOGIN "$passwdfile\n";
                print CHECKLOGIN "$userid\n";
                print CHECKLOGIN "$password\n";
                close (CHECKLOGIN);
              }
        )
      ) {
      $thissession = $userid . "-session-" . rand(); # name the sessionid
      $user = $userid;
      writelog("login - $thissession");

      cleanupoldsessions(); # Deletes sessionids that have expired

      $setcookie = crypt(rand(),'NM');
      open (SESSION, '>' . $neomaildir . $thissession) or # create sessionid
         neomailerror("$lang_err{'couldnt_open'} $thissession!");
      print SESSION "$setcookie";
      close (SESSION);

      if (($homedirspools eq 'yes') || ($homedirfolders eq 'yes')) {
         ($login, $pass, $uid, $gid, $homedir) = (getpwnam($user))[0,1,2,3,7] or
            neomailerror("User $user doesn't exist!");
         $gid = getgrnam('neomail');
      }

      if ( $homedirfolders eq 'yes') {
         $folderdir = "$homedir/mail";
      } else {
         $folderdir = "$userprefsdir/$user";
      }

      if ( -d "$userprefsdir$user" ) {
         %prefs = %{&readprefs};
         %style = %{&readstyle};
         $lang = $prefs{'language'} || $defaultlanguage;
         ($lang =~ /^(..)$/) && ($lang = $1);
         require "lang/$lang";
         $sort = $prefs{"sort"} || 'date';
         $numberofheaders = $prefs{'numberofmessages'} || $numberofheaders;
         my $isvalid = 0;
         @validfolders = @{&getfolders()};
         $folder = "INBOX";
         displayheaders();
      } else {
         firsttimeuser();
      }
   } else { # Password is INCORRECT
      my $html = '';
      writelog("invalid login attempt for username=$userid");
      printheader();
      open (INCORRECT, "$neomaildir/templates/$lang/passwordincorrect.template") or
         neomailerror("$lang_err{'couldnt_open'} passwordincorrect.template!");
      while (<INCORRECT>) {
         $html .= $_;
      }
      close (INCORRECT);

      $html = applystyle($html);
      
      print $html;
      printfooter();
      exit 0;
   }
}
#################### END LOGIN #####################

#################### LOGOUT ########################
sub logout {
   neomailerror("Session ID $lang_err{'has_illegal_chars'}") unless
      (($thissession =~ /^(.+?\-\d?\.\d+)$/) && ($thissession = $1));
   $thissession =~ s/\///g;  # just in case someone gets tricky ...
   unlink "$neomaildir$thissession";

   writelog("logout - $thissession");

   print "Location: $scripturl\n\n";
}
################## END LOGOUT ######################

################## GETFOLDERS ####################
sub getfolders {
   my $totalfoldersize = 0;
   my @folders;
   if ( $homedirfolders eq 'yes' ) {
      @folders = qw(INBOX saved-messages sent-mail neomail-trash);
   } else {
      @folders = qw(INBOX SAVED TRASH SENT);
   }
   my $filename;
   opendir (FOLDERDIR, "$folderdir") or
      neomailerror("$lang_err{'couldnt_open'} $folderdir!");
   while (defined($filename = readdir(FOLDERDIR))) {
      if ( $homedirfolders eq 'yes' ) {
         unless ( ($filename eq 'saved-messages') ||
                  ($filename eq 'sent-mail') ||
                  ($filename eq 'neomail-trash') ||
                  ($filename eq '.') ||
                  ($filename eq '..')
                ) {
            push (@folders, $filename);
            $totalfoldersize += ( -s "$folderdir/$filename" );
         }
      } else {
         if ($filename =~ /^(.+)\.folder$/) {
            push (@folders, $1);
            $totalfoldersize += ( -s "$folderdir/$filename" );
         }
      }
   }
   closedir (FOLDERDIR) or
      neomailerror("$lang_err{'couldnt_close'} $folderdir!");
   if ( $homedirfolders eq 'yes' ) {
      $totalfoldersize += ( -s "$folderdir/sent-mail" ) || 0;
      $totalfoldersize += ( -s "$folderdir/saved-messages" ) || 0;
      $totalfoldersize += ( -s "$folderdir/neomail-trash" ) || 0;
   } else {
      $totalfoldersize += ( -s "$folderdir/SAVED" ) || 0;
      $totalfoldersize += ( -s "$folderdir/TRASH" ) || 0;
      $totalfoldersize += ( -s "$folderdir/SENT" ) || 0;
   }
   if ($folderquota) {
      ($hitquota = 1) if ($totalfoldersize >= ($folderquota * 1024));
   }

   return \@folders;
}
################ END GETFOLDERS ##################

################ CLEANUPOLDSESSIONS ##################
sub cleanupoldsessions {
   my $sessionid;
   opendir (NEOMAILDIR, "$neomaildir") or
      neomailerror("$lang_err{'couldnt_open'} $neomaildir!");
   while (defined($sessionid = readdir(NEOMAILDIR))) {
      if ($sessionid =~ /^(\w+\-session\-0\.\d*.*)$/) {
         $sessionid = $1;
         if ( -M "$neomaildir/$sessionid" > $sessiontimeout ) {
            writelog("session cleanup - $sessionid");
            unlink "$neomaildir/$sessionid";
         }
      }
   }
   closedir (NEOMAILDIR);
}
############## END CLEANUPOLDSESSIONS ################

############## VERIFYSESSION ########################
sub verifysession {
   if ($validsession == 1) {
      return 1;
   }
   if ( -M "$neomaildir/$thissession" > $sessiontimeout || !(-e "$neomaildir/$thissession")) {
      my $html = '';
      printheader();
      open (TIMEOUT, "$neomaildir/templates/$lang/sessiontimeout.template") or
         neomailerror("$lang_err{'couldnt_open'} sessiontimeout.template!");
      while (<TIMEOUT>) {
         $html .= $_;
      }
      close (TIMEOUT);

      $html = applystyle($html);

      print $html;

      printfooter();
      writelog("timed-out session access attempt - $thissession");
      exit 0;
   }
   if ( -e "$neomaildir/$thissession" ) {
      open (SESSION, "$neomaildir/$thissession");
      my $cookie = <SESSION>;
      close (SESSION);
      chomp $cookie;
      unless ( cookie("sessionid") eq $cookie) {
         writelog("attempt to hijack session $thissession!");
         neomailerror("$lang_err{'inv_sessid'}");
      }
   }

   neomailerror("Session ID $lang_err{'has_illegal_chars'}") unless
      (($thissession =~ /^([\w\.\-]+)$/) && ($thissession = $1));
   open (SESSION, '>' . $neomaildir . $thissession) or
      neomailerror("$lang_err{'couldnt_open'} $thissession!");
   print SESSION cookie("sessionid");
   close (SESSION);
   $validsession = 1;
   return 1;
}
############# END VERIFYSESSION #####################

################ DISPLAYHEADERS #####################
sub displayheaders {
   verifysession() unless $setcookie;
   printheader();

   my ($bgcolor, $status, $message_size);
   my $newmessages = 0;
   my $escapedmessageid; # Used when creating link from subject line
   my @headers = @{&getheaders($user)};
   my $numheaders = $#headers + 1 || 1;
   my $page_total = $numheaders/$numberofheaders || 1;
   $page_total = int($page_total) + 1 if ($page_total != int($page_total));

   if (defined(param("custompage"))) {
      my $pagenumber = param("custompage");
      $pagenumber = 1 if ($pagenumber < 1);
      $pagenumber = $page_total if ($pagenumber > $page_total);
      $firstmessage = (($pagenumber-1)*$numberofheaders) + 1;
   }

### Perform verification of $firstmessage, make sure it's within bounds
   if ($firstmessage > ($#headers + 1)) {
      $firstmessage = $#headers - ($numberofheaders - 1);
   }
   if ($firstmessage < 1) {
      $firstmessage = 1;
   }
   my $lastmessage = $firstmessage + $numberofheaders - 1;
   if ($lastmessage > ($#headers + 1)) {
       $lastmessage = ($#headers + 1);
   }

   foreach my $messnum (0 .. $#headers) {
      unless (${$headers[$messnum]}{status} =~ /r/i) {
         $newmessages++;
      }
   }

   my $base_url = "$scripturl?sessionid=$thissession&amp;sort=$sort&amp;folder=$escapedfolder";

   my $page_nb;
   if ($#headers > 0) {
      $page_nb = ($firstmessage) * (($#headers + 1) / $numberofheaders) / ($#headers + 1);
      ($page_nb = int($page_nb) + 1) if ($page_nb != int($page_nb));
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

   my $html = '';
   my $temphtml;
   open (VIEWFOLDER, "$neomaildir/templates/$lang/viewfolder.template") or
      neomailerror("$lang_err{'couldnt_open'} viewfolder.template!");
   while (<VIEWFOLDER>) {
      $html .= $_;
   }
   close (VIEWFOLDER);

   $html = applystyle($html);

   $temphtml = end_form();
   $html =~ s/\@\@\@ENDFORM\@\@\@/$temphtml/g;

   $temphtml = startform(-action=>$scripturl,
                         -name=>'FolderForm');
   $temphtml .= hidden(-name=>'sessionid',
                       -value=>$thissession,
                       -override=>'1');
   $temphtml .= hidden(-name=>'sort',
                       -value=>$sort,
                       -override=>'1');
   $temphtml .= hidden(-name=>'action',
                       -value=>'displayheaders',
                       -override=>'1');
   $temphtml .= hidden(-name=>'firstmessage',
                       -value=>$firstmessage,
                       -override=>'1');
   $html =~ s/\@\@\@STARTFOLDERFORM\@\@\@/$temphtml/;

   $temphtml = popup_menu(-name=>'folder',
                          -"values"=>\@validfolders,
                          -default=>$folder,
                          -labels=>\%lang_folders,
                          -onChange=>'JavaScript:document.FolderForm.submit();',
                          -override=>'1');
   $html =~ s/\@\@\@FOLDERPOPUP\@\@\@/$temphtml/;

   if (defined($headers[0])) {
      $temphtml = ($firstmessage) . " - " . ($lastmessage) . " $lang_text{'of'} " .
                  ($#headers + 1) . " $lang_text{'messages'} ";
      if ($newmessages) {
         $temphtml .= "($newmessages $lang_text{'unread'})";
      }
      $temphtml .= " - $total_size";
   } else {
      $temphtml = $lang_text{'nomessages'};
   }

   if ($hitquota) {
      $temphtml .= " [ $lang_text{'quota_hit'} ]";
   }

   $html =~ s/\@\@\@NUMBEROFMESSAGES\@\@\@/$temphtml/g;

   $temphtml = "<a href=\"$base_url&amp;action=composemessage&amp;firstmessage=$firstmessage\"><IMG SRC=\"$image_url/compose.gif\" border=\"0\" ALT=\"$lang_text{'composenew'}\"></a> ";
   $temphtml .= "<a href=\"$base_url&amp;action=displayheaders&amp;firstmessage=$firstmessage\"><IMG SRC=\"$image_url/refresh.gif\" border=\"0\" ALT=\"$lang_text{'refresh'}\"></a> ";
   $temphtml .= "<a href=\"$prefsurl?sessionid=$thissession&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage\"><IMG SRC=\"$image_url/prefs.gif\" border=\"0\" ALT=\"$lang_text{'userprefs'}\"></a> ";
   $temphtml .= "<a href=\"$prefsurl?action=editaddresses&amp;sessionid=$thissession&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage\"><IMG SRC=\"$image_url/addresses.gif\" border=\"0\" ALT=\"$lang_text{'addressbook'}\"></a> ";
   $temphtml .= "<a href=\"$prefsurl?action=editfolders&amp;sessionid=$thissession&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage\"><IMG SRC=\"$image_url/folder.gif\" border=\"0\" ALT=\"$lang_text{'folders'}\"></a> &nbsp; &nbsp; &nbsp; ";
   $temphtml .= "<a href=\"$base_url&amp;action=emptytrash&amp;firstmessage=$firstmessage\"><IMG SRC=\"$image_url/trash.gif\" border=\"0\" ALT=\"$lang_text{'emptytrash'}\"></a> ";
   $temphtml .= "<a href=\"$base_url&amp;action=logout&amp;firstmessage=$firstmessage\"><IMG SRC=\"$image_url/logout.gif\" border=\"0\" ALT=\"$lang_text{'logout'}\"></a>";

   $html =~ s/\@\@\@MENUBARLINKS\@\@\@/$temphtml/g;

   $temphtml = start_form(-action=>$scripturl);
   $temphtml .= hidden(-name=>'action',
                       -default=>'displayheaders',
                       -override=>'1');
   $temphtml .= hidden(-name=>'sessionid',
                       -default=>$thissession,
                       -override=>'1');
   $temphtml .= hidden(-name=>'sort',
                       -default=>$sort,
                       -override=>'1');

   $html =~ s/\@\@\@STARTPAGEFORM\@\@\@/$temphtml/g;
   
   if ($firstmessage != 1) {
      $temphtml = "<a href=\"$base_url&amp;action=displayheaders&amp;firstmessage=1\">";
      $temphtml .= "<img src=\"$image_url/first.gif\" align=\"absmiddle\" border=\"0\" alt=\"&lt;&lt;\"></a>";
   } else {
      $temphtml = "<img src=\"$image_url/first-grey.gif\" align=\"absmiddle\" border=\"0\" alt=\"\">";
   }

   if (($firstmessage - $numberofheaders) >= 1) {
      $temphtml .= "<a href=\"$base_url&amp;action=displayheaders&amp;firstmessage=" . ($firstmessage - $numberofheaders) . "\">";
      $temphtml .= "<img src=\"$image_url/left.gif\" align=\"absmiddle\" border=\"0\" alt=\"&lt;\"></a>";
   } else {
      $temphtml .= "<img src=\"$image_url/left-grey.gif\" align=\"absmiddle\" border=\"0\" alt=\"\">";
   }

   $temphtml .= "[$lang_text{'page'} " .
                textfield(-name=>'custompage',
                          -default=>$page_nb,
                          -size=>'2',
                          -override=>'1') .
                " $lang_text{'of'} " . $page_total . ']';

   if (($firstmessage + $numberofheaders) <= ($#headers + 1)) {
      $temphtml .= "<a href=\"$base_url&amp;action=displayheaders&amp;firstmessage=" . ($firstmessage + $numberofheaders) . "\">";
      $temphtml .= "<img src=\"$image_url/right.gif\" align=\"absmiddle\" border=\"0\" alt=\"&gt;\"></a>";
   } else {
      $temphtml .= "<img src=\"$image_url/right-grey.gif\" align=\"absmiddle\" border=\"0\" alt=\"\">";
   }

   if (($firstmessage + $numberofheaders) <= ($#headers +1) ) {
      $temphtml .= "<a href=\"$base_url&amp;action=displayheaders&amp;custompage=" . "$page_total\">";
      $temphtml .= "<img src=\"$image_url/last.gif\" align=\"absmiddle\" border=\"0\" alt=\"&gt;&gt;\"></a>";
   } else {
      $temphtml .= "<img src=\"$image_url/last-grey.gif\" align=\"absmiddle\" border=\"0\" alt=\"\">";
   }

   $html =~ s/\@\@\@PAGECONTROL\@\@\@/$temphtml/g;

   $temphtml = start_form(-action=>$scripturl,
                          -onSubmit=>"return confirm($lang_text{'moveconfirm'})",
                          -name=>'moveform');
   my @movefolders;
   foreach my $checkfolder (@validfolders) {
      unless ( ($checkfolder eq 'INBOX') || ($checkfolder eq $folder) ) {
         push (@movefolders, $checkfolder);
      }
   }
   $temphtml .= hidden(-name=>'action',
                       -default=>'movemessage',
                       -override=>'1');
   $temphtml .= hidden(-name=>'sessionid',
                       -default=>$thissession,
                       -override=>'1');
   $temphtml .= hidden(-name=>'firstmessage',
                       -default=>$firstmessage,
                       -override=>'1');
   $temphtml .= hidden(-name=>'sort',
                       -default=>$sort,
                       -override=>'1');
   $temphtml .= hidden(-name=>'folder',
                       -default=>$folder,
                       -override=>'1');
   $html =~ s/\@\@\@STARTMOVEFORM\@\@\@/$temphtml/g;
   
   if ( $homedirfolders eq 'yes' ) {
      $temphtml = popup_menu(-name=>'destination',
                             -"values"=>\@movefolders,
                             -default=>'neomail-trash',
                             -labels=>\%lang_folders,
                             -override=>'1');
   } else {
      $temphtml = popup_menu(-name=>'destination',
                             -"values"=>\@movefolders,
                             -default=>'TRASH',
                             -labels=>\%lang_folders,
                             -override=>'1');
   }
   $temphtml .= submit("$lang_text{'move'}");

   $html =~ s/\@\@\@MOVECONTROLS\@\@\@/$temphtml/g;

   $temphtml = "<a href=\"$scripturl?action=displayheaders&amp;firstmessage=".
               ($firstmessage)."&amp;sessionid=$thissession&amp;folder=$escapedfolder&amp;sort=";
   if ($sort eq "date") {
      $temphtml .= "date_rev\">$lang_text{'date'} <IMG SRC=\"$image_url/up.gif\"                   border=\"0\" alt=\"^\"></a></B></td>";
   } elsif ($sort eq "date_rev") {
      $temphtml .= "date\">$lang_text{'date'} <IMG SRC=\"$image_url/down.gif\"                      border=\"0\" alt=\"v\"></a></B></td>";
   } else {
      $temphtml .= "date\">$lang_text{'date'}</a></B></td>";
   }

   $html =~ s/\@\@\@DATE\@\@\@/$temphtml/g;
   
   $temphtml = "<a href=\"$scripturl?action=displayheaders&amp;firstmessage=".
                ($firstmessage)."&amp;sessionid=$thissession&amp;folder=$escapedfolder&amp;sort=";

   if ( ($folder eq 'SENT') || ($folder eq 'sent-mail') ) {
      if ($sort eq "sender") {
         $temphtml .= "sender_rev\">$lang_text{'recipient'} <IMG SRC=\"$image_url/down.gif\" border=\"0\" alt=\"v\"></a></B></td>";
      } elsif ($sort eq "sender_rev") {
         $temphtml .= "sender\">$lang_text{'recipient'} <IMG SRC=\"$image_url/up.gif\" border=\"0\" alt=\"^\"></a></B></td>";
      } else {
         $temphtml .= "sender\">$lang_text{'recipient'}</a></B></td>";
      }
   } else {
      if ($sort eq "sender") {
         $temphtml .= "sender_rev\">$lang_text{'sender'} <IMG SRC=\"$image_url/down.gif\" border=\"0\" alt=\"v\"></a></B></td>";
      } elsif ($sort eq "sender_rev") {
         $temphtml .= "sender\">$lang_text{'sender'} <IMG SRC=\"$image_url/up.gif\" border=\"0\" alt=\"^\"></a></B></td>";
      } else {
         $temphtml .= "sender\">$lang_text{'sender'}</a></B></td>";
      }
   }

   $html =~ s/\@\@\@SENDER\@\@\@/$temphtml/g;

   $temphtml = "<a href=\"$scripturl?action=displayheaders&amp;firstmessage=".
                ($firstmessage)."&amp;sessionid=$thissession&amp;folder=$escapedfolder&amp;sort=";

   if ($sort eq "subject") {
      $temphtml .= "subject_rev\">$lang_text{'subject'} <IMG SRC=\"$image_url/down.gif\" border=\"0\" alt=\"v\"></a></B></td>";
   } elsif ($sort eq "subject_rev") {
      $temphtml .= "subject\">$lang_text{'subject'} <IMG SRC=\"$image_url/up.gif\" border=\"0\" alt=\"^\"></a></B></td>";
   } else {
      $temphtml .= "subject\">$lang_text{'subject'}</a></B></td>";
   }

   $html =~ s/\@\@\@SUBJECT\@\@\@/$temphtml/g;

   $temphtml = "<a href=\"$scripturl?action=displayheaders&amp;firstmessage=".
                ($firstmessage)."&amp;sessionid=$thissession&amp;folder=$escapedfolder&amp;sort=";

   if ($sort eq "size") {
      $temphtml .= "size_rev\">$lang_text{'size'} <IMG SRC=\"$image_url/up.gif\" border=\"0\" alt=\"^\"></a></B></td>";
   } elsif ($sort eq "size_rev") {
      $temphtml .= "size\">$lang_text{'size'} <IMG SRC=\"$image_url/down.gif\" border=\"0\" alt=\"v\"></a></B></td>";
   } else {
      $temphtml .= "size\">$lang_text{'size'}</a></B></td>";
   }

   $html =~ s/\@\@\@SIZE\@\@\@/$temphtml/g;

   $temphtml = '';
   my ($boldon, $boldoff); # Used to control whether text is bold for new mails
   foreach my $messnum (($firstmessage - 1) .. ($lastmessage - 1)) {
### Stop when we're out of messages!
      last if !(defined($headers[$messnum]));

      ${$headers[$messnum]}{subject} =~ s/&/&amp;/g;
      ${$headers[$messnum]}{subject} =~ s/\"/&quot;/g;
      ${$headers[$messnum]}{subject} =~ s/</&lt;/g;
      ${$headers[$messnum]}{subject} =~ s/>/&gt;/g;

### Make sure there's SOMETHING clickable for subject line
      unless (${$headers[$messnum]}{subject} =~ /[^\s]/) {
         ${$headers[$messnum]}{subject} = "N/A";
      }

      $escapedmessageid = CGI::escape(${$headers[$messnum]}{message_id});

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
      if ( ${$headers[$messnum]}{status} =~ /r/i ) {
         $boldon = '';
         $boldoff = '';
      } else {
         $status .= "<img src=\"$image_url/new.gif\" align=\"absmiddle\">";
         $boldon = "<B>";
         $boldoff = "</B>";
      }

      if ( (${$headers[$messnum]}{content_type} ne 'N/A') && !(${$headers[$messnum]}{content_type} =~ /^text/i) ) {
         $status .= "<img src=\"$image_url/attach.gif\" align=\"absmiddle\">";
      }

      $temphtml .= "<tr><td valign=\"middle\" width=\"50\" bgcolor=$bgcolor>$status&nbsp;</td>".
         "<td valign=\"middle\" width=\"150\" bgcolor=$bgcolor>$boldon".
         ${$headers[$messnum]}{date}."$boldoff</td>".
         "<td valign=\"middle\" width=\"150\" bgcolor=$bgcolor>$boldon".
         ${$headers[$messnum]}{from}."$boldoff</td>".
         "<td valign=\"middle\" width=\"350\" bgcolor=$bgcolor>".
         "<a href=\"$scripturl?action=readmessage&amp;firstmessage=".
         ($firstmessage)."&amp;sessionid=$thissession&amp;status=".
         ${$headers[$messnum]}{status}."&amp;folder=$escapedfolder&amp;sort=$sort&amp;headers=".
         ($prefs{"headers"} || 'simple'). "&amp;message_id=".
         $escapedmessageid ."\">$boldon".
         ${$headers[$messnum]}{subject}."</a>$boldoff</td>".
         "<td valign=\"middle\" width=\"40\" bgcolor=$bgcolor>$boldon".
         $message_size . "$boldoff</td>".
         "<td align=\"center\" valign=\"middle\" width=\"50\" bgcolor=$bgcolor>".
         checkbox(-name=>'message_ids',
                  -value=>${$headers[$messnum]}{message_id},
                  -label=>'').
         '</td></tr>';
   }
   $html =~ s/\@\@\@HEADERS\@\@\@/$temphtml/;

   print $html;

   printfooter();
}
############### END DISPLAYHEADERS ##################

################# READMESSAGE ####################
sub readmessage {
   verifysession();
   printheader();
   my $messageid = param("message_id");
   my $escapedmessageid = CGI::escape($messageid);
   my %message = %{&getmessage($user,$messageid)};
   my $headers = param("headers") || 'simple';
   unless ($message{status} =~ /r/i) {
      updatestatus($user,$messageid,"R");
   }
   if (%message) {
      my $html = '';
      my $temphtml;
      open (READMESSAGE, "$neomaildir/templates/$lang/readmessage.template") or
         neomailerror("$lang_err{'couldnt_open'} readmessage.template!");
      while (<READMESSAGE>) {
         $html .= $_;
      }
      close (READMESSAGE);

      $html = applystyle($html);

### these will hold web-ified headers
      my ($from, $replyto, $to, $cc, $subject, $body);
      $from = $message{from} || '';
      $from =~ s/&/&amp;/g;
      $from =~ s/\"/&quot;/g;
      $from =~ s/</&lt;/g;
      $from =~ s/>/&gt;/g;
      $replyto = $message{replyto} || '';
      $replyto =~ s/&/&amp;/g;
      $replyto =~ s/\"/&quot;/g;
      $replyto =~ s/</&lt;/g;
      $replyto =~ s/>/&gt;/g;
      $to = $message{to} || '';
      $to =~ s/&/&amp;/g;
      $to =~ s/\"/&quot;/g;
      $to =~ s/</&lt;/g;
      $to =~ s/>/&gt;/g;
      $cc = $message{cc} || '';
      $cc =~ s/&/&amp;/g;
      $cc =~ s/\"/&quot;/g;
      $cc =~ s/</&lt;/g;
      $cc =~ s/>/&gt;/g;
      $subject = $message{subject} || '';
      $subject =~ s/&/&amp;/g;
      $subject =~ s/\"/&quot;/g;
      $subject =~ s/</&lt;/g;
      $subject =~ s/>/&gt;/g;
### Handle mail programs that send the body of a message quoted-printable
      if ( ($message{contenttype} =~ /^text/i) &&
           ($message{encoding} =~ /^quoted-printable/i) ) {
         $message{"body"} = decode_qp($message{"body"});
### OR base64 :)
      } elsif ( ($message{contenttype} =~ /^text/i) &&
           ($message{encoding} =~ /^base64/i) ) {
         $message{"body"} = decode_base64($message{"body"});
      }

      $body = $message{"body"} || '';
      $body =~ s/&/&amp;/g;
      $body =~ s/\"/&quot;/g;
      $body =~ s/</&lt;/g;
      $body =~ s/>/&gt;/g;
      $body =~ s/\n/<BR>\n/g;
      $body =~ s/ {2}/ &nbsp;/g;
      $body =~ s/\t/ &nbsp;&nbsp;&nbsp;&nbsp;/g;

      my $base_url = "$scripturl?sessionid=$thissession&amp;firstmessage=" . ($firstmessage) .
                     "&amp;sort=$sort&amp;folder=$escapedfolder&amp;message_id=$escapedmessageid";
      my $base_url_noid = "$scripturl?sessionid=$thissession&amp;firstmessage=" . ($firstmessage) .
                          "&amp;sort=$sort&amp;folder=$escapedfolder";

##### Set up the message to go to after move.
      my $messageaftermove;
      if (defined($message{"next"})) {
         $messageaftermove = $message{"next"};
      } elsif (defined($message{"prev"})) {
         $messageaftermove = $message{"prev"};
      }

      $html =~ s/\@\@\@MESSAGENUMBER\@\@\@/$message{"number"}/g;

      $temphtml = "<a href=\"$base_url&amp;action=displayheaders\"><IMG SRC=\"$image_url/backtofolder.gif\" border=\"0\" ALT=\"$lang_text{'backto'} $printfolder\"></a> &nbsp; &nbsp; ";
      $temphtml .= "<a href=\"$base_url&amp;action=composemessage&amp;composetype=reply\"><IMG SRC=\"$image_url/reply.gif\" border=\"0\" ALT=\"$lang_text{'reply'}\"></a> " .
      "<a href=\"$base_url&amp;action=composemessage&amp;composetype=replyall\"><IMG SRC=\"$image_url/replyall.gif\" border=\"0\" ALT=\"$lang_text{'replyall'}\"></a> " .
      "<a href=\"$base_url&amp;action=composemessage&amp;composetype=forward\"><IMG SRC=\"$image_url/forward.gif\" border=\"0\" ALT=\"$lang_text{'forward'}\"></a> &nbsp; &nbsp; " .
      "<a href=\"$base_url&amp;action=logout\"><IMG SRC=\"$image_url/logout.gif\" border=\"0\" ALT=\"$lang_text{'logout'}\"></a>";
   
      $html =~ s/\@\@\@MENUBARLINKS\@\@\@/$temphtml/g;

      if (defined($message{"prev"})) {
         $temphtml = "<a href=\"$base_url_noid&amp;action=readmessage&amp;message_id=$message{'prev'}\"><img src=\"$image_url/left.gif\" align=\"absmiddle\" border=\"0\" alt=\"&lt;&lt;\"></a>";
      } else {
         $temphtml = "<img src=\"$image_url/left-grey.gif\" align=\"absmiddle\" border=\"0\" alt=\"\">";
      }

      $temphtml .= "  " . $message{"number"} . "  ";

      if (defined($message{"next"})) {
         $temphtml .= "<a href=\"$base_url_noid&amp;action=readmessage&amp;message_id=$message{'next'}\"><img src=\"$image_url/right.gif\" align=\"absmiddle\" border=\"0\" alt=\"&gt;&gt;\"></a>";
      } else {
         $temphtml .= "<img src=\"$image_url/right-grey.gif\" align=\"absmiddle\" border=\"0\" alt=\"\">";
      }

      $html =~ s/\@\@\@MESSAGECONTROL\@\@\@/$temphtml/g;

      $temphtml = start_form(-action=>$scripturl,
                             -onSubmit=>"return confirm($lang_text{'moveconfirm'})",
                             -name=>'moveform');
      my @movefolders;
      foreach my $checkfolder (@validfolders) {
         unless ( ($checkfolder eq 'INBOX') || ($checkfolder eq $folder) ) {
            push (@movefolders, $checkfolder);
         }
      }
      $temphtml .= hidden(-name=>'action',
                          -default=>'movemessage',
                          -override=>'1');
      $temphtml .= hidden(-name=>'sessionid',
                          -default=>$thissession,
                          -override=>'1');
      $temphtml .= hidden(-name=>'firstmessage',
                          -default=>$firstmessage,
                          -override=>'1');
      $temphtml .= hidden(-name=>'sort',
                          -default=>$sort,
                          -override=>'1');
      $temphtml .= hidden(-name=>'folder',
                          -default=>$folder,
                          -override=>'1');
      $temphtml .= hidden(-name=>'message_ids',
                          -default=>$messageid,
                          -override=>'1');
      if ($messageaftermove) {
         $temphtml .= hidden(-name=>'messageaftermove',
                             -default=>'1',
                             -override=>'1');
         $temphtml .= hidden(-name=>'message_id',
                             -default=>$messageaftermove,
                             -override=>'1');
      }
      $html =~ s/\@\@\@STARTMOVEFORM\@\@\@/$temphtml/g;
   
      if ( $homedirfolders eq 'yes' ) {
         $temphtml = popup_menu(-name=>'destination',
                                -"values"=>\@movefolders,
                                -labels=>\%lang_folders,
                                -default=>'neomail-trash',
                                -override=>'1');
      } else {
         $temphtml = popup_menu(-name=>'destination',
                                -"values"=>\@movefolders,
                                -labels=>\%lang_folders,
                                -default=>'TRASH',
                                -override=>'1');
      }
      $temphtml .= submit("$lang_text{'move'}");

      $html =~ s/\@\@\@MOVECONTROLS\@\@\@/$temphtml/g;

      if ($headers eq "all") {
         $message{"header"} = decode_mimewords($message{"header"});
         $message{"header"} =~ s/&/&amp;/g;
         $message{"header"} =~ s/\"/&quot;/g;
         $message{"header"} =~ s/</&lt;/g;
         $message{"header"} =~ s/>/&gt;/g;
         $message{"header"} =~ s/\n/<BR>\n/g;
         $message{"header"} =~ s/ {2}/ &nbsp;/g;
         $message{"header"} =~ s/\t/ &nbsp;&nbsp;&nbsp;&nbsp;/g;
         $message{"header"} =~ s/\n([-\w]+?:)/\n<B>$1<\/B>/g;
         $temphtml = $message{"header"};
      } else {
         $temphtml = "<B>$lang_text{'date'}:</B> $message{date}<BR>\n";
         $temphtml .= "<B>$lang_text{'from'}:</B> $from<BR>\n";
         if ($replyto) {
            $temphtml .= "<B>$lang_text{'replyto'}:</B> $replyto<BR>\n";
         }
         if ($to) {
            $temphtml .= "<B>$lang_text{'to'}:</B> $to<BR>\n";
         }
         if ($cc) {
            $temphtml .= "<B>$lang_text{'cc'}:</B> $cc<BR>\n";
         }
         if ($subject) {
            $temphtml .= "<B>$lang_text{'subject'}:</B> $subject\n";
         }
      }

      $html =~ s/\@\@\@HEADERS\@\@\@/$temphtml/g;

      if ($headers eq "all") {
         $temphtml = "<a href=\"$base_url&amp;action=readmessage&amp;message_id=$escapedmessageid&amp;headers=simple\">$lang_text{'simplehead'}</a>";
      } else {
         $temphtml = "<a href=\"$base_url&amp;action=readmessage&amp;message_id=$escapedmessageid&amp;headers=all\">$lang_text{'allhead'}</a>";
      }
      $html =~ s/\@\@\@HEADERSTOGGLE\@\@\@/$temphtml/g;

      foreach (qw(http https ftp nntp news gopher telnet)) {
         $body =~ s/($_:\/\/[\w\.\-]+?\/?[^\s<>]*[\w\/])([\b|\n| ]*)/<A HREF=\"$1\" TARGET=\"_blank\">$1<\/A>$2/gs;
      }
      $body =~ s/([\b|\n| ]+)(www\.[-\w\.]+\.[-\w]{2,3})([\b|\n| ]*)/$1<a href=\"http:\/\/$2\" TARGET=\"_blank\">$2<\/a>$3/gs;

      $temphtml = $body;

# Handle the messages generated if sendmail is set up to send MIME error reports
      if ($message{contenttype} =~ /^multipart\/report/i) {
         foreach my $attnumber (0 .. $#{$message{attachment}}) {
            if (defined(${$message{attachment}[$attnumber]}{contents})) {
               ${$message{attachment}[$attnumber]}{contents} =~ s/&/&amp;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/\"/&quot;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/</&lt;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/>/&gt;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/\n/<BR>\n/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/ {2}/ &nbsp;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/\t/ &nbsp;&nbsp;&nbsp;&nbsp;/g;
               $temphtml .= ${$message{attachment}[$attnumber]}{contents} .
                     hr();
            }
         }
      } elsif ( ($message{contenttype} ne 'N/A') && !($message{contenttype} =~ /^text/i )) {
         foreach my $attnumber (0 .. $#{$message{attachment}}) {
            next unless (defined(%{$message{attachment}[$attnumber]}));
            if (($attnumber == 0) &&
               (${$message{attachment}[$attnumber]}{contenttype} =~ /^text\/plain/i)) {
               if (${$message{attachment}[$attnumber]}{encoding} =~ /^quoted-printable/i) {
                  ${$message{attachment}[$attnumber]}{contents} = decode_qp(${$message{attachment}[$attnumber]}{contents});
               }
               $temphtml .= hr();
               ${$message{attachment}[$attnumber]}{contents} =~ s/&/&amp;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/\"/&quot;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/</&lt;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/>/&gt;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/\n/<BR>\n/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/ {2}/ &nbsp;/g;
               ${$message{attachment}[$attnumber]}{contents} =~ s/\t/ &nbsp;&nbsp;&nbsp;&nbsp;/g;
               foreach (qw(http https ftp nntp news gopher telnet)) {
                  ${$message{attachment}[$attnumber]}{contents} =~
                  s/($_:\/\/[\w\.\-]+?\/?[^\s<>]*[\w\/])([\b|\n| ]*)/<A HREF=\"$1\" TARGET=\"_blank\">$1<\/A>$2/gs;
               }
               ${$message{attachment}[$attnumber]}{contents} =~ s/([\b|\n| ]+)(www\.[-\w\.]+\.[-\w]{2,3})([\b|\n| ]*)/$1<a href=\"http:\/\/$2\" TARGET=\"_blank\">$2<\/a>$3/gs;
               $temphtml .= ${$message{attachment}[$attnumber]}{contents} . "<BR><BR>";
            } else {
               my $escapedfilename = CGI::escape(${$message{attachment}[$attnumber]}{filename});
               if (${$message{attachment}[$attnumber]}{filename} =~
                  /\.(jpg|jpeg|gif|png)$/i) {
                  $temphtml .= "<table border=\"0\" align=\"center\" cellpadding=\"2\">
                  <tr><td valign=\"middle\"
                  bgcolor=" . $style{"attachment_dark"} . " align=\"center\">$lang_text{'attachment'} $attnumber: ${$message{attachment}[$attnumber]}{filename}
                  </td></tr><td valign=\"middle\" bgcolor=" . $style{"attachment_light"} .
                  " align=\"center\">";
                  $temphtml .= "<IMG BORDER=\"0\"
                  SRC=\"$scripturl/$escapedfilename?action=viewattachment&amp;sessionid=$thissession&amp;message_id=$escapedmessageid&amp;folder=$escapedfolder&amp;attachment_number=$attnumber\">";
                  $temphtml .= "</td></tr></table>";

               } else {

                  $temphtml .= "<table border=\"0\" align=\"center\" cellpadding=\"2\"><tr><td colspan=\"2\" valign=\"middle\" bgcolor=" . $style{"attachment_dark"} . " align=\"center\">$lang_text{'attachment'} $attnumber</td></tr><td valign=\"middle\" bgcolor=" . $style{"attachment_light"} . " align=\"center\">";
                  
                  $temphtml .= "$lang_text{'type'}: " . ${$message{attachment}[$attnumber]}{contenttype} . "<BR>";
                  $temphtml .= "$lang_text{'filename'}: " . ${$message{attachment}[$attnumber]}{filename} . "<BR>";
                  $temphtml .= "$lang_text{'encoding'}: " . ${$message{attachment}[$attnumber]}{encoding};
                  $temphtml .= '</td><td valign="middle" bgcolor=' . $style{"attachment_light"} . ' align="center">';
                  $temphtml .= "<a href=\"$scripturl/$escapedfilename?action=viewattachment&amp;sessionid=$thissession&amp;message_id=$escapedmessageid&amp;folder=$escapedfolder&amp;attachment_number=$attnumber\">$lang_text{'download'}</a>";
                  $temphtml .= '</td></tr></table>';
               }
            }
         }
      }

      $html =~ s/\@\@\@BODY\@\@\@/$temphtml/g;
      print $html;

   } else {
      $messageid =~ s/&/&amp;/g;
      $messageid =~ s/\"/&quot;/g;
      $messageid =~ s/>/&gt;/g;
      $messageid =~ s/</&lt;/g;

      print "What the heck? Message $messageid seems to be gone!";
   }
   printfooter();
}
############### END READMESSAGE ##################

############### COMPOSEMESSAGE ###################
sub composemessage {
   no strict 'refs';
   verifysession();
   my $html = '';
   my $temphtml;
   my @attlist;
   open (COMPOSEMESSAGE, "$neomaildir/templates/$lang/composemessage.template") or
      neomailerror("$lang_err{'couldnt_open'} composemessage.template!");
   while (<COMPOSEMESSAGE>) {
      $html .= $_;
   }
   close (COMPOSEMESSAGE);

   $html = applystyle($html);
   
   if (defined(param($lang_text{'add'}))) {
      @attlist = @{&getattlist()};
      my $attachment = param("attachment");
      my $attname = $attachment;
      my $attcontents = '';
      if ($attachment) {
         if ( ($attlimit) && ( ( $savedattsize + (-s $attachment) ) > ($attlimit * 1048576) ) ) {
            neomailerror ("$lang_err{'att_overlimit'} $attlimit MB!");
         }
         my $content_type;
### Convert :: back to the ' like it should be.
         $attname =~ s/::/'/g;
### Trim the path info from the filename
         $attname =~ s/^.*\\//;
         $attname =~ s/^.*\///;
         $attname =~ s/^.*://;
         $/ = undef; # Force a single input to grab the whole spool
         $attcontents = <$attachment>;
         $/ = "\n";
         $attcontents = encode_base64($attcontents);
         $savedattsize += length($attcontents);
         if (defined(uploadInfo($attachment))) {
            $content_type = ${uploadInfo($attachment)}{'Content-Type'} || 'application/octet-stream';
         } else {
            $content_type = 'application/octet-stream';
         }
         my $attnum = ($#attlist +1) || 0;
         open (ATTFILE, ">$neomaildir$thissession-att$attnum");
         print ATTFILE "Content-Type: ", $content_type,";\n";
         print ATTFILE "\tname=\"$attname\"\nContent-Transfer-Encoding: base64\n\n";
         print ATTFILE "$attcontents";
         close ATTFILE;
         $attname =~ s/&/&amp;/g;
         $attname =~ s/\"/&quot;/g;
         $attname =~ s/</&lt;/g;
         $attname =~ s/>/&gt;/g;
         $attname =~ s/^(.*)$/<em>$1<\/em>/;
         push (@attlist, $attname);
      }
   } elsif ( !(defined(param($lang_text{'add'}))) ) {
      deleteattachments();
   }

   my $messageid = param("message_id");
   my %message;
   my $attnumber;
   my $from;
   if ($prefs{"fromname"}) {
      $from = $prefs{"fromname"} . "@" . $prefs{domainname}; 
   } else {
      $from = $thissession;
      $from =~ s/\-session\-0.*$/\@$prefs{domainname}/; # create from: address
   } 
   if ($prefs{"realname"}) {
      my $realname = $prefs{"realname"};
      $from =~ s/^(.+)$/$realname <$1>/;
   }
   my $escapedfrom = $from;
   $escapedfrom =~ s/&/&amp;/g;
   $escapedfrom =~ s/\"/&quot;/g;
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
      $cc = param("cc") || '';
      $bcc = param("bcc") || '';
      $subject = param("subject") || '';
      $body = param("body") || '';

      if (($composetype eq "reply") || ($composetype eq "replyall") ||
          ($composetype eq "forward") ) {
         %message = %{&getmessage($user,$messageid)};

### Handle mail programs that send the body of a message quoted-printable
         if ( ($message{contenttype} =~ /^text/i) &&
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
            shift @{$message{attachment}};
         }
# Handle the messages generated if sendmail is set up to send MIME error reports
         if ($message{contenttype} =~ /^multipart\/report/i) {
            foreach my $attnumber (0 .. $#{$message{attachment}}) {
               if (defined(${$message{attachment}[$attnumber]}{contents})) {
                  $body .= ${$message{attachment}[$attnumber]}{contents};
                  shift @{$message{attachment}};
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
         if (defined(${$message{attachment}[0]}{header})) {
            foreach my $attnumber (0 .. $#{$message{attachment}}) {
               open (ATTFILE, ">$neomaildir$thissession-att$attnumber");
               print ATTFILE ${$message{attachment}[$attnumber]}{header}, "\n\n", ${$message{attachment}[$attnumber]}{contents};
               close ATTFILE;
            }
            @attlist = @{&getattlist()};
         }
         $subject = $message{"subject"} || '';
         $subject = "Fw: " . $subject unless ($subject =~ /^fw:/i);
         $body = "\n\n------------- Forwarded message follows -------------\n\n$body";
      }

   }
   if ( (defined($prefs{"signature"})) && ($composetype ne 'continue') ) {
      $body .= "\n\n".$prefs{"signature"};
   }
   printheader();
   
   $temphtml = "<a href=\"$scripturl?action=displayheaders&amp;sessionid=$thissession&amp;folder=$escapedfolder&amp;sort=$sort&amp;firstmessage=$firstmessage\"><IMG SRC=\"$image_url/backtofolder.gif\" border=\"0\" ALT=\"$lang_text{'backto'} $printfolder\"></a>";
   $html =~ s/\@\@\@BACKTOFOLDER\@\@\@/$temphtml/g;

   $temphtml = start_multipart_form(-name=>'composeform');
   $temphtml .= hidden(-name=>'action',
                       -default=>'sendmessage',
                       -override=>'1');
   $temphtml .= hidden(-name=>'sessionid',
                       -default=>$thissession,
                       -override=>'1');
   $temphtml .= hidden(-name=>'composetype',
                       -default=>'continue',
                       -override=>'1');
   $temphtml .= hidden(-name=>'sort',
                       -default=>$sort,
                       -override=>'1');
   $temphtml .= hidden(-name=>'firstmessage',
                       -default=>$firstmessage,
                       -override=>'1');
   $temphtml .= hidden(-name=>'folder',
                       -default=>$folder,
                       -override=>'1');
   $html =~ s/\@\@\@STARTCOMPOSEFORM\@\@\@/$temphtml/g;

   $html =~ s/\@\@\@ESCAPEDFROM\@\@\@/$escapedfrom/g;

   $temphtml = textfield(-name=>'to',
                         -default=>$to,
                         -size=>'70',
                         -override=>'1');
   $html =~ s/\@\@\@TOFIELD\@\@\@/$temphtml/g;

   $temphtml = textfield(-name=>'cc',
                         -default=>$cc,
                         -size=>'70',
                         -override=>'1');
   $html =~ s/\@\@\@CCFIELD\@\@\@/$temphtml/g;
          
   $temphtml = textfield(-name=>'bcc',
                         -default=>$bcc,
                         -size=>'70',
                         -override=>'1');
   $html =~ s/\@\@\@BCCFIELD\@\@\@/$temphtml/g;
 
   $temphtml = textfield(-name=>'replyto',
                         -default=>$prefs{"replyto"} || '',
                         -size=>'70',
                         -override=>'1');
   $html =~ s/\@\@\@REPLYTOFIELD\@\@\@/$temphtml/g;
   
   $temphtml = '';
   foreach my $filename (@attlist) {
      $temphtml .= "$filename<BR>";
   }
   if ( $savedattsize ) {
      $temphtml .= "<em>" . int($savedattsize/1024) . "KB";
      if ( $attlimit ) {
         $temphtml .= " $lang_text{'of'} $attlimit MB";
      }
      $temphtml .= "</em><BR>";
   }
   $temphtml .= filefield(-name=>'attachment',
                         -default=>'',
                         -size=>'60',
                         -override=>'1',
                         -tabindex=>'-1');
   $temphtml .= submit(-name=>"$lang_text{'add'}",
                       -value=>"$lang_text{'add'}",
                       -tabindex=>'-1'
                      );
   $html =~ s/\@\@\@ATTACHMENTFIELD\@\@\@/$temphtml/g;

   $temphtml = textfield(-name=>'subject',
                         -default=>$subject,
                         -size=>'70',
                         -override=>'1');
   $html =~ s/\@\@\@SUBJECTFIELD\@\@\@/$temphtml/g;

   $temphtml = textarea(-name=>'body',
                        -default=>$body,
                        -rows=>'10',
                        -columns=>'72',
                        -wrap=>'hard',
                        -override=>'1');
   $html =~ s/\@\@\@BODYAREA\@\@\@/$temphtml/g;

   $temphtml = submit("$lang_text{'send'}");
   $html =~ s/\@\@\@SENDBUTTON\@\@\@/$temphtml/g;

   $temphtml = end_form();
   $html =~ s/\@\@\@ENDFORM\@\@\@/$temphtml/g;

   $temphtml = start_form(-action=>$scripturl);
   
   if (param("message_id")) {
      $temphtml .= hidden(-name=>'action',
                          -default=>'readmessage',
                          -override=>'1');
      $temphtml .= hidden(-name=>'firstmessage',
                          -default=>$firstmessage,
                          -override=>'1');
      $temphtml .= hidden(-name=>'sort',
                          -default=>$sort,
                          -override=>'1');
      $temphtml .= hidden(-name=>'folder',
                          -default=>$folder,
                          -override=>'1');
      $temphtml .= hidden(-name=>'headers',
                          -default=>$prefs{"headers"} || 'simple',
                          -override=>'1');
      $temphtml .= hidden(-name=>'sessionid',
                          -default=>$thissession,
                          -override=>'1');
      $temphtml .= hidden(-name=>'message_id',
                          -default=>param("message_id"),
                          -override=>'1');
   } else {
      $temphtml .= hidden(-name=>'action',
                          -default=>'displayheaders',
                          -override=>'1');
      $temphtml .= hidden(-name=>'firstmessage',
                          -default=>$firstmessage,
                          -override=>'1');
      $temphtml .= hidden(-name=>'sort',
                          -default=>$sort,
                          -override=>'1');
      $temphtml .= hidden(-name=>'folder',
                          -default=>$folder,
                          -override=>'1');
      $temphtml .= hidden(-name=>'sessionid',
                          -default=>$thissession,
                          -override=>'1');
   }
   $html =~ s/\@\@\@STARTCANCELFORM\@\@\@/$temphtml/g;

   $temphtml = submit("$lang_text{'cancel'}");
   $html =~ s/\@\@\@CANCELBUTTON\@\@\@/$temphtml/g;

   $html =~ s/\@\@\@SESSIONID\@\@\@/$thissession/g;

   print $html;

   printfooter();
}
############# END COMPOSEMESSAGE #################

############### SENDMESSAGE ######################
sub sendmessage {
   no strict 'refs';
   verifysession();
   if (defined(param($lang_text{'add'}))) {
      composemessage();
   } else {
### Add a header that will allow SENT folder to function correctly
      my $localtime = scalar(localtime);
      my $messagecontents = "From $user $localtime\n";
      my $date = localtime();
      my @datearray = split(/ +/, $date);
      $date = "$datearray[0], $datearray[2] $datearray[1] $datearray[4] $datearray[3] $timeoffset";
      my $from;
      my $realname = $prefs{"realname"} || '';
      if($prefs{"fromname"}) {
         # Create from: address for when "fromname" is defined
         $from = $prefs{"fromname"} . "@" . $prefs{domainname};
      } else {
         # Create from: address for when "fromname" is not defined
         $from = $thissession;
         $from =~ s/\-session\-0.*$/\@$prefs{domainname}/; 
      }
      $from =~ s/[\||'|"|`]/ /g;  # Get rid of shell escape attempts
      $realname =~ s/[\||'|"|`]/ /g;  # Get rid of shell escape attempts
      ($realname =~ /^(.+)$/) && ($realname = '"'.$1.'"');
      ($from =~ /^(.+)$/) && ($from = $1);

      my $savedatts = ''; # Will buffer saved attachments
      my $boundary = "----=NEOMAIL_ATT_" . rand();
      my $to = param("to");
      my $cc = param("cc");
      my $bcc = param("bcc");
      my $subject = param("subject");
      my $body = param("body");
      $body =~ s/\r//g;  # strip ^M characters from message. How annoying!
      my $attachment = param("attachment");
      if ( $attachment ) {
         getattlist();
         if ( ($attlimit) && ( ( $savedattsize + (-s $attachment) ) > ($attlimit * 1048576) ) ) {
            neomailerror ("$lang_err{'att_overlimit'} $attlimit MB!");
         }
      }
      my $attname = $attachment;
### Convert :: back to the ' like it should be.
      $attname =~ s/::/'/g;
### Trim the path info from the filename
      $attname =~ s/^.*\\//;
      $attname =~ s/^.*\///;
      $attname =~ s/^.*://;

      open (SENDMAIL, "|" . $sendmail . " -oem -oi -F '$realname' -f '$from' -t 1>&2") or
         neomailerror("$lang_err{'couldnt_open'} $sendmail!");
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
      print SENDMAIL "MIME-Version: 1.0\n";
      $messagecontents .= "MIME-Version: 1.0\n";

      opendir (NEOMAILDIR, "$neomaildir") or
         neomailerror("$lang_err{'couldnt_open'} $neomaildir!");
      while (defined(my $currentfile = readdir(NEOMAILDIR))) {
         if ($currentfile =~ /^($thissession-att\d+)$/) {
            $currentfile = $1;
            open (ATTFILE, "$neomaildir$currentfile");
            $/ = undef; # Force a single input to grab the whole spool
            $savedatts .= "\n--$boundary\n" . <ATTFILE>;
            $/ = "\n";
            close (ATTFILE);
         }
      }
      closedir (NEOMAILDIR);

      if ($attachment || $savedatts) {
         print SENDMAIL "Content-Type: multipart/mixed;\n";
         print SENDMAIL "\tboundary=\"$boundary\"\n\n";
         print SENDMAIL "This is a multi-part message in MIME format.\n\n";
         print SENDMAIL "--$boundary\n";
         print SENDMAIL "Content-Type: text/plain; charset=US-ASCII\n\n";
         print SENDMAIL $body;
         $body =~ s/^From />From /gm;
         print SENDMAIL "\n$savedatts\n";

         $messagecontents .= "Content-Type: multipart/mixed;\n".
                             "\tboundary=\"$boundary\"\n\nThis is a multi-part message in MIME format.\n\n".
                             "--$boundary\nContent-Type: text/plain; charset=US-ASCII\n\n$body\n$savedatts\n";
         if ($attachment) {
            my $attcontents = '';
            $/ = undef; # Force a single input to grab the whole spool
            $attcontents = <$attachment>;
            $/ = "\n";
            $attcontents = encode_base64($attcontents);
            my $content_type;
            if (defined(uploadInfo($attachment))) {
               $content_type = ${uploadInfo($attachment)}{'Content-Type'} || 'application/octet-stream';
            } else {
               $content_type = 'application/octet-stream';
            }
            print SENDMAIL "--$boundary\nContent-Type: ", $content_type,";\n";
            print SENDMAIL "\tname=\"$attname\"\nContent-Transfer-Encoding: base64\n\n";
            print SENDMAIL "$attcontents\n";
            $messagecontents .= "--$boundary\nContent-Type: $content_type;\n".
                             "\tname=\"$attname\"\nContent-Transfer-Encoding: base64\n\n".
                             "$attcontents\n";
         }
         print SENDMAIL "--$boundary--";
         $messagecontents .= "--$boundary--\n\n";
      } else {
         print SENDMAIL "\n$body\n";
         $body =~ s/^From />From /gm;
         $messagecontents .= "\n$body\n\n";
      }

      close(SENDMAIL) or senderror();
      
      deleteattachments();
      
      my $sentfolder;
      if ( $homedirfolders eq 'yes' ) {
         $sentfolder = 'sent-mail';
      } else {
         $sentfolder = 'SENT';
      }
      unless ($hitquota) {
         if ( ($homedirfolders eq 'yes') && ($> == 0) ) {
            $) = $gid;
            $> = $uid;
         }
         open (SENT, ">>$folderdir/$sentfolder") or
            neomailerror("$lang_err{'couldnt_open'} $sentfolder!");
         unless (flock(SENT, 2)) {
            neomailerror("$lang_err{'couldnt_lock'} $sentfolder!");
         }
         print SENT "$messagecontents\n";
         close (SENT) or neomailerror ("$lang_err{'couldnt_close'} $sentfolder!");
      }
      displayheaders();
   }
}

sub senderror {
   my $html = '';
   my $temphtml;
   open (SENDERROR, "$neomaildir/templates/$lang/senderror.template") or
      neomailerror("$lang_err{'couldnt_open'} senderror.template!");
   while (<SENDERROR>) {
      $html .= $_;
   }
   close (SENDERROR);

   $html = applystyle($html);

   printheader();

   print $html;

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
      unless (${$message{attachment}[$attnumber]}{contenttype} =~ /^text/i) {
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
################### END VIEWATTACHMENT ##################

################## GETHEADERS #######################
sub getheaders {
   my $username = shift;
   my @message = ();
   my @datearray;
   my $currentheader;
   my $spoolfile;
   if ($folder eq 'INBOX') {
      if ($homedirspools eq "yes") {
         $spoolfile = "$homedir/$homedirspoolname";
      } elsif ($hashedmailspools eq "yes") {
         $username =~ /^(.)(.)/;
         my $firstchar = $1;
         my $secondchar = $2;
         $spoolfile = "$mailspooldir/$firstchar/$secondchar/$username";
      } else {
         $spoolfile = "$mailspooldir/$username";
      }
   } elsif ( ($folder eq 'SAVED') || ($folder eq 'SENT') || 
      ($folder eq 'TRASH') || ( $homedirfolders eq 'yes' ) ) {
      $spoolfile = "$folderdir/$folder";
   } else {
      $spoolfile = "$folderdir/$folder.folder";
   }
   
   if ( ( ($homedirfolders eq 'yes') || ($homedirspools eq 'yes') ) && ($> == 0) ) {
      $) = $gid;
      $> = $uid;
   }
   open (SPOOL, $spoolfile) or return \@message;

   my $messagenumber = -1;
   my %header;
   my $lastline;
   my $line;
   my $inheader = 1;

   while (defined($line = <SPOOL>)) {
      $total_size += length($line);
      if ($line =~ /^From /) {
         unless ($messagenumber == -1) {
            if ( ($folder eq 'SENT') || ($folder eq 'sent-mail') ) {
### We aren't interested in the sender in this case, but the recipient
### Handling it this way avoids having a separate sort sub for To:.
               $header{from} = (split(/,/, $header{to}))[0];
            }
### Convert to readable text from MIME-encoded
            $header{"from"} = decode_mimewords($header{"from"});
            $header{"subject"} = decode_mimewords($header{"subject"});

            ($header{from} =~ s/^"?(.+?)"?\s+<(.*)>$/<a href="$scripturl\?action=composemessage&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage&amp;sessionid=$thissession&amp;composetype=sendto&amp;to=$2">$1<\/a>/) ||
               ($header{from} =~ s/(.+)/<a href="$scripturl\?action=composemessage&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage&amp;sessionid=$thissession&amp;composetype=sendto&amp;to=$1">$1<\/a>/);
            @datearray = split(/\s/, $header{date});
            if ($datearray[0] =~ /[A-Za-z,]/) {
               shift @datearray; # Get rid of the day of the week
            }
            $header{date} = "$month{$datearray[1]}/$datearray[0]/$datearray[2] $datearray[3] $datearray[4]";
### Get a unique memory address before creating pointer
            my %uniqheader = %header;
            $message[$messagenumber] = \%uniqheader;
         }
         $messagenumber++;
         $header{"from"} = 'N/A';
         $header{"to"} = 'N/A';
         $header{"date"} = 'N/A';
         $header{"subject"} = 'N/A';
         $header{"message_id"} = 'N/A';
         $header{"content_type"} = 'N/A';
         $header{"status"} = '';
         $header{"messagesize"} = length($line);
         $inheader = 1;
         $lastline = 'NONE';
      } else {
         $header{"messagesize"} += length($line);

         if ($inheader) {
            if ($line =~ /^\r*$/) {
               $inheader = 0;
            } elsif ($line =~ /^\s/) {
               if    ($lastline eq 'FROM') { $header{from} .= $line }
               elsif ($lastline eq 'DATE') { $header{date} .= $line }
               elsif ($lastline eq 'SUBJ') { $header{subject} .= $line }
               elsif ($lastline eq 'TO') { $header{to} .= $line }
               elsif ($lastline eq 'MESSID') { 
                  $line =~ s/^\s+//;
                  chomp($line);
                  $header{message_id} .= $line;
               }
            } elsif ($line =~ /^from:\s+(.+)$/ig) {
               $header{from} = $1;
               $lastline = 'FROM';
            } elsif ($line =~ /^to:\s+(.+)$/ig) {
               $header{to} = $1;
               $lastline = 'TO';
            } elsif ($line =~ /^date:\s+(.+)$/ig) {
               $header{date} = $1;
               $lastline = 'DATE';
            } elsif ($line =~ /^subject:\s+(.+)$/ig) {
               $header{subject} = $1;
               $lastline = 'SUBJ';
            } elsif ($line =~ /^message-id:\s+(.*)$/ig) {
               $header{message_id} = $1;
               $lastline = 'MESSID';
            } elsif ($line =~ /^content-type:\s+(.+)$/ig) {
               $header{content_type} = $1;
               $lastline = 'NONE';
            } elsif ($line =~ /^status:\s+(.+)$/ig) {
               $header{status} = $1;
               $lastline = 'NONE';
            } else {
               $lastline = 'NONE';
            }
         }
      }
   }
   close (SPOOL);
### Catch the last message, since there won't be a From: to trigger the capture
   unless ($messagenumber == -1) {
      if ( ($folder eq 'SENT') || ($folder eq 'sent-mail') ) {
### We aren't interested in the sender in this case, but the recipient
### Handling it this way avoids having a separate sort sub for To:.
         $header{from} = (split(/,/, $header{to}))[0];
      }
      $header{"from"} = decode_mimewords($header{"from"});
      $header{"subject"} = decode_mimewords($header{"subject"});
      ($header{from} =~ s/^"(.+?)"\s+<(.*)>$/<a href="$scripturl\?action=composemessage&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage&amp;sessionid=$thissession&amp;composetype=sendto&amp;to=$2">$1<\/a>/) ||
      ($header{from} =~ s/^<(.*)>$/<a href="$scripturl\?action=composemessage&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage&amp;sessionid=$thissession&amp;composetype=sendto&amp;to=$1">$1<\/a>/) ||
         ($header{from} =~ s/(.+)/<a href="$scripturl\?action=composemessage&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage&amp;sessionid=$thissession&amp;composetype=sendto&amp;to=$1">$1<\/a>/);
      @datearray = split(/\s/, $header{date});
      if ($datearray[0] =~ /[A-Za-z,]/) {
         shift @datearray; # Get rid of the day of the week
      }
      $header{date} = "$month{$datearray[1]}/$datearray[0]/$datearray[2] $datearray[3] $datearray[4]";
### Get a unique memory address before creating pointer
      my %uniqheader = %header;
      $message[$messagenumber] = \%uniqheader;
   }

   if ( (defined($message[0])) && (${$message[0]}{subject} =~
      /DON'T DELETE THIS MESSAGE/) ) {
      shift @message;  # Remove those pesky IMAP messages :)
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

   $offseta = $timezones{$offseta} unless ($offseta =~ /[\+|\-]/);
   $offsetb = $timezones{$offsetb} unless ($offsetb =~ /[\+|\-]/);

   my @datearraya = split(/\//, $datea);
   my @timearraya = split(/:/, $timea);
   my @datearrayb = split(/\//, $dateb);
   my @timearrayb = split(/:/, $timeb);
### No, this doesn't take into account the day change near midnight, but
### It's close enough. :)
   $timearraya[0] -= $offseta / 100;
   $timearrayb[0] -= $offsetb / 100;

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
   $timearrayb[2] <=> $timearraya[2]
      or
   ${$a}{message_id} cmp ${$b}{message_id};
}

sub by_sender {
   my $sendera = ${$a}{from};
   my $senderb = ${$b}{from};

   lc($sendera) cmp lc($senderb)
      or
   ${$a}{message_id} cmp ${$b}{message_id};
}

sub by_subject {
   my $subjecta = ${$a}{subject};
   my $subjectb = ${$b}{subject};

   lc($subjecta) cmp lc($subjectb)
      or
   ${$a}{message_id} cmp ${$b}{message_id};
}

sub by_size {
   ${$b}{messagesize} <=> ${$a}{messagesize}
      or
   ${$a}{message_id} cmp ${$b}{message_id};
}
#################### END GETHEADERS #######################

#################### GETMESSAGE ###########################
sub getmessage {
   my $username = shift;
   my $currentmessage = undef;
   my $line;
   my $spoolfile;
   my $messageid = shift;

   my %message = ();
   my @attachment = ();

   my ($currentheader, $currentbody, $currentfrom, $currentdate,
       $currentsubject, $currentid, $currenttype, $currentto, $currentcc,
       $currentreplyto, $currentencoding, $currentstatus);
   if ($folder eq 'INBOX') {
      if ($homedirspools eq "yes") {
         $spoolfile = "$homedir/$homedirspoolname";
      } elsif ($hashedmailspools eq "yes") {
         $username =~ /^(.)(.)/;
         my $firstchar = $1;
         my $secondchar = $2;
         $spoolfile = "$mailspooldir/$firstchar/$secondchar/$username";
      } else {
         $spoolfile = "$mailspooldir/$username";
      }
   } elsif ( ($folder eq 'SAVED') || ($folder eq 'SENT') || 
      ($folder eq 'TRASH') || ($homedirfolders eq 'yes') ) {
      $spoolfile = "$folderdir/$folder";
   } else {
      $spoolfile = "$folderdir/$folder.folder";
   }

   if ( ( ($homedirfolders eq 'yes') || ($homedirspools eq 'yes') ) && ($> == 0) ) {
      $) = $gid;
      $> = $uid;
   }
   open (SPOOL, $spoolfile) or return \%message;
   my $lastline;
   while (defined($line = <SPOOL>)) {
      if ( ($line =~ /^From /) && (defined($currentmessage)) ) {
         last if ($currentid eq $messageid);
         $currentmessage = $line;
         $currentid = '';
         $lastline = '';
      } else {
         if ($currentid) {
            next unless ($currentid eq $messageid);
         }
         if ( ($lastline =~ /^message-id:/i) && ($line =~ /^\s+(.+)$/) ) {
            $currentid = $1 unless $currentid;
         } elsif ($line =~ /^message-id:\s+([^\s]+?)$/i) {
            $currentid = $1 unless $currentid;
         }
         $lastline = $line;
         $currentmessage .= $line;
      }
   }
   $currentid ||= ''; # Make sure currentid isn't undef for next comparison
   if ( (defined($currentmessage)) && !($currentid eq $messageid) ) {
      if ($currentmessage =~ /^message-id:[\s\n]+([^\s\n]+?)$/im) {
            $currentid = $1;
      }
   }
   close (SPOOL);

   if ($currentid eq $messageid) {
      $currentheader = $currentbody = $currentfrom = $currentdate =
      $currentsubject = $currenttype = $currentto =
      $currentcc = $currentreplyto = $currentencoding = 'N/A';
      $currentstatus = '';
      ($currentheader, $currentbody) = split(/\n\r*\n/, $currentmessage, 2);
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

      if ($currenttype =~ /^multipart/i) {
         my @attachments;
         my ($attheader, $attcontents);
         my $boundary = $currenttype;
         $boundary =~ s/.*boundary="?([^"]+)"?.*$/$1/i;
         ($currentbody, @attachments) = split(/\-\-\Q$boundary\E\n*/,$currentbody);
         my $attnum = -1;  # So that the first increment gives 0
         my $outerattnum = -1;
         foreach my $bound (0 .. $#attachments) {
            $outerattnum++;
            $attnum++;
            my %temphash;
            ($attheader, $attcontents) = split(/\n\n/, $attachments[$outerattnum], 2);
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
                  $boundary =~ s/.*boundary="?([^"]+)"?.*$/$1/i;
                  ($attcontents, my @attachments) = split(/\-\-\Q$boundary\E\n*/,$attcontents);
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
                        unless ($attfilename =~ s/^.+name="?([^"]+)"?.*$/$1/ig) {
                           $attfilename = "Unknown.html";
                        }
                        $attfilename = decode_mimewords($attfilename);
                        $attheader = decode_mimewords($attheader);
                        $temphash{filename} = $attfilename;
                        $temphash{contenttype} = $attcontenttype || 'text/plain';
                        $temphash{encoding} = $attencoding;
                        $temphash{header} = $attheader;
                        $temphash{contents} = $attcontents;
                        $attachment[$attnum] = \%temphash;
                     }
                  }
               } else {
                  $attfilename = $attcontenttype;
                  $attcontenttype =~ s/^(.+);.*/$1/g;
                  unless ($attfilename =~ s/^.+name="?([^"]+)"?.*$/$1/ig) {
                     $attfilename = "Unknown.html";
                  }
                  $attfilename = decode_mimewords($attfilename);
                  $attheader = decode_mimewords($attheader);
                  $temphash{filename} = $attfilename;
                  $temphash{contenttype} = $attcontenttype || 'text/plain';
                  $temphash{encoding} = $attencoding;
                  $temphash{header} = $attheader;
                  $temphash{contents} = $attcontents;
                  $attachment[$attnum] = \%temphash;
               }
            }
         }
      } elsif ( ($currenttype ne 'N/A') && !($currenttype =~ /^text/i) ) {
         my ($attfilename, $attcontenttype);
         my %temphash;
         $attcontenttype = $attfilename = $currenttype;
         $attcontenttype =~ s/^(.+);.*/$1/g;
         unless ($attfilename =~ s/^.+name="?([^"]+)"?.*$/$1/ig) {
            $attfilename = "Unknown.html";
         }
         $attfilename = decode_mimewords($attfilename);
         $attheader = decode_mimewords($attheader);
         $temphash{filename} = $attfilename;
         $temphash{contenttype} = $attcontenttype || 'text/plain';
         $temphash{encoding} = $currentencoding;
         $temphash{header} = $attheader;
         $temphash{contents} = $currentbody;
         $currentbody = " ";
         $attachment[0] = \%temphash;
      }

      $currentfrom = decode_mimewords($currentfrom);
      $currentto = decode_mimewords($currentto);
      $currentcc = decode_mimewords($currentcc);
      $currentreplyto = decode_mimewords($currentreplyto);
      $currentsubject = decode_mimewords($currentsubject);

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
   my ($currentheader, $currentbody);
   my $currentmessageid;
   my $spool = '';
   my $spoolfile;
   if ($folder eq 'INBOX') {
      if ($homedirspools eq "yes") {
         $spoolfile = "$homedir/$homedirspoolname";
      } elsif ($hashedmailspools eq "yes") {
         $user =~ /^(.)(.)/;
         my $firstchar = $1;
         my $secondchar = $2;
         $spoolfile = "$mailspooldir/$firstchar/$secondchar/$user";
      } else {
         $spoolfile = "$mailspooldir/$user";
      }
   } elsif ( ($folder eq 'SAVED') || ($folder eq 'SENT') || 
      ($folder eq 'TRASH') || ($homedirfolders eq 'yes') ) {
      $spoolfile = "$folderdir/$folder";
   } else {
      $spoolfile = "$folderdir/$folder.folder";
   }
   if ( ( ($homedirfolders eq 'yes') || ($homedirspools eq 'yes') ) && ($> == 0) ) {
      $) = $gid;
      $> = $uid;
   }
   open (SPOOL, "+<$spoolfile") or neomailerror("$lang_err{'couldnt_open'} $spoolfile!");
   unless (flock(SPOOL, 2)) {
      neomailerror("$lang_err{'couldnt_lock'} $spoolfile!");
   }

   $/ = undef;  # Force a single input to grab the whole spool
   $spool = <SPOOL>;
   $/ = "\n";
   
   seek (SPOOL, 0, 0) or neomailerror("$lang_err{'couldnt_seek'} $spoolfile!");

   foreach my $currmessage (split(/\nFrom /, $spool)) {
      $currentmessageid = '';
      ($currentheader, $currentbody) = split(/\n\r*\n/,$currmessage, 2);
      if ($currentheader =~ /^message-id:[\s\n]+([^\s\n]+?)$/im) {
         $currentmessageid = $1;
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
   close (SPOOL) or neomailerror("$lang_err{'couldnt_close'} $spoolfile!");
}
################### END UPDATESTATUS ######################

#################### MOVEMESSAGE ########################
sub movemessage {
   verifysession();
   my $destination = param("destination");
   ($destination =~ /(.+)/) && ($destination = $1);
   my @messageids = param("message_ids");
   my $messageids = join("\n", @messageids);
   my $spool = '';
   my $spoolfile;
   neomailerror ("$lang_err{'shouldnt_move_here'}") if 
      (($folder eq $destination) || ($destination eq 'INBOX'));

   unless ( ($destination eq 'TRASH') || ($destination eq 'SAVED') ||
        ($destination eq 'SENT') || ($destination eq 'sent-mail') ||
        ($destination eq 'saved-messages') ||
        ($destination eq 'neomail-trash') ) {
      $destination .= ".folder" unless ( $homedirfolders eq 'yes' );
      neomailerror("$lang_err{'destination_folder'} $destination $lang_err{'doesnt_exist'}") unless 
         ( -f "$folderdir/$destination" );
   }

   if ($hitquota) {
      unless ( ($destination eq 'TRASH') || ($destination eq 'neomail-trash') ){
         neomailerror("$lang_err{'folder_hitquota'}");
      }
   }

   if ($folder eq 'INBOX') {
      if ($homedirspools eq "yes") {
         $spoolfile = "$homedir/$homedirspoolname";
      } elsif ($hashedmailspools eq "yes") {
         $user =~ /^(.)(.)/;
         my $firstchar = $1;
         my $secondchar = $2;
         $spoolfile = "$mailspooldir/$firstchar/$secondchar/$user";
      } else {
         $spoolfile = "$mailspooldir/$user";
      }
   } elsif ( ($folder eq 'SAVED') || ($folder eq 'SENT') || 
      ($folder eq 'TRASH') || ($homedirfolders eq 'yes') ) {
      $spoolfile = "$folderdir/$folder";
   } else {
      $spoolfile = "$folderdir/$folder.folder";
   }

   my $currmessage;
   if ( ( ($homedirfolders eq 'yes') || ($homedirspools eq 'yes') ) && ($> == 0) ) {
      $) = $gid;
      $> = $uid;
   }
   open (SPOOL, "+<$spoolfile") or neomailerror("$lang_err{'couldnt_open'} $spoolfile!");
   unless (flock(SPOOL, 2)) {
      neomailerror("$lang_err{'couldnt_lock'} $spoolfile!");
   }
   $/ = undef; # Force a single input to grab the whole spool
   $spool = <SPOOL>;
   $/ = "\n";

   seek (SPOOL, 0, 0) or neomailerror("$lang_err{'couldnt_seek'} $spoolfile!");

   foreach my $currmessage (split(/\nFrom /, $spool)) {
      my $currentmessageid = '';
      if ($currmessage =~ /^message-id:[\s\n]+([^\s\n]+?)$/im) {
         $currentmessageid = $1;
      }
      if ($messageids =~ /^\Q$currentmessageid\E$/m) {
         unless ($hitquota) {
            open (DEST, ">>$folderdir/$destination") or
               neomailerror ("$lang_err{'couldnt_open'} $destination!");
               unless (flock(DEST, 2)) {
                  neomailerror("$lang_err{'couldnt_lock'} $destination!");
               }
            if ($currmessage =~ /^From /) {
               print DEST "$currmessage\n";
            } else {
               print DEST "From $currmessage\n";
            }
            close (DEST) or neomailerror("$lang_err{'couldnt_close'} $destination!");
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

   close (SPOOL) or neomailerror("$lang_err{'couldnt_close'} $spoolfile!");
   $messageids =~ s/\n/, /g;
   writelog("moved messages to $destination - ids=$messageids");
   if (param("messageaftermove")) {
      readmessage();
   } else {
      displayheaders();
   }
}
#################### END MOVEMESSAGE #######################

#################### EMPTYTRASH ########################
sub emptytrash {
   verifysession();

   my $trashfile;
   if ( $homedirfolders eq 'yes' ) {
      $trashfile = "$folderdir/neomail-trash";
   } else {
      $trashfile = "$folderdir/TRASH";
   }
   if ( ($homedirfolders eq 'yes') && ($> == 0) ) {
      $) = $gid;
      $> = $uid;
   }
   open (TRASH, ">$trashfile") or
      neomailerror ("$lang_err{'couldnt_open'} $trashfile!");
   close (TRASH) or neomailerror("$lang_err{'couldnt_close'} $trashfile!");
   writelog("trash emptied");
   displayheaders();
}
#################### END EMPTYTRASH #######################

###################### ENCODING/DECODING ##############################
# Most of this code is blatantly snatched from parts of the MIME-Tools
# Perl modules, by the talented Eryq, and particularly code contributed to
# them by Gisle Aas

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

sub decode_mimewords {
    my $encstr = shift;
    my %params = @_;
    my @tokens;
    $@ = '';           # error-return

    # Collapse boundaries between adjacent encoded words:
    $encstr =~ s{(\?\=)[\r\n \t]*(\=\?)}{$1$2}gs;
    pos($encstr) = 0;
    ### print STDOUT "ENC = [", $encstr, "]\n";

    # Decode:
    my ($charset, $encoding, $enc, $dec);
    while (1) {
        last if (pos($encstr) >= length($encstr));
        my $pos = pos($encstr);               # save it

        # Case 1: are we looking at "=?..?..?="?
        if ($encstr =~    m{\G                # from where we left off..
                            =\?([^?]*)        # "=?" + charset +
                             \?([bq])         #  "?" + encoding +
                             \?([^?]+)        #  "?" + data maybe with spcs +
                             \?=              #  "?="
                            }xgi) {
            ($charset, $encoding, $enc) = ($1, lc($2), $3);
            $dec = (($encoding eq 'q') ? _decode_Q($enc) : _decode_B($enc));
            push @tokens, [$dec, $charset];
            next;
        }

        # Case 2: are we looking at a bad "=?..." prefix?
        # We need this to detect problems for case 3, which stops at "=?":
        pos($encstr) = $pos;               # reset the pointer.
        if ($encstr =~ m{\G=\?}xg) {
            $@ .= qq|unterminated "=?..?..?=" in "$encstr" (pos $pos)\n|;
            push @tokens, ['=?'];
            next;
        }

        # Case 3: are we looking at ordinary text?
        pos($encstr) = $pos;               # reset the pointer.
        if ($encstr =~ m{\G                # from where we left off...
                         ([\x00-\xFF]*?    #   shortest possible string,
                          \n*)             #   followed by 0 or more NLs,
                         (?=(\Z|=\?))      # terminated by "=?" or EOS
                        }xg) {
            length($1) or die "MIME::Words: internal logic err: empty token\n";
            push @tokens, [$1];
            next;
        }

        # Case 4: bug!
        die "MIME::Words: unexpected case:\n($encstr) pos $pos\n\t".
            "Please alert developer.\n";
    }
    return (wantarray ? @tokens : join('',map {$_->[0]} @tokens));
}

sub _decode_Q {
    my $str = shift;
    $str =~ s/=([\da-fA-F]{2})/pack("C", hex($1))/ge;  # RFC-1522, Q rule 1
    $str =~ s/_/\x20/g;                                # RFC-1522, Q rule 2
    $str;
}

sub _decode_B {
    my $str = shift;
    decode_base64($str);
}

################### END ENCODING/DECODING ##########################

##################### GETATTLIST ###############################
sub getattlist {
   my $currentfile;
   my @attlist;
   $savedattsize = 0;
   opendir (NEOMAILDIR, "$neomaildir") or
      neomailerror("$lang_err{'couldnt_open'} $neomaildir!");
   while (defined($currentfile = readdir(NEOMAILDIR))) {
      if ($currentfile =~ /^($thissession-att\d+)$/) {
         $currentfile = $1;
         $savedattsize += ( -s "$neomaildir$currentfile" );
         open (ATTFILE, "$neomaildir$currentfile");
         while (defined(my $line = <ATTFILE>)) {
            if ($line =~ s/^.+name="?([^"]+)"?.*$/$1/i) {
               $line =~ s/&/&amp;/g;
               $line =~ s/\"/&quot;/g;
               $line =~ s/</&lt;/g;
               $line =~ s/>/&gt;/g;
               $line =~ s/^(.*)$/<em>$1<\/em>/;
               push (@attlist, $line);
               last;
            }
         }
         close (ATTFILE);
      }
   }
   closedir (NEOMAILDIR);
   return \@attlist;
}
##################### END GETATTLIST ###########################

##################### DELETEATTACHMENTS ############################
sub deleteattachments {
   my $currentfile;
   opendir (NEOMAILDIR, "$neomaildir") or
      neomailerror("$lang_err{'couldnt_open'} $neomaildir!");
   while (defined($currentfile = readdir(NEOMAILDIR))) {
      if ($currentfile =~ /^($thissession-att\d+)$/) {
         $currentfile = $1;
         unlink ("$neomaildir$currentfile");
      }
   }
   closedir (NEOMAILDIR);
}
#################### END DELETEATTACHMENTS #########################

##################### FIRSTTIMEUSER ################################
sub firsttimeuser {
   my $html = '';
   my $temphtml;
   open (FTUSER, "$neomaildir/templates/$lang/firsttimeuser.template") or
      neomailerror("$lang_err{'couldnt_open'} firsttimeuser.template!");
   while (<FTUSER>) {
      $html .= $_;
   }
   close (FTUSER);
   
   $html = applystyle($html);

   printheader();

   $temphtml = startform(-action=>"$prefsurl");
   $temphtml .= hidden(-name=>'sessionid',
                       -default=>$thissession,
                       -override=>'1');
   $temphtml .= hidden(-name=>'firsttimeuser',
                       -default=>'yes',
                       -override=>'1');
   $temphtml .= hidden(-name=>'realname',
                       -default=>(split(/,/,(getpwnam($user))[6]))[0] || "Your Name",
                       -override=>'1');
   $temphtml .= submit("$lang_text{'continue'}");
   $temphtml .= end_form();

   $html =~ s/\@\@\@CONTINUEBUTTON\@\@\@/$temphtml/;
   
   print $html;

   printfooter();
}
################### END FIRSTTIMEUSER ##############################

###################### READPREFS #########################
sub readprefs {
   my ($key,$value);
   my %prefshash;
   if ( -f "$userprefsdir$user/config" ) {
      open (CONFIG,"$userprefsdir$user/config") or
         neomailerror("$lang_err{'couldnt_open'} config!");
      while (<CONFIG>) {
         ($key, $value) = split(/=/, $_);
         chomp($value);
         if ($key eq 'style') {
            $value =~ s/\.//g;  ## In case someone gets a bright idea...
         }
         $prefshash{"$key"} = $value;
      }
      close (CONFIG) or neomailerror("$lang_err{'couldnt_close'} config!");
   }
   if ( -f "$userprefsdir$user/signature" ) {
      $prefshash{"signature"} = '';
      open (SIGNATURE, "$userprefsdir$user/signature") or
         neomailerror("$lang_err{'couldnt_open'} signature!");
      while (<SIGNATURE>) {
         $prefshash{"signature"} .= $_;
      }
      close (SIGNATURE) or neomailerror("$lang_err{'couldnt_close'} signature!");
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
      neomailerror("$lang_err{'couldnt_open'} $stylefile!");
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
   close (STYLE) or neomailerror("$lang_err{'couldnt_close'} $stylefile!");
   return \%stylehash;
}
##################### END READSTYLE ######################

##################### WRITELOG ############################
sub writelog {
   unless ( ($logfile eq 'no') || ( -l "$logfile" ) ) {
      open (LOGFILE,">>$logfile") or neomailerror("$lang_err{'couldnt_open'} $logfile!");
      my $timestamp = localtime();
      my $logaction = shift;
      my $loggeduser = $user || 'UNKNOWNUSER';
      print LOGFILE "$timestamp - [$$] ($ENV{REMOTE_ADDR}) $loggeduser - $logaction\n";
      close (LOGFILE);
   }
}
#################### END WRITELOG #########################

##################### NEOMAILERROR ##########################
sub neomailerror {
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
   print '<BR><BR><BR><BR><BR><BR>';
   print '<table border="0" align="center" width="40%" cellpadding="1" cellspacing="1">';

   print '<tr><td bgcolor=',$style{"titlebar"},' align="left">',
   '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>NEOMAIL ERROR</b></font>',
   '</td></tr><tr><td align="center" bgcolor=',$style{"window_light"},'><BR>';
   print shift;
   print '<BR><BR></td></tr></table>';
   print '<p align="center"><font size="1"><BR>
          <a href="http://neomail.sourceforge.net">
          NeoMail</a> version ', $version,'<BR>
          </FONT></FONT></P></BODY></HTML>';
   exit 0;
}
################### END NEOMAILERROR #######################

##################### PRINTHEADER #########################
sub printheader {
   my $cookie;
   unless ($headerprinted) {
      if ($setcookie) {
         $cookie = cookie( -name    => 'sessionid',
                           -"value" => $setcookie,
                           -path    => '/' );
      }
      my $html = '';
      $headerprinted = 1;
      open (HEADER, "$neomaildir/templates/$lang/header.template") or
         neomailerror("$lang_err{'couldnt_open'} header.template!");
      while (<HEADER>) {
         $html .= $_;
      }
      close (HEADER);

      $html = applystyle($html);

      $html =~ s/\@\@\@BG_URL\@\@\@/$bg_url/g;
      if ($setcookie) {
         print header(-pragma=>'no-cache',
                      -cookie=>$cookie);
      } else {
         print header(-pragma=>'no-cache');
      }
      print $html;
   }
}
################### END PRINTHEADER #######################

################### PRINTFOOTER ###########################
sub printfooter {
   my $html = '';
   open (FOOTER, "$neomaildir/templates/$lang/footer.template") or
      neomailerror("$lang_err{'couldnt_open'} footer.template!");
   while (<FOOTER>) {
      $html .= $_;
   }
   close (FOOTER);
   
   $html = applystyle($html);
   
   $html =~ s/\@\@\@VERSION\@\@\@/$version/g;
   print $html;
}
################# END PRINTFOOTER #########################

################# APPLYSTYLE ##############################
sub applystyle {
   my $template = shift;
   $template =~ s/\@\@\@LOGO_URL\@\@\@/$logo_url/g;
   $template =~ s/\@\@\@BACKGROUND\@\@\@/$style{"background"}/g;
   $template =~ s/\@\@\@TITLEBAR\@\@\@/$style{"titlebar"}/g;
   $template =~ s/\@\@\@TITLEBAR_TEXT\@\@\@/$style{"titlebar_text"}/g;
   $template =~ s/\@\@\@MENUBAR\@\@\@/$style{"menubar"}/g;
   $template =~ s/\@\@\@WINDOW_DARK\@\@\@/$style{"window_dark"}/g;
   $template =~ s/\@\@\@WINDOW_LIGHT\@\@\@/$style{"window_light"}/g;
   $template =~ s/\@\@\@ATTACHMENT_DARK\@\@\@/$style{"attachment_dark"}/g;
   $template =~ s/\@\@\@ATTACHMENT_LIGHT\@\@\@/$style{"attachment_light"}/g;
   $template =~ s/\@\@\@COLUMNHEADER\@\@\@/$style{"columnheader"}/g;
   $template =~ s/\@\@\@TABLEROW_LIGHT\@\@\@/$style{"tablerow_light"}/g;
   $template =~ s/\@\@\@TABLEROW_DARK\@\@\@/$style{"tablerow_dark"}/g;
   $template =~ s/\@\@\@FONTFACE\@\@\@/$style{"fontface"}/g;
   $template =~ s/\@\@\@SCRIPTURL\@\@\@/$scripturl/g;
   $template =~ s/\@\@\@PREFSURL\@\@\@/$prefsurl/g;
   $template =~ s/\@\@\@CSS\@\@\@/$style{"css"}/g;
   $template =~ s/\@\@\@VERSION\@\@\@/$version/g;

   return $template;
}
################ END APPLYSTYLE ###########################
