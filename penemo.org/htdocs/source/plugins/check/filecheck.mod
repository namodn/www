#!/usr/bin/perl -w
#
#  pugins/check/filecheck.mod 
#  Copyright (C) 2000 Nick Jennings
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA
#
#  This program is developed and maintained by Nick Jennings.
# Contact Information:
#
#    Nick Jennings                 nick@namodn.com
#    PMB 377                       http://nick.namodn.com
#    4096 Piedmont Ave.
#    Oakland, CA 94611
#
#  penemo homepage : http://www.communityprojects.org/apps/penemo/
#
#


use lib '/usr/local/share/penemo/modules/';
use penemo;
use strict;

unless (@ARGV) {
	print "params: \n";
	print "		check = returns a 0, for use internally.\n";
	print "		exec (runs check)\n"; 
	exit;
}

if (($ARGV[0] eq 'check') && (! $ARGV[1])) { exit 1; }
unless ($ARGV[0] eq 'exec') { penemo::core->notify_die("bad parameters.\n"); }

chomp @ARGV;


my $ok_light = penemo::core->html_image('agent', 'ok');
my $bad_light = penemo::core->html_image('agent', 'bad');

if (-f "/tmp/penemo.test") {
	print "1\n";
	print "--htmldump\n";
	print "$ok_light <FONT COLOR=\"#11AA11\">the file: /tmp/penemo.test exists.</FONT><BR>\n";
}
else {
	print "0\n";
	print "filecheck: the file /tmp/penemo.test does not exists.\n";
	print "--htmldump\n";
	print "$bad_light <FONT COLOR=\"#AAAAAA\">filecheck: the file: /tmp/penemo.test does not exists.</FONT><BR>\n";
}





