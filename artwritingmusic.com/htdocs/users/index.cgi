#!/usr/bin/perl -w

use strict;

use CGI qw(:standard);
use CGI::Carp;

#
# Put name of domain (all lowercase, e.g. www.iaminsane.com)
#
my $domain = 'www.artwritingmusic.com';

##################
# Security Check #
##################

my $secure = &referer();
   $secure =~ tr/A-Z/a-z/;

if 	( $secure =~ /^http:\/\/$domain\/users\/$/ ) 
	{ &form_check(); }
elsif	( $secure =~ /^http:\/\/$domain\/users\/index.cgi/ ) 
	{ &form_check(); }
else	{  &index(); exit; }

&form_check();

exit;



sub index
#
#
#
{
	print header;
	print start_html('ArtWritingMusic - User Login');
	&default_html('style');
	&default_html('body');
	&default_html('table');
	print <<EOF;
	<TR>
            	<TD WIDTH="100%" ALIGN=CENTER COLSPAN=2>
			<B>
                	<FONT SIZE=5>ArtWritingMusic - User Login</FONT><BR>
			</B>
		</TD>
	</TR>

	<TR>
      		<TD WIDTH="70%" BGCOLOR="#666666" ROWSPAN=2>
          		<CENTER>
                	<FONT COLOR="#000000">
                	&nbsp;<BR>
                	<FONT COLOR="#660000" SIZE=4><B>
                	        (This site is under heavy development<BR>
				 and is not yet ready for use)
                	</FONT></B>
                	</CENTER>
	
	                <FORM method="Post" action="index.cgi">
	                <FONT COLOR="#000000" SIZE=3><B>
	                  Username: &nbsp
	                          <INPUT type="text" name="username" size=10 maxlength=25>
			&nbsp &nbsp &nbsp
	                  Password: &nbsp
	                          <INPUT type="password" name="password" size=10 maxlength=25>
	                </FONT></B>
	                &nbsp;<BR>&nbsp;<BR>
	                <CENTER>
	                <FONT COLOR="#000000">
	                <INPUT type="SUBMIT" NAME="logon" VALUE="Logon">
	                </FONT>
	                </CENTER>
	                </FORM>
		</TD>
	
		<TD WIDTH="300" ALIGN=CENTER>
        	          &nbsp;<BR>
        	                  <IMG SRC="/icons/awm.jpg" border=0>
        	          &nbsp;<BR>
		</TD>
	</TR>

	<TR>
		<TD WIDTH="300">
EOF

	print <<EOF;

      	        </TD>
        </TR>

        <TR>
                <TD WIDTH="100%" COLSPAN=3 ALIGN=CENTER>
                        <HR WIDTH="50%">
                        <FONT COLOR="#44AA22"><B><I>
                        Web Design by
                        <A HREF="http://nick.namodn.com">Nick Jennings</A>
                        , email:
                        <A HREF=mailto:nick\@namodn.com>nick\@namodn.com</A>
                        <BR>
                        </FONT></B></I>
                        <HR WIDTH="50%">
      	        </TD>
        </TR>
</TABLE>    
	
EOF
	print end_html;

}



sub form_check
#
# This is the initial test to see if the login variables have been filled in.
# If so, it jumps to the &validate subroutine to verify that the $username and
# $password is correct. If not, it jumps to the &incomplete subroutine with the
# name of the field that is empty (i.e. username, or password).
#
{
	if (param('menu'))
	{
		my $menu	= param('menu');
		my $name	= param('name');
	
		&nav_bar("$name", "$menu");
	}
	
	if (param('username'))
	{ 
		if (param('password'))	{ &validate }	
		else			{ &incomplete('password') }
	}
	else 				{ &incomplete('username') }
}



sub validate
#
# This subroutine verifies the username and password. If validation is
# successfull, it jumps to the &login subroutine, passing the $username
# variable. If validation fails, it jumps to the &invalid subroutine.
#
{
	my $username = param('username');
	my $password = param('password');

	open (ACCOUNTS, "/home/system/data/iaminsane/accounts.dat")
		or die "$!\n";

		while (<ACCOUNTS>)
		{
			my @plate = split(' ', $_);
			if ($username =~ /^$plate[0]$/)
			{
				if ($password =~ /^$plate[1]$/)
				{ &logon("$username"); next; }
			}
		}

	close ACCOUNTS;

	&invalid();
}



sub logon
#
# Once validation is successfull, this subroutine is run, it must be passed
# the $username variable. This subroutine loads the users account settings.
#
{
	my $name = $_[0];

	&nav_bar("$name", 'Inbox');	
}



sub nav_bar
#
# This is the subroutine for the navigational bar that appears at the top of
# every menu within a users account. It takes the $name and current $menu as
# parameters and displays the nav bar, highlighting the current menu
# defferently than the others using the &nav_bar_common subroutine to reuse
# common html to simplify changes. Once its displayed the nav bar, it jumps
# to the subroutine for whichever menu its currently supposed to display.
#
{
	my $name = $_[0];
	my $menu = $_[1];

        print header;
        print start_html("$name - $domain - $menu");
	&default_html('style');
	&default_html('body');
	&default_html('table');

	print <<EOF;
	<TR>
		<TD WIDTH="20%" ALIGN=CENTER>
			<IMG SRC="http://$domain/icons/awm.jpg">
		</TD>

		<TD WIDTH="80%" COLSPAN=10 ALIGN=CENTER>
EOF
	print "\t\t</TD>\n";			
	print "\t</TR>\n";


	print "\n\t<TR>\n";
	print "\t\t<TD WIDTH=\"100%\" ALIGN=CENTER COLSPAN=11
		BGCOLOR=\"#000000\">\n";
	print "\t\t\t&nbsp;<BR>\n";
	print "\t\t</TD>\n";
	print "\t</TR>\n";

	print "\n\t<TR>\n";
	print "\n\t\t<TD WIDTH=\"20%\" BGCOLOR=\"#000000\" ALIGN=CENTER>\n";
	print "\t\t\t&nbsp;<BR>\n";
	print "\t\t</TD>\n";


	if ($menu eq 'Inbox')
	{ &nav_bar_common('focus', "Inbox", "$name"); }
	else
	{ &nav_bar_common('option', "Inbox", "$name"); }		

	&nav_bar_common('space');

	if ($menu eq 'Compose')
	{ &nav_bar_common('focus', "Compose", "$name"); }
	else
	{ &nav_bar_common('option', "Compose", "$name"); }		

	&nav_bar_common('space');

	if ($menu eq 'Folders')
	{ &nav_bar_common('focus', "Folders", "$name"); }
	else
	{ &nav_bar_common('option', "Folders", "$name"); }		

	&nav_bar_common('space');

	if ($menu eq 'Settings')
	{ &nav_bar_common('focus', "Settings", "$name"); }
	else
	{ &nav_bar_common('option', "Settings", "$name"); }		

	&nav_bar_common('space');

	if ($menu eq 'Help')
	{ &nav_bar_common('focus', "Help", "$name"); }
	else
	{ &nav_bar_common('option', "Help", "$name"); }		


	print "\n\t\t<TD WIDTH=\"21%\" BGCOLOR=\"#000000\" ALIGN=CENTER>\n";
	print "\t\t\t&nbsp;<BR>\n";
	print "\t\t</TD>\n";
	print "\t</TR>\n";

	print "\n\t<TR>\n";
	print "\t\t<TD WIDTH=\"100%\" ALIGN=CENTER COLSPAN=11
		BGCOLOR=\"#000000\">\n";
	print "\t\t\t&nbsp;<BR>\n";
	print "\t\t</TD>\n";
	print "\t</TR>\n";
	
	print "\t<TR>\n";
	print "\t\t<TD WIDTH=\"100%\" ALIGN=CENTER COLSPAN=11
		BGCOLOR=\"#DDDDDD\">\n";
	print "\t\t\t<FONT COLOR=\"#000000\">\n";

	if 	($menu eq 'Inbox')	{ &inbox("$name"); }
	elsif 	($menu eq 'Compose')	{ &compose("$name"); }
	elsif 	($menu eq 'Folders')	{ &folders("$name"); }
	elsif 	($menu eq 'Settings')	{ &settings("$name"); }
	elsif 	($menu eq 'Help')	{ &help(); }
	else 				{ &inbox('Error'); }

	print <<EOF;
			</FONT>
		</TD>
	</TR>
</TABLE>
EOF
	print end_html;

	exit;
}



sub nav_bar_common
#
#
#
{
	my $type = $_[0];

	if ($type eq 'space')
	{
		print "\t\t<TD WIDTH=\"1%\" BGCOLOR=\"#000000\" 
			ALIGN=CENTER>\n";
		print "\t\t\t&nbsp \n";
		print "\t\t</TD>\n";
		return;
	}

	my $menu	= $_[1];
	my $name	= $_[2];

	if ($type eq 'focus')
	{
		print "\n\t\t<TD WIDTH=\"11%\" BGCOLOR=\"000066\" 
				ALIGN=CENTER>\n";
		print "\t\t\t<B>$menu</B>\n";
	}
	elsif ($type eq 'option')
	{
		print "\n\t\t<TD WIDTH=\"11%\" BGCOLOR=\"666666\" 
				ALIGN=CENTER>\n";
		print "\t\t\t<A HREF=\"index.cgi?menu=$menu&name=$name\">\n";
		print "\t\t\t<FONT COLOR=\"#000000\">\n";
		print "\t\t\t$menu\n";
		print "\t\t\t</FONT>\n";
		print "\t\t\t</A>\n";
	}
	else
	{
		print "\n\t\t<TD WIDTH=\"11%\" BGCOLOR=\"000066\" 
				ALIGN=CENTER>\n";
		print "\t\t\t<B>Error</B>\n";
	}
	print "\t\t</TD>\n";

	return;
}



sub inbox
#
#
#
{
	my $name = $_[0];

	print <<EOF;
			&nbsp;<BR>
EOF
	print "\t\t\t<FONT COLOR=\"#000000\">\n";
	print "\t\t\tThis is the inbox of $name\n";
	print "\t\t\t</FONT>\n";

	print <<EOF;
			&nbsp;<BR>
			&nbsp;<BR>
EOF
	return;
}



sub compose
#
#
#
{
	my $name = $_[0];

	print <<EOF;
			&nbsp;<BR>
EOF
	print "\t\t\t<FONT COLOR=\"#000000\">\n";
	print "\t\t\tThis is the composition menu for $name\n";
	print "\t\t\t</FONT>\n";

	print <<EOF;
			&nbsp;<BR>
			&nbsp;<BR>
EOF
	return;
}



sub folders
#
#
#
{
	my $name = $_[0];

	print <<EOF;
			&nbsp;<BR>
EOF
	print "\t\t\t<FONT COLOR=\"#000000\">\n";
	print "\t\t\tThese are the folders of $name\n";
	print "\t\t\t</FONT>\n";

	print <<EOF;
			&nbsp;<BR>
			&nbsp;<BR>
EOF
	return;
}



sub settings
#
#
#
{
	my $name = $_[0];

	print <<EOF;
			&nbsp;<BR>
EOF
	print "\t\t\t<FONT COLOR=\"#000000\">\n";
	print "\t\t\tThese are the settings of $name\n";
	print "\t\t\t</FONT>\n";

	print <<EOF;
			&nbsp;<BR>
			&nbsp;<BR>
EOF
	return;
}



sub help
#
#
#
{
	print <<EOF;
			&nbsp;<BR>
EOF
	print "\t\t\t<FONT COLOR=\"#000000\">\n";
	print "\t\t\tThis is the help menu\n";
	print "\t\t\t</FONT>\n";

	print <<EOF;
			&nbsp;<BR>
			&nbsp;<BR>
EOF
	return;
}


sub incomplete
#
# This is where the script goes when one or both of the logon fields have
# not been filled out, it simply prints which of the two have not been filled
# out and exits.
#
{
	print header;
	print start_html('Incomplete Logon');
	print '<FONT SIZE=5> ', "Incomplete Logon Fields",
		'<BR></FONT>', "\n";
	print '<HR WIDTH="95%">', "\n";
	print "The $_[0] field is empty, please
		hit your browsers back button and fill in the empty 
		field(s).", '<BR>', "\n";
	print end_html;

	exit;
}



sub invalid
#
# When invalid account information is entered (i.e. both fields have been
# filled out, but are not succesfully validated against any of the accounts),
# This subroutine lets the user know, and exits.
#
{
	print header;
	print start_html('Invalid Logon Attempt');
	print '<FONT SIZE=5> ', "Invalid Logon Attempt",
		'<BR></FONT>', "\n";
	print '<HR WIDTH="95%">', "\n";
	print "You have attempted to logon with an invalid username and/or
		password. Please click on your browsers back button and 
		double check the information you entered.", '<BR>', "\n";
	print end_html;

	exit;
}



sub default_html
#
# This subroutine is sort of an internal module form generating uniform html
# settings. It is called with the name of the type of code it wishes to use
# (i.e. &default_html('body') sets the body of the html code to the default
# colors) so that the "look and feal" is somewhat consistent throughout several
# dynamically generated html pages.
#
{
	if (!$_[0])	{ return; }

	if ($_[0] eq 'style')
	{
		print "\n<STYLE>\n";
		print "\t<!--\n";
		print "\tA:hover{color:#FFDD44;}\n";
		print "\tA:link{text-decoration: none}\n";
		print "\tA:visited{text-decoration:none}\n";
		print "\t-->\n";
		print "</STYLE>\n";
		return;
	}
	if ($_[0] eq 'body')
	{
		print "<BODY BGCOLOR=\"#000000\" TEXT=\"#44AA22\"
			LINK=\"#AAAA00\" VLINK=\"#AAAA00\">\n";
		return;
	}
	if ($_[0] eq 'table')
	{
		print "<TABLE WIDTH=\"100%\" CELLPADDING=4 CELLSPACING=0
			BORDER=0 ALIGN=CENTER>\n";
		return;
	}
}



sub banner_display
#
#
#
{
	my @ad  = ();
	my $num = 0;
	my $url = '';

	opendir(AD, "/html/iaminsane/ads/") or die "$!\n";
		while ( defined( $ad[$num] = readdir(AD) ) )
		{
			if	($ad[$num] eq '.')	{ next; }
			elsif	($ad[$num] eq '..')	{ next; }
			$num++;
		}
	closedir(AD);

	srand;
	$num = rand($#ad);
	
	open (URL, "/html/iaminsane/urls/$ad[$num].url") or die "$!\n";
		while (<URL>)
		{
			$url = $_;
			chomp $url;
		}
	close URL;

	print "\t\t\t<A HREF=\"http://$url\" target=\"new\">\n";
	print "\t\t\t<IMG SRC=\"http://$domain/ads/$ad[$num]\" BORDER=0>\n";
	print "\t\t\t</A>\n";
}
