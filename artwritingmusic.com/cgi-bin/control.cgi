#!/usr/bin/perl -w

use CGI qw(:standard);
use CGI::Carp;

if (param('call'))	{ &call(param('call')); }
else			{ &invalid(); }

sub call
{

# Detect if awm-control is already used.

my $call_file = $_[0];

print header;
print '<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">', "\n";
print '<HTML>', "\n";
print ' <HEAD>', "\n";
print '  <FRAMESET ROWS=100%,28 FRAMEBORDER="no" BORDER="1">', "\n";
print '   <FRAME NORESIZE MARGINHEIGHT="0" MARGINWIDTH="0" NAME="content" 
		SRC="', "/$call_file", '">', "\n";
print '   <FRAME NORESIZE MARGINHEIGHT="0" MARGINWIDTH="0" NAME="top"
		SRC=/awm-control.html>', "\n";
print '   <NOFRAMES>', "\n";
print '    Your browser doesn\'t support frames', "\n";
print '   </NOFRAMES>', "\n";
print '  </FRAMESET>', "\n";
print ' <HEAD>', "\n";
print '</HTML>', "\n";

}

sub invalid
{
	print header;
	print start_html;

	print <<EOF;

<FONT SIZE=5>Invalid Parameter, nothing to control!</FONT>

EOF

	print end_html;
}
