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
push (@INC, '/var/neomail/mail.namodn.com');
use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser);

CGI::nph();   # Treat script as a non-parsed-header script

$ENV{PATH} = ""; # no PATH should be needed

require "neomail.conf";

my $version = "1.14";

my $thissession = param("sessionid") || '';
my $user = $thissession || '';
$user =~ s/\-session\-0.*$//; # Grab userid from sessionid
($user =~ /^(.+)$/) && ($user = $1);  # untaint $user...

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
   $sort = 'date';
}

my $folderdir;
if ( $homedirfolders eq 'yes') {
   $folderdir = "$homedir/mail";
} else {
   $folderdir = "$userprefsdir/$user";
}

my $folder;
if (param("folder")) {
   $folder = param("folder");
} else {
   $folder = "INBOX";
}
my $printfolder = $lang_folders{$folder} || $folder;
my $escapedfolder = CGI::escape($folder);

my $firsttimeuser = param("firsttimeuser") || ''; # Don't allow cancel if 'yes'

$sessiontimeout = $sessiontimeout/60/24; # convert to format expected by -M

# once we print the header, we don't want to do it again if there's an error
my $headerprinted = 0;
my $validsession = 0;

########################## MAIN ##############################
if (defined(param("action"))) {      # an action has been chosen
   my $action = param("action");
   if ($action =~ /^(\w+)$/) {
      $action = $1;
      if ($action eq "saveprefs") {
         saveprefs();
      } elsif ($action eq "addressbook") {
         addressbook();
      } elsif ($action eq "editfolders") {
         editfolders();
      } elsif ($action eq "addfolder") {
         addfolder();
      } elsif ($action eq "deletefolder") {
         deletefolder();
      } elsif ($action eq "editaddresses") {
         editaddresses();
      } elsif ($action eq "importabook") {
         importabook();
      } elsif ($action eq "addaddress") {
         modaddress("add");
      } elsif ($action eq "deleteaddress") {
         modaddress("delete");
      } else {
         neomailerror("Action $lang_err{'has_illegal_chars'}");
      }
   } else {
      neomailerror("Action $lang_err{'has_illegal_chars'}");
   }
} else {            # no action has been taken, display prefs page
   verifysession();

   my $html = '';
   my $temphtml;

   open (PREFSTEMPLATE, "$neomaildir/templates/$lang/prefs.template") or
      neomailerror("$lang_err{'couldnt_open'} prefs.template");
   while (<PREFSTEMPLATE>) {
      $html .= $_;
   }
   close (PREFSTEMPLATE);

   $html = applystyle($html);

   my @styles;
   printheader();

### Get a list of valid style files
   opendir (STYLESDIR, $stylesdir) or
      neomailerror("$lang_err{'couldnt_open'} $stylesdir directory for reading!");
   while (defined(my $currentstyle = readdir(STYLESDIR))) {
      unless ($currentstyle =~ /\./) {
         push (@styles, $currentstyle);
      }
   }
   @styles = sort(@styles);
   closedir(STYLESDIR) or
      neomailerror("$lang_err{'couldnt_close'} $stylesdir!");
   $temphtml = start_form(-action=>$prefsurl);
   $temphtml .= hidden(-name=>'action',
                       -default=>'saveprefs',
                       -override=>'1');
   $temphtml .= hidden(-name=>'sessionid',
                       -default=>$thissession,
                       -override=>'1');
   $temphtml .= hidden(-name=>'firstmessage',
                       -default=>$firstmessage,
                       -override=>'1');
   $temphtml .= hidden(-name=>'folder',
                       -default=>$folder,
                       -override=>'1');

   $html =~ s/\@\@\@STARTPREFSFORM\@\@\@/$temphtml/;

   if (param("realname")) {
      $prefs{"realname"} = param("realname");
   }
   if ($prefs{"realname"}) {
      $temphtml = " $lang_text{'for'} " . uc($prefs{"realname"});
   } else {
      $temphtml = '';
   }

   $html =~ s/\@\@\@REALNAME\@\@\@/$temphtml/;

   $temphtml = popup_menu(-name=>'language',
                          -"values"=>\@availablelanguages,
                          -default=>$prefs{"language"} || $defaultlanguage,
                          -labels=>\%languagenames,
                          -override=>'1');

   $html =~ s/\@\@\@LANGUAGEFIELD\@\@\@/$temphtml/;

   $temphtml = textfield(-name=>'realname',
                         -default=>$prefs{"realname"} || $lang_text{'yourname'},
                         -size=>'40',
                         -override=>'1');

   $html =~ s/\@\@\@REALNAMEFIELD\@\@\@/$temphtml/;

   $temphtml = textfield(-name=>'fromname',
                         -default=>$prefs{"fromname"} || $user,
                         -size=>'15',
                         -override=>'1');

   $html =~ s/\@\@\@USERNAME\@\@\@/$temphtml/;

   $temphtml = popup_menu(-name=>'domainname',
                          -"values"=>\@domainnames,
                          -default=>$prefs{"domainname"} || $domainnames[0],
                          -override=>'1');

   $html =~ s/\@\@\@DOMAINFIELD\@\@\@/$temphtml/;

   $temphtml = textfield(-name=>'replyto',
                         -default=>$prefs{"replyto"} || '',
                         -size=>'40',
                         -override=>'1');

   $html =~ s/\@\@\@REPLYTOFIELD\@\@\@/$temphtml/;
   
   $temphtml = popup_menu(-name=>'style',
                          -"values"=>\@styles,
                          -default=>$prefs{"style"} || 'Default',
                          -override=>'1');

   $html =~ s/\@\@\@STYLEMENU\@\@\@/$temphtml/;

   $temphtml = popup_menu(-name=>'sort',
                          -"values"=>['date','date_rev','sender','sender_rev',
                                      'size','size_rev','subject','subject_rev'],
                          -default=>$prefs{"sort"} || 'date',
                          -labels=>\%lang_sortlabels,
                          -override=>'1');

   $html =~ s/\@\@\@SORTMENU\@\@\@/$temphtml/;

   $temphtml = popup_menu(-name=>'numberofmessages',
                          -"values"=>['10','20','30','40','50','100'],
                          -default=>$prefs{"numberofmessages"} || $numberofheaders,
                          -override=>'1');

   $html =~ s/\@\@\@NUMBEROFMESSAGES\@\@\@/$temphtml/;

   my %headerlabels = ('simple'=>$lang_text{'simplehead'},
                       'all'=>$lang_text{'allhead'}
                      );
   $temphtml = popup_menu(-name=>'headers',
                          -"values"=>['simple','all'],
                          -default=>$prefs{"headers"} || 'simple',
                          -labels=>\%headerlabels,
                          -override=>'1');
   
   $html =~ s/\@\@\@HEADERSMENU\@\@\@/$temphtml/;

   unless (defined($prefs{"signature"})) {
      $prefs{"signature"} = "-- \nNeoMail - Webmail that doesn't suck... as much.\nhttp://neomail.sourceforge.net";
   }
   $temphtml = textarea(-name=>'signature',
                        -default=>$prefs{"signature"},
                        -rows=>'5',
                        -columns=>'72',
                        -wrap=>'hard',
                        -override=>'1');

   $html =~ s/\@\@\@SIGAREA\@\@\@/$temphtml/;

   $temphtml = submit("$lang_text{'save'}") . end_form();

   unless ( $firsttimeuser eq 'yes' ) {
      $temphtml .= startform(-action=>"$scripturl");
      $temphtml .= hidden(-name=>'action',
                          -default=>'displayheaders',
                          -override=>'1');
      $temphtml .= hidden(-name=>'sessionid',
                          -default=>$thissession,
                          -override=>'1');
      $temphtml .= hidden(-name=>'sort',
                          -default=>$sort,
                          -override=>'1');
      $temphtml .= hidden(-name=>'firstmessage',
                          -default=>$firstmessage,
                          -override=>'1');
      $temphtml .= hidden(-name=>'folder',
                          -default=>$folder,
                          -override=>'1') . 
                   '</td><td>' . 
                   submit("$lang_text{'cancel'}") . end_form();
   }

   $html =~ s/\@\@\@BUTTONS\@\@\@/$temphtml/;

   print $html;

   printfooter();
}
###################### END MAIN ##############################

#################### EDITFOLDERS ###########################
sub editfolders {
   verifysession();
   my @folders;
   opendir (FOLDERDIR, "$folderdir") or
      neomailerror("$lang_err{'couldnt_open'} $folderdir!");
   while (defined(my $filename = readdir(FOLDERDIR))) {
      if ($homedirfolders eq 'yes') {
         unless ( ($filename eq 'saved-messages') ||
                  ($filename eq 'sent-mail') ||
                  ($filename eq 'neomail-trash') ||
                  ($filename eq '.') ||
                  ($filename eq '..')
                ) {
            push (@folders, $filename);
         }
      } else {
         if ($filename =~ /^(.+)\.folder$/) {
            push (@folders, $1);
         }
      }
   }
   closedir (FOLDERDIR) or
      neomailerror("$lang_err{'couldnt_close'} $folderdir!");

   my $html = '';
   my $temphtml;

   open (EDITFOLDERSTEMPLATE, "$neomaildir/templates/$lang/editfolders.template") or
      neomailerror("$lang_err{'couldnt_open'} editfolders.template!");
   while (<EDITFOLDERSTEMPLATE>) {
      $html .= $_;
   }
   close (EDITFOLDERSTEMPLATE);

   $html = applystyle($html);

   printheader();

   $temphtml = "<a href=\"$scripturl?action=displayheaders&amp;sessionid=$thissession&amp;sort=$sort&amp;firstmessage=$firstmessage&amp;folder=$escapedfolder\"><IMG SRC=\"$image_url/backtofolder.gif\" border=\"0\" ALT=\"$lang_text{'backto'} $printfolder\"></a>";

   $html =~ s/\@\@\@MENUBARLINKS\@\@\@/$temphtml/g;

   $temphtml = start_form(-action=>$prefsurl) .
               hidden(-name=>'action',
                      -value=>'addfolder',
                      -override=>'1') .
               hidden(-name=>'sessionid',
                      -value=>$thissession,
                      -override=>'1') .
               hidden(-name=>'sort',
                      -default=>$sort,
                      -override=>'1') .
               hidden(-name=>'firstmessage',
                      -default=>$firstmessage,
                      -override=>'1') .
               hidden(-name=>'folder',
                      -default=>$folder,
                      -override=>'1');

   $html =~ s/\@\@\@STARTFOLDERFORM\@\@\@/$temphtml/;

   $temphtml = textfield(-name=>'foldername',
                         -default=>'',
                         -size=>'16',
                         -maxlength=>'16',
                         -override=>'1');

   $html =~ s/\@\@\@FOLDERNAMEFIELD\@\@\@/$temphtml/;
   
   $temphtml = submit("$lang_text{'add'}");
   $html =~ s/\@\@\@ADDBUTTON\@\@\@/$temphtml/;

   $temphtml = end_form();
   $html =~ s/\@\@\@ENDFORM\@\@\@/$temphtml/;

   $temphtml = '';
   my $bgcolor = $style{"tablerow_dark"};
   my $currfolder;
   foreach $currfolder (sort (@folders)) {
      $temphtml .= "<tr><td align=\"center\" bgcolor=$bgcolor>$currfolder</td>";

      $temphtml .= start_form(-action=>$prefsurl,
                              -onSubmit=>"return confirm($lang_text{'folderconf'})");
      $temphtml .= hidden(-name=>'action',
                          -value=>'deletefolder',
                          -override=>'1');
      $temphtml .= hidden(-name=>'sessionid',
                          -value=>$thissession,
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
      $temphtml .= hidden(-name=>'foldername',
                          -value=>$currfolder,
                          -override=>'1');
      $temphtml .= "<td bgcolor=$bgcolor align=\"center\">";
      $temphtml .= submit("$lang_text{'delete'}");
      $temphtml .= '</td></tr>';
      $temphtml .= end_form();
      if ($bgcolor eq $style{"tablerow_dark"}) {
         $bgcolor = $style{"tablerow_light"};
      } else {
         $bgcolor = $style{"tablerow_dark"};
      }
   }
   
   $html =~ s/\@\@\@FOLDERS\@\@\@/$temphtml/;
   print $html;

   printfooter();
}
################### END EDITFOLDERS ########################

################### ADDFOLDER ##############################
sub addfolder {
   my $foldertoadd = param('foldername') || '';
   $foldertoadd =~ s/[\.\.|\/|\\|\`|;|<|>]//g;
   unless ($homedirfolders eq 'yes') {
      $foldertoadd = uc($foldertoadd);
   }
   if (length($foldertoadd) > 16) {
      neomailerror("$lang_err{'foldername_long'}");
   }
   ($foldertoadd =~ /^(.+)$/) && ($foldertoadd = $1);
   unless ($homedirfolders eq 'yes') {
      $foldertoadd .= '.folder';
   }
   if ( -f "$folderdir/$foldertoadd" ) {
      neomailerror ("$lang_err{'folder_with_name'} $foldertoadd $lang_err{'already_exists'}");
   }
   if ( ($homedirfolders eq 'yes') && ($> == 0) ) {
      $) = $gid;
      $> = $uid;
   }
   open (FOLDERTOADD, ">$folderdir/$foldertoadd") or
      neomailerror("$lang_err{'cant_create_folder'}");
   close (FOLDERTOADD) or neomailerror("$lang_err{'couldnt_close'} $foldertoadd!");
   print "Location: $prefsurl?action=editfolders&sessionid=$thissession&sort=$sort&folder=$escapedfolder&firstmessage=$firstmessage\n\n";
}
################### END ADDFOLDER ##########################

################### DELETEFOLDER ##############################
sub deletefolder {
   my $foldertodel = param('foldername') || '';
   $foldertodel =~ s/[\.\.|\/|\\|\`|;|<|>]//g;
   ($foldertodel =~ /^(.+)$/) && ($foldertodel = $1);
   unless ($homedirfolders eq 'yes') {
      $foldertodel .= '.folder';
   }
   if ( -f "$folderdir/$foldertodel" ) {
      unlink ("$folderdir/$foldertodel");
   }
   print "Location: $prefsurl?action=editfolders&sessionid=$thissession&sort=$sort&folder=$escapedfolder&firstmessage=$firstmessage\n\n";
}
################### END DELETEFOLDER ##########################

#################### EDITADDRESSES ###########################
sub editaddresses {
   verifysession();
   my %addresses;
   my ($name, $email);

   my $html = '';
   my $temphtml;

   open (EDITABOOKTEMPLATE, "$neomaildir/templates/$lang/editaddresses.template") or
      neomailerror("$lang_err{'couldnt_open'} editaddresses.template");
   while (<EDITABOOKTEMPLATE>) {
      $html .= $_;
   }
   close (EDITABOOKTEMPLATE);

   $html = applystyle($html);

   if ( -f "$userprefsdir$user/addressbook" ) {
      open (ABOOK,"$userprefsdir$user/addressbook") or
         neomailerror("$lang_err{'couldnt_open'} addressbook!");
      while (<ABOOK>) {
         ($name, $email) = split(/:/, $_);
         chomp($email);
         $addresses{"$name"} = $email;
      }
      close (ABOOK) or neomailerror("$lang_err{'couldnt_close'} addressbook!");
   }
   my $abooksize = ( -s "$userprefsdir$user/addressbook" ) || 0;
   my $freespace = int($maxabooksize - ($abooksize/1024) + .5);

   printheader();

   $html =~ s/\@\@\@FREESPACE\@\@\@/$freespace/g;

   $temphtml = "<a href=\"$scripturl?action=displayheaders&amp;sessionid=$thissession&amp;sort=$sort&amp;firstmessage=$firstmessage&amp;folder=$folder\"><IMG SRC=\"$image_url/backtofolder.gif\" border=\"0\" ALT=\"$lang_text{'backto'} $printfolder\"></a> &nbsp; &nbsp; ";
   $temphtml .= "<a href=\"$prefsurl?action=importabook&amp;sessionid=$thissession&amp;sort=$sort&amp;firstmessage=$firstmessage&amp;folder=$folder\"><IMG SRC=\"$image_url/import.gif\" border=\"0\" ALT=\"$lang_text{'importadd'}\"></a>";

   $html =~ s/\@\@\@MENUBARLINKS\@\@\@/$temphtml/g;

   $temphtml = startform(-action=>$prefsurl,
                         -name=>'newaddress') .
               hidden(-name=>'action',
                      -value=>'addaddress',
                      -override=>'1') .
               hidden(-name=>'sessionid',
                      -value=>$thissession,
                      -override=>'1') .
               hidden(-name=>'sort',
                      -default=>$sort,
                      -override=>'1') .
               hidden(-name=>'firstmessage',
                      -default=>$firstmessage,
                      -override=>'1') .
               hidden(-name=>'folder',
                      -default=>$folder,
                      -override=>'1');

   $html =~ s/\@\@\@STARTADDRESSFORM\@\@\@/$temphtml/;

   $temphtml = textfield(-name=>'realname',
                         -default=>'',
                         -size=>'25',
                         -override=>'1');

   $html =~ s/\@\@\@REALNAMEFIELD\@\@\@/$temphtml/;
   
   $temphtml = textfield(-name=>'email',
                         -default=>'',
                         -size=>'25',
                         -override=>'1');

   $html =~ s/\@\@\@EMAILFIELD\@\@\@/$temphtml/;

   $temphtml = submit("$lang_text{'addmod'}");
   $html =~ s/\@\@\@ADDBUTTON\@\@\@/$temphtml/;

   $temphtml = end_form();
   $html =~ s/\@\@\@ENDFORM\@\@\@/$temphtml/;

   $temphtml = '';
   my $bgcolor = $style{"tablerow_dark"};
   foreach my $key (sort { uc($a) cmp uc($b) } (keys %addresses)) {
      $temphtml .= "<tr><td bgcolor=$bgcolor width=\"200\">
                    <a href=\"Javascript:Update('$key','$addresses{$key}')\">
                    $key</a></td><td bgcolor=$bgcolor width=\"200\">
                    <a href=\"$scripturl?action=composemessage&amp;firstmessage=$firstmessage&amp;sort=$sort&amp;folder=$escapedfolder&amp;sessionid=$thissession&amp;composetype=sendto&amp;to=$addresses{$key}\">$addresses{$key}</a></td>";
            
      $temphtml .= start_form(-action=>$prefsurl);
      $temphtml .= hidden(-name=>'action',
                          -value=>'deleteaddress',
                          -override=>'1');
      $temphtml .= hidden(-name=>'sessionid',
                          -value=>$thissession,
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
      $temphtml .= hidden(-name=>'realname',
                          -value=>$key,
                          -override=>'1');
      $temphtml .= "<td bgcolor=$bgcolor align=\"center\" width=\"100\">";
      $temphtml .= submit("$lang_text{'delete'}");
      $temphtml .= '</td></tr>';
      $temphtml .= end_form();
      if ($bgcolor eq $style{"tablerow_dark"}) {
         $bgcolor = $style{"tablerow_light"};
      } else {
         $bgcolor = $style{"tablerow_dark"};
      }
   }
   
   $html =~ s/\@\@\@ADDRESSES\@\@\@/$temphtml/;
   print $html;

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
            neomailerror("$lang_err{'abook_invalid'} <a href=\"$prefsurl?action=importabook&amp;sessionid=$thissession&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage\">$lang_err{'back'}</a> $lang_err{'tryagain'}");
         }
      }
      unless ( -f "$userprefsdir$user/addressbook" ) {
         open (ABOOK, ">>$userprefsdir$user/addressbook"); # Create if nonexistent
         close(ABOOK);
      }
      open (ABOOK,"+<$userprefsdir$user/addressbook") or
         neomailerror("$lang_err{'couldnt_open'} addressbook!");
      unless (flock(ABOOK, 2)) {
         neomailerror("$lang_err{'couldnt_lock'} addressbook!");
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
         neomailerror("$lang_err{'couldnt_seek'} addressbook!");

      while ( ($name, $email) = each %addresses ) {
         $abooktowrite .= "$name:$email\n";
      }

      if (length($abooktowrite) > ($maxabooksize * 1024)) {
         neomailerror("$lang_err{'abook_toobig'}
                       <a href=\"$prefsurl?action=importabook&amp;sessionid=$thissession&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage\">$lang_err{'back'}</a>
                       $lang_err{'tryagain'}");
      }
      print ABOOK $abooktowrite;
      truncate(ABOOK, tell(ABOOK));
      close (ABOOK) or neomailerror("$lang_err{'couldnt_close'} addressbook!");

      print "Location: $prefsurl?action=editaddresses&sessionid=$thissession&sort=$sort&folder=$escapedfolder&firstmessage=$firstmessage\n\n";

   } else {

      my $abooksize = ( -s "$userprefsdir$user/addressbook" ) || 0;
      my $freespace = int($maxabooksize - ($abooksize/1024) + .5);

      my $html = '';
      my $temphtml;

      open (IMPORTTEMPLATE, "$neomaildir/templates/$lang/importabook.template") or
         neomailerror("$lang_err{'couldnt_open'} importabook.template");
      while (<IMPORTTEMPLATE>) {
         $html .= $_;
      }
      close (IMPORTTEMPLATE);

      $html = applystyle($html);

      printheader();

      $html =~ s/\@\@\@FREESPACE\@\@\@/$freespace/g;

      $temphtml = start_multipart_form();
      $temphtml .= hidden(-name=>'action',
                          -value=>'importabook',
                          -override=>'1') .
                   hidden(-name=>'sessionid',
                          -value=>$thissession,
                          -override=>'1') .
                   hidden(-name=>'sort',
                          -default=>$sort,
                          -override=>'1') .
                   hidden(-name=>'firstmessage',
                          -default=>$firstmessage,
                          -override=>'1') .
                   hidden(-name=>'folder',
                          -default=>$folder,
                          -override=>'1');
      $html =~ s/\@\@\@STARTIMPORTFORM\@\@\@/$temphtml/;

      $temphtml = radio_group(-name=>'mua',
                              -"values"=>['outlookexp5','nsmail'],
                              -default=>'outlookexp5',
                              -labels=>\%lang_mualabels);
      $html =~ s/\@\@\@MUARADIOGROUP\@\@\@/$temphtml/;

      $temphtml = filefield(-name=>'abook',
                            -default=>'',
                            -size=>'30',
                            -override=>'1');
      $html =~ s/\@\@\@IMPORTFILEFIELD\@\@\@/$temphtml/;

      $temphtml = submit("$lang_text{'import'}");
      $html =~ s/\@\@\@IMPORTBUTTON\@\@\@/$temphtml/;

      $temphtml = end_form();
      $html =~ s/\@\@\@ENDFORM\@\@\@/$temphtml/g;

      $temphtml = start_form(-action=>$prefsurl) .
                  hidden(-name=>'action',
                         -value=>'editaddresses',
                         -override=>'1') .
                  hidden(-name=>'sessionid',
                         -value=>$thissession,
                         -override=>'1') .
                  hidden(-name=>'sort',
                         -default=>$sort,
                         -override=>'1') .
                  hidden(-name=>'folder',
                         -default=>$folder,
                         -override=>'1') .
                  hidden(-name=>'firstmessage',
                         -default=>$firstmessage,
                         -override=>'1');
      $html =~ s/\@\@\@STARTCANCELFORM\@\@\@/$temphtml/;


      $temphtml = submit("$lang_text{'cancel'}");
      $html =~ s/\@\@\@CANCELBUTTON\@\@\@/$temphtml/;

      print $html;

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
         if ( (($abooksize + length($realname) + length($address) + 2) >= ($maxabooksize * 1024) ) && ($mode ne "delete") ) {
            neomailerror("$lang_err{'abook_toobig'} <a href=\"$prefsurl?action=editaddresses&amp;sessionid=$thissession&amp;sort=$sort&amp;folder=$escapedfolder&amp;firstmessage=$firstmessage\">$lang_err{'back'}</a>
                          $lang_err{'tryagain'}");
         }
         open (ABOOK,"+<$userprefsdir$user/addressbook") or
            neomailerror("$lang_err{'couldnt_open'} addressbook!");
         unless (flock(ABOOK, 2)) {
            neomailerror("$lang_err{'couldnt_lock'} addressbook!");
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
            neomailerror("$lang_err{'couldnt_seek'} addressbook!");
         while ( ($name, $email) = each %addresses ) {
            print ABOOK "$name:$email\n";
         }
         truncate(ABOOK, tell(ABOOK));
         close (ABOOK) or neomailerror("$lang_err{'couldnt_close'} addressbook!");
      } else {
         open (ABOOK, ">$userprefsdir$user/addressbook" ) or
            neomailerror("$lang_err{'couldnt_open'} addressbook!");
         print ABOOK "$realname:$address\n";
         close (ABOOK) or neomailerror("$lang_err{'couldnt_close'} addressbook!");
      }
   }
   print "Location: $prefsurl?action=editaddresses&sessionid=$thissession&sort=$sort&folder=$escapedfolder&firstmessage=$firstmessage\n\n";
}
################## END MODADDRESS ###########################

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

###################### SAVEPREFS #########################
sub saveprefs {
   verifysession();
   unless ( -d "$userprefsdir$user" ) {
      mkdir ("$userprefsdir$user", oct(700)) or
         neomailerror("$lang_err{'cant_create_dir'}");
   }
   open (CONFIG,">$userprefsdir$user/config") or
      neomailerror("$lang_err{'couldnt_open'} config!");
   foreach my $key (qw(realname domainname replyto sort headers style
                       numberofmessages language fromname)) {
      my $value = param("$key") || '';
      $value =~ s/[\n|=|\/|\||\\|\`]//; # Strip out any sort of nastiness.
      if ($key eq 'language') {
         my $validlanguage=0;
         my $currlanguage;
         foreach $currlanguage (@availablelanguages) {
            if ($value eq $currlanguage) {
               print CONFIG "$key=$value\n";
               last;
            }
         }
      } elsif ($key eq 'fromname') {
         $value =~ s/\s+//g; # Spaces will just screw people up.
         print CONFIG "$key=$value\n";
      } else {
         print CONFIG "$key=$value\n";
      }
   }
   close (CONFIG) or neomailerror("$lang_err{'couldnt_close'} config!");
   open (SIGNATURE,">$userprefsdir$user/signature") or
      neomailerror("$lang_err{'couldnt_open'} signature!");
   my $value = param("signature") || '';
   if (length($value) > 500) {  # truncate signature to 500 chars
      $value = substr($value, 0, 500);
   }
   print SIGNATURE $value;
   close (SIGNATURE) or neomailerror("$lang_err{'couldnt_close'} signature!");
   printheader();

   my $html = '';
   my $temphtml;

   open (PREFSSAVEDTEMPLATE, "$neomaildir/templates/$lang/prefssaved.template") or
      neomailerror("$lang_err{'couldnt_open'} prefssaved.template!");
   while (<PREFSSAVEDTEMPLATE>) {
      $html .= $_;
   }
   close (PREFSSAVEDTEMPLATE);

   $html = applystyle($html);

   $temphtml = startform(-action=>"$scripturl") .
               hidden(-name=>'action',
                      -default=>'displayheaders',
                      -override=>'1') .
               hidden(-name=>'sessionid',
                      -default=>$thissession,
                      -override=>'1') .
               hidden(-name=>'sort',
                      -default=>$sort,
                      -override=>'1') .
               hidden(-name=>'firstmessage',
                      -default=>$firstmessage,
                      -override=>'1') .
               hidden(-name=>'folder',
                      -default=>$folder,
                      -override=>'1') .
               submit("$lang_text{'continue'}") .
               end_form();
   $html =~ s/\@\@\@CONTINUEBUTTON\@\@\@/$temphtml/;
   print $html;

   printfooter();
}
##################### END SAVEPREFS ######################

#################### ADDRESSBOOK #######################
sub addressbook {
   verifysession();
   print header(-pragma=>'no-cache'),
         start_html(-"title"=>"$lang_text{'abooktitle'}",
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
   '<font color=',$style{"titlebar_text"},' face=',$style{"fontface"},' size="3"><b>',uc($lang_text{$field}),": $lang_text{'abook'}</b></font>",
   '</td></tr>';

   if ( -f "$userprefsdir$user/addressbook" ) {
      open (ABOOK,"$userprefsdir$user/addressbook") or
         neomailerror("$lang_err{'couldnt_open'} addressbook!");
      while (<ABOOK>) {
         ($name, $email) = split(/:/, $_);
         chomp($email);
         $addresses{"$name"} = $email;
      }
      close (ABOOK) or neomailerror("$lang_err{'couldnt_close'} addressbook!");

      my $bgcolor = $style{"tablerow_dark"};
      foreach my $key (sort(keys %addresses)) {
         print "<tr><td bgcolor=$bgcolor width=\"20\"><input type=\"checkbox\" name=\"to\" value=\"",
         $addresses{"$key"}, '"';
         if ($preexisting =~ s/\Q$addresses{"$key"}\E,?//g) {
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
   unless ($headerprinted) {
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
      print header(-pragma=>'no-cache');
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
