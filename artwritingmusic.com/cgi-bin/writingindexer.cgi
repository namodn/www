#!/usr/bin/perl -w

use strict;

use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser);

my @errors = ();

unless ( param() )	{ exit; }

my $from_url = referer();
my $user = _get_username();

my ($title_align, $title, $body_align, $body) = _param_check();

my $text_color = _color_convert('text_color');
my $background_color = _color_convert('background_color');

print header;
print start_html;
print "User: $user<BR>\n";
print "Background color: $background_color<BR>\n";
print "Foreground color: $text_color<BR>\n";
print "Title: $title<BR>\n";
print "Title Align: $title_align<BR>\n";
print "Body Align: $body_align<BR>\n";
print "Body:<BR>\n";
print "$body<BR>\n";
print end_html;

############################### Subroutines ######################################

sub _color_convert($)
{
	my $color = param("$_[0]");
	if ($color eq 'Blue')		{ return '0E9CCF'; }
	elsif ($color eq 'Green')	{ return '0AA000'; }
	elsif ($color eq 'Purple')	{ return 'DF43DA'; }
	elsif ($color eq 'Red')		{ return 'AABBAA'; }
	elsif ($color eq 'Pink')	{ return 'DDAAAA'; }
	elsif ($color eq 'Orange')	{ return 'FAB133'; }
	elsif ($color eq 'Yellow')	{ return 'FFCC00'; }
	elsif ($color eq 'Brown')	{ return 'AA6611'; }
	elsif ($color eq 'Black')	{ return '000000'; }
}

sub _get_username
{
	my @tmp = split('/', $from_url);
	my $user = $tmp[3];
	chomp $user;

	open(FILE, "/home/staff/data/awm/accounts.dat") or die("Cant open account data : $!\n");
	while (<FILE>)
	{
		chomp $_;
		if ($_ eq $user)
		{
			return $user;
		}
	}
	close FILE;
	
	_return_error("Invalid User! : $user");
	_return_error('return');
}

sub _param_check
{
	unless ( param('title_align') )	
	{ 
		_return_error('the text alignment field is undefined');
	}
	unless ( param('title') )
	{ 
		_return_error('the title field is empty'); 
	}
	unless ( param('body_align') )
	{ 
		_return_error('the body alignment field is undefined'); 
	}
	unless ( param('body') )
	{
		_return_error('the body field is empty'); 
	}

	if (@errors)
	{ 
		_return_error('return'); 
	}
	return ( param('title_align'), param('title'), param('body_align'), param('body') );
}

sub _return_error
{
        if ($_[0] eq 'return')
        {
                my $field = $_[1];
                print header;
                print start_html('Errors Detected');
	        print "<FONT SIZE=5><B>Errors detected in Form</B></FONT></BR>\n";
                print "please go back and correct the following list of errors.<BR>\n";
                print "<HR>\n";
                while (@errors)
                {
                        my $error = shift @errors;
                        print "<li>$error</li>\n";
                }
                print end_html;
                exit;
        }
        else
        { 
                push @errors, $_[0];
        }
}
