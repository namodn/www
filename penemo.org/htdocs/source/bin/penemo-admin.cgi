#!/usr/bin/perl -w

use strict;
use CGI qw(:standard);
use CGI::Carp;


use lib '/usr/local/share/penemo/modules/';

use penemo;

my $penemo_conf_file = '/usr/local/etc/penemo/penemo.conf';

my $agent_conf_file = '/usr/local/etc/penemo/agent.conf';

my $conf = penemo::config->load_config($penemo_conf_file, $agent_conf_file);

unless (param('agent')) {
	die "no agent specified\n";
}

my $date = `date`;
chomp $date;
$date =~ s/\s+/ /g;   # takeout any double spaces
my ($date_string, $date_delimited) = &convert_date_to_string();
my $agent = param('agent');

if (param('pause')) {
	&pause();
}
elsif (param('unpause')) {
	&unpause();
}
else {
	die "nothing to do\n";
}



# sub for pausing agents.
sub pause {
	# load agents data file into array
	my @data = &load_data();  # load agent data into array

	if ($data[7] != '000000000000') {
		my $paused = convert_to_fulltime();
		# agent already paused
		print header;
		print "<HEAD><TITLE>$agent paused</TITLE></HEAD>\n";
		print '<BODY BGCOLOR="#000000" TEXT="#AAAADD">', "\n";
		print '<CENTER>';
		print "&nbsp;<BR>\n";
		print "<FONT SIZE=2>";
		print "$agent is already paused untill: $paused <BR>\n";
		print "&nbsp;<BR>\n";
		print "If this is not showing in the agent list, it will be<BR>\n";
		print "updated the next time penemo is run.<BR>\n";
		print "</FONT>\n";
		print '</CENTER>';
		print "</BODY>\n";
		print end_html;
		exit;
	}
	
	# print html form to get time to pause agent for
	unless (param('time')) { &get_time($agent); }
	else {
		my $paused = convert_to_fulltime();
		# time set, pause agent
		$data[6] = '1';
		$data[7] = $paused;
	
		&set_data(@data);  # write agent data with paused info

		print header;
		print "<HEAD><TITLE>$agent paused</TITLE></HEAD>\n";
		print '<BODY BGCOLOR="#000000" TEXT="#AAAADD">', "\n";
		print '<CENTER>';
		print "<FONT SIZE=2>";
		print "&nbsp;<BR>\n";
		print "$agent paused untill: $paused <BR>\n";
		print "&nbsp;<BR>\n";
		print "the html will be updated the next time penemo is run.<BR>\n";
		print "</FONT>\n";
		print '</CENTER>';
		print "</BODY>\n";
		print end_html;
		exit;
	}
}

# sub to unpause agent
sub unpause {
	# load agents data into array
	my @data = &load_data();

	# this unpauses agent
	$data[6] = '0';
	$data[7] = '000000000000';

	# write data back to file
	&set_data(@data);

	# update index.html to show agent unpaused.
	#&update_html_unpause();

	print header;
	print "<HEAD><TITLE>unpaused $agent</TITLE></HEAD>\n";
	print '<BODY BGCOLOR="#000000" TEXT="#AAAADD">', "\n";
	print '<CENTER>';
	print "<FONT SIZE=2>";
	print "&nbsp;<BR>\n";
	print "$agent has been unpaused<BR>\n";
	print "&nbsp;<BR>\n";
	print "the html will be updated the next time penemo is run.<BR>\n";
	print "</FONT>\n";
	print '</CENTER>';
	print "</BODY>\n";
	print end_html;
	exit;
}




#
# FUNCTIONS
#

# prints html for to get time to pause agent for.
sub get_time {
	print header;
	print "<HEAD><TITLE>pause $agent</TITLE></HEAD>\n";
	print '<BODY BGCOLOR="#000000" TEXT="#AAAADD">', "\n";
	print '<CENTER>';
	print '&nbsp;<BR>', "\n";
	print "<FONT SIZE=3><B>pausing agent: $agent</B></FONT><BR>\n";
	print "<FONT SIZE=2>\n";
	print '&nbsp;<BR>', "\n";
	print 'current server time: ', "$date<BR>\n";
	print "<FORM METHOD=\"Post\" action=\"/cgi-bin/penemo-admin.cgi\">\n";
	print "<INPUT type=text name=\"agent\" value=\"$agent\" size=16><BR>\n";
	print 'enter the number minutes you wish to pause this agent? (max: 60): <INPUT type=text name="time" size=2 maxlength=2><BR>', "\n";
	print "</FONT><FONT SIZE=2 COLOR=#000000>\n";
	print '<INPUT TYPE=SUBMIT NAME=pause VALUE=pause><BR>', "\n";
	print '</FORM><BR>', "\n";
	print "</FONT>\n";
	print '</CENTER>';
	print '</BODY>', "\n";
	print end_html;
}

# converts unix time to YYYYMoMoDDHHMiMi
sub convert_to_fulltime {
	my $time = param('time');
	if ($time > '60') { $time = '60'; }
	my ($year, $month, $day, $hour, $minutes) = split(/-/, $date_delimited);
	print "$date_delimited, year: $year month: $month day: $day hour: $hour min: $minutes\n";
	my $calc = $minutes + $time;
	if ($calc >= '60') {
		$hour++;
		if ($hour >= '24') {
			$hour = $hour - 24;	
			$day++;
		}
		$minutes = $calc - 60;
	}	
	else {
		$minutes = $calc;
	}

	# if any are single digits add a before it
	if ($minutes =~ /^\d{1}$/) {
		$minutes = "0$minutes";
	}
	if ($hour =~ /^\d{1}$/) {
		$hour = "0$hour";
	}
	if ($day =~ /^\d{1}$/) {
		$day = "0$day";
	}
	if ($month =~ /^\d{1}$/) {
		$month = "0$month";
	}

	return ("$year$month$day$hour$minutes");
}

sub convert_date_to_string {
        my @date = split (/\s/, $date); # Split on whitespace
	print "", join(' ', @date), "\n";
        my ($month, $day, $time, $year) = ($date[1], $date[2], $date[3], $date[5]);
        $month = convert_month($month);
        my ($hour, $minutes, $seconds) = split(/:/, $time);
        return ("$year$month$day$hour$minutes", "$year-$month-$day-$hour-$minutes");
}

sub convert_month {
        my $month = shift;
        if      ($month =~ /^Jan$/)     { $month = '01'; }      
        elsif   ($month =~ /^Feb$/)     { $month = '02'; }      
        elsif   ($month =~ /^Mar$/)     { $month = '03'; }      
        elsif   ($month =~ /^Apr$/)     { $month = '04'; }      
        elsif   ($month =~ /^May$/)     { $month = '05'; }      
        elsif   ($month =~ /^Jun$/)     { $month = '06'; }      
        elsif   ($month =~ /^Jul$/)     { $month = '07'; }      
        elsif   ($month =~ /^Aug$/)     { $month = '08'; }      
        elsif   ($month =~ /^Sep$/)     { $month = '09'; }      
        elsif   ($month =~ /^Oct$/)     { $month = '10'; }      
        elsif   ($month =~ /^Nov$/)     { $month = '11'; }      
        elsif   ($month =~ /^Dec$/)     { $month = '12'; }      
        return ($month);
}


# load agents data 
sub load_data {
	my $dir_data = $conf->get_dir_data();
	open (DATA, "$dir_data/$agent") or die "Cant open $dir_data/$agent : $!\n";
		my @data = <DATA>;
	close DATA;

	@data = split(/\s+/, $data[0]);
	return (@data);
}

sub set_data {
	my (@data) = @_;
	my $dir_data = $conf->get_dir_data();
	open (DATA, ">$dir_data/$agent") or die "Cant open $dir_data/$agent : $!\n";
		foreach my $delm (@data) {
			print DATA "$delm\t";
		}
		print DATA "\n";
	close DATA;
}


#sub update_html_pause {
#	my $time = shift;
#	my $dir_html = $conf->get_dir_html();
#	my @html = ();
#
#	open (HTML, "$dir_html/index.html") or die "Cant open $dir_html/index.html : $!\n";
#		@html = <HTML>;
#	close HTML;
#
#	open (HTML, ">$dir_html/index.html") or die "Cant open $dir_html/index.html : $!\n";
#	foreach my $line (@html) {
#		if ($line =~ /\<A HREF=\"agents\/$agent\/index.html\"\>/) {
#			$line =~ s/green/blue/;	
#			$line =~ s/red/blue/;	
#		}	
#		if ($line =~ /agent=\$agent&pause=1/) {
#			$line =~ s/pause/unpause/;
#			$line = "untill: $time<BR>" . $line;	
#		}
#		print HTML $line;
#	}
#	close HTML;
#	
#}
#sub update_html_unpause {
#}
