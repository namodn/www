#!/usr/bin/perl -w

use strict;
use CGI qw(:standard);
use CGI::Carp;

print header;
print "<HEAD><TITLE>pause</TITLE></HEAD>\n";
print '<BODY BGCOLOR="#000000" TEXT="#AAAADD">', "\n";
print '<CENTER>';
print '&nbsp;<BR>', "\n";
print "<FONT SIZE=3><B>pausing with the web interface has been disabled on this example instance of penemo</B></FONT><BR>\n";
print '</CENTER>';
print '</BODY>', "\n";
print end_html;
