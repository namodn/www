#!/usr/bin/perl -w

use strict;
# standard modules
use CGI::Carp;
use CGI qw(:standard);

# HTML template module
use HTML::Template;
use DBI;

# database variable settings
my $driver = 'Pg';
my $data_source = 'dbi:Pg:dbname=www-data';
my $db_user = 'www-data';
my $db_pwd = '';

my $template_dir = "/var/www/artwritingmusic.com/cgi-bin/templates/";
my $admin_email = 'robert@namodn.com';
my $index_template = HTML::Template->new(filename => "$template_dir/index_template.html");
my $email_template = HTML::Template->new(filename => "$template_dir/namodn_email.template");
my $user = 'cell';
my $email = 'Jackson__V99@hotmail.com';
my $password = 'random';
my $fullname = 'Joshua Grooms';

sub main {
    if (! param('action' )) {
        &index();        
    }
    elsif (param('action') eq 'Approve') {
        if (! param("$user")) {
	    &index();
	    print "No users selected.";
	}
    elsif (param("$user") eq 'selected') { 
            &approved();
	    &index();
	    print "$user Approved.";
	}
    }
    elsif (param('action') eq 'Deny') {
        if (! param("$user")) {
	    &index();
	    print "No users selected.";
        }
        else {
	    &index();
	    print "No.";
	}
    }
}

sub index {
    $index_template->param(
        TITLE => 'QuestionArt Admin Center',
        USER => $user,
        FULLNAME => $fullname
    );

    print header;
    print $index_template->output;
}

sub approved {
    $email_template ->param(
        USER => $user,
        EMAIL => $email,
        PASSWORD => $password,
        FULLNAME => $fullname
    );

    open ( MAIL, "| /usr/lib/sendmail -t -oi" ) 
        or die "Unable to send email to $admin_email! : $!\n";
    print MAIL "To: $admin_email\n";
    print MAIL "From: $admin_email\n";
    print MAIL "Subject: Membership submission for $email\n";
    print MAIL "\n";
    print MAIL $email_template->output;
    close MAIL;
}

&main();

exit 0;
