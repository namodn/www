#!/usr/bin/perl
# 3/15/99 Terry Ewing
# CGI to search for a domain in the InterNIC
# whois database.  Uses html tmplates for 
# ease of upgrade 

use CGI;
use Whois;
$q = new CGI;

# defines - these can be changed
$introform = "/html/register/index.html";
$takenform = "/html/register/taken.html";
$availableform = "/html/register/available.html";
$thankyouform = "/html/register/thankyou.html";
$internicform = "/html/register/internic.html";
$mailer = '/usr/sbin/sendmail -t robert@namodn.com < /tmp/test.db';

# end of defines


$domain = $q->param('domain');
$formfilled = $q->param('formfilled');

print "Content-type: text/html\n\n";

if ($domain eq "") 
{
	&printintroform()
}
else 
{
	if ($formfilled eq 'Y') 
		{
		&printthankyou();
   		} 
	else 
	{
	&printwhois();
	}
}


sub printintroform 
{
   print &readtemplate($introform);
   die;
}

sub printwhois 
{
   my $w = new Net::Whois::Domain $domain 
      or &domainavailable($domain);
   my $domain = $w->domain;
   my $domname = $w->name;
   #my $domaddress =  map { "    $_\n" } $w->address;
   my $domaddress =  $w->address;
   &domaintaken($domain, $domname, $domaddress);
}

sub domainavailable 
{
   my $domain = shift;

   my $template = &readtemplate($availableform);
   $template =~ s/\<!--domain--\>/$domain/g;

   print $template;
}

sub domaintaken 
{
   my $domain = shift;
   my $domname = shift;
   my $domaddress = shift;

   my $template = &readtemplate($takenform);
   $template =~ s/\<!--domain--\>/$domain/g;
   $template =~ s/\<!--domname--\>/$domname/g;
   $template =~ s/\<!--domaddress--\>/$domaddress/g;

   print $template;
}

sub printthankyou 
{
   my $CompanyName = $q->param('CompanyName');                        
   my $StreetAddress = $q->param('StreetAddress');
   my $City = $q->param('City');
   my $State = $q->param('State');  
   my $Zip = $q->param('Zip');
   my $BizPhone = $q->param('BizPhone');
   my $Email = $q->param('Email');
   my $LastName = $q->param('LastName');
   my $FirstName = $q->param('FirstName');
   my $BizType = $q->param('TypeofBiz');
   my $Comments = $q->param('Comments');



#   my $mailtemplate = &readtemplate($internicform);
    my $mailtemplate = $q->param('CompanyName');

#   $mailtemplate =  s/\<! <!--domain--\>/$domain/g;
 #  $mailtemplate =~ s/\<!--companyname--\>/$CompanyName/g;
 #  $mailtemplate =~ s/\<!--streetaddress--\>/$StreetAddress/g;
 #  $mailtemplate =~ s/\<!--city--\>/$City/g;
 #  $mailtemplate =~ s/\<!--state--\>/$State/g;
 #  $mailtemplate =~ s/\<!--zip--\>/$Zip/g;
 #  $mailtemplate =~ s/\<!--businessphone--\>/$BizPhone/g;
 #  $mailtemplate =~ s/\<!--emailaddress--\>/$Email/g;
 #  $mailtemplate =~ s/\<!--lastname--\>/$LastName/g;
 #  $mailtemplate =~ s/\<!--firstname--\>/$FirstName/g;
 #  $mailtemplate =~ s/\<!--typeofbiz--\>/$BizType/g;
 #  $mailtemplate =~ s/\<!--comments--\>/$Comments/g;

   open (OUTPUT, ">/tmp/test");
   print OUTPUT $mailtemplate;
   close (OUTPUT);
   
   #append data to /home/robert/quick.cust.db in comma delimited format
   open (LOGFILE, ">//tmp/test.db");
   print LOGFILE $CompanyName . "," . 
 $BizType . "," . 	
 $FirstName . " " . $LastName . "," .
 $Email . "," .
 $StreetAddress . "," .
 $City . "," .
 $State . "," .
 $Zip . "," .
 $BizPhone . "," .
 $domain . "," .
 $Comments . "\n";
   close(LOGFILE);

 
   system("$mailer");

   my $thanktemplate = &readtemplate($thankyouform);
	
   $thanktemplate =~ s/\<!--firstname--\>/$FirstName/g;
   $thanktemplate =~ s/\<!--lastname--\>/$LastName/g;
   $thanktemplate =~ s/\<!--domain--\>/$domain/g;

   print $thanktemplate;     

}   

sub readtemplate {
 
   my $templatename = shift;
   my $TBuf = "";

   open(FILE, "<$templatename");
   read(FILE, $TBuf, -s(FILE));
   close(FILE);

   return $TBuf;
}
