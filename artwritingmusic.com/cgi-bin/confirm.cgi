#!/usr/bin/perl -w

use strict;
# standard modules
use CGI::Carp;
use CGI qw(:standard);

# HTML template module
use HTML::Template;
my $template_dir = "templates/";
my $MUA = "/usr/lib/sendmail";
my $admin_email = 'robert@namodn.com';
my $question = '';
my $frontpage = HTML::Template->new(filename => "$template_dir/index_template.html");
my $email = HTML::Template->new(filename => "$template_dir/namodn_email.template");

$frontpage ->param(
    TITLE => 'QuestionArt Admin Center'
);

$email ->param(
    USER => 'robert',
    EMAIL => 'robert@namodn.com',
    PASSWORD => 'test',
    FULLNAME => 'Rob Helmer'
);

print header;
print $frontpage->output;

print $email->output;

if ( $question eq "Deny" ) {
    system("$MUA $admin_email < /tmp/email.txt");
}

exit 1
