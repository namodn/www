#!/usr/bin/perl -w

use strict;
use CGI qw(:standard);
use CGI::Carp;

my $flag = 0;
my $news = '/var/www/artwritingmusic.com/htdocs/news.txt';
my $title = "News & Updates";

print header;
print <<"EOF";
<HTML>
<BODY TEXT="#550044" LINK="##002255" VLINK="#002255" BGCOLOR="#DDDDDD"
 BACKGROUND="/images/glrybg.jpg">
<STYLE>
	<!--
	A:hover{color:#FFDD44;}
#	A:link{text-decoration: none}
#	A:visited{text-decoration:none}
	-->
</STYLE>

<TABLE CELLSPACING=0 BORDER=0 CELLPADDING=4 WIDTH=100%>
	<TR>
		<TD WIDTH=11% ALIGN=LEFT ROWSPAN=2>
		</TD>
	
		<TD WIDTH=89% ALIGN=CENTER>
			<FONT SIZE=4><B>
			$title
			</B></FONT>
			<HR WIDTH=70%>
		</TD>
	</TR>
	<TR>
		<TD WIDTH=89%>
			<FONT SIZE=3>
			<CENTER>
			<!-- BEGIN NEWS -->
EOF

open(NEWS, "$news") or die "No News!! $!\n";
while (<NEWS>)
{
	if ($_)	
	{ 
		if 	( $_ =~ '{HEADER}' )	{ $flag = 1; }
		elsif 	( $_ =~ '{TITLE}' )	{ $flag = 2; }
		else
		{ 
			if ( $flag == '1' )
			{
				print "</CENTER>\n";
				print '<FONT COLOR="#BB0011" SIZE=3>', "\n";
				print "<BR><B>$_";
				print '</B></FONT>', "\n";
				print "<CENTER>\n";
				$flag = 0;
				next;
			}
			if ( $flag == '2' )
			{
				print "</CENTER>\n";
				print '<FONT COLOR="#1111FF" SIZE=3>', "\n";
				print "&nbsp &nbsp &nbsp &nbsp $_";
				print '</FONT>', "\n";
				print "<CENTER>\n";
				$flag = 0;
				next;	
			}
			elsif ( $_ eq "\n" )	{ print "&nbsp;<BR>\n"; }
			else  			{ print "$_"; }
		}
	}
	else 	{ print "&nbsp;<BR>\n"; }	
}
close NEWS;

print <<EOF;
			<!-- END NEWS -->
			</FONT></CENTER>
			&nbsp;<BR>
			<HR WIDTH=70%>
		</TD>
	</TR>		
</TABLE>
</BODY>
</HTML>

EOF

system("cp $news $news.bak");
