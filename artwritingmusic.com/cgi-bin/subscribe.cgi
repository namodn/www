#!/usr/bin/perl -w

use strict;

use CGI qw(:standard);
use CGI::Carp;

my $db = "/usr/home/system/database/";
my $check = "";
my $en = 0;

my $svc = param('service');
my @svc = split(' ', $svc);
$svc = $svc[0];


print header;

while ()
{
	if (param('name') eq "")
	{
		$check = "0";
		last;
	}
	elsif (param('email') eq "")
	{
		$check = "0";
		last;
	}
	elsif (param('username') eq "")
	{
		$check = "0";
		last;
	}
	elsif (param('from') eq "")
	{
		$check = "0";
		last;
	}

	else
	{
		$check = "1";
		last;
	}

	if ( $svc eq 'W2' )
	{
		if (param('street') eq "")
		{
			$check = "0";
			last;
		}
		elsif (param('city') eq "")
		{
			$check = "0";
			last;
		}
		elsif (param('state') eq "")
		{
			$check = "0";
			last;
		}
		elsif (param('zip') eq "")
		{
			$check = "0";
			last;
		}
	}		

	last;
}

if ($check == "1")
{
	print start_html('Subscription Request Sent');
	print "<H1>Thank You ", param('name'), "!</H1>\n";
	print "<HR>\n";
	print "Your subscription request has been verified, we will email";
	print " you with details shortly<BR>\n";
	print "<HR>\n";
	print '<A HREF="http://www.ArtWritingMusic.com" target="_top">Back to\n'; 
	print "ArtWritingMusic.com</A><BR>\n";

	open (MAIL, '| /usr/sbin/sendmail -t -oi') or die "Can't open sendmail: $!";
		print MAIL 'To: admin@namodn.com', "\n";
		print MAIL 'From: ', param('email'), "\n";
		print MAIL "Subject: $svc Subscriber!!!\n";
		print MAIL "Subscribtion request for $svc account.\n";
		print MAIL "--------\n";
		print MAIL 'Name: ', param('name'), "\n";
		print MAIL 'Username: ', param('username'), "\n";
		print MAIL 'Art: ', param('AA'), ' - Writing: ', param('AW'), ' - Music: ', param('AM'), "\n";
		print MAIL 'Email: ', param('email'), "\n";
		print MAIL 'Mailing List?: ', param('ML'), "\n";
		if ( $svc eq 'W2' )
		{
			print MAIL 'Street: ', param('street'), "\n";
			print MAIL 'City: ', param('city'), "\n";
			print MAIL 'State: ', param('state'), '  Zip: ', param('zip'), "\n";
		}
		print MAIL "--------\n";
		print MAIL 'Where did you here about us?: ', "\n";
		print MAIL param('from'), "\n";
		print MAIL "--------\n";
		print MAIL 'Comments: ', "\n";
		print MAIL param('comments'), "\n";
	close MAIL;
	
	my $name = param('name');
	my $username = param('username');
	my $AA = param('AA');
	my $AW = param('AW');
	my $AM = param('AM');
	my $email = param('email');
	my $ML = param('ML');
	my $from = param('from');
	my $comments = param('comments');
}
else
{
	print start_html('Incomplete Form');
	print "<H1>Incomplete Form</H1>\n";
	print "<HR>\n";
	print "The form you filled out is incomplete, please go back and\n";
	print " fill out the entire form<BR>\n";
	print "<HR>\n";
}

print end_html;

