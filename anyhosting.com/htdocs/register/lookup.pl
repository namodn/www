#!/usr/bin/perl

use Net::DNS;
$argument = shift;
$res = new Net::DNS::Resolver;
$query = $res->query("$argument", "NS");
if ($query) 
{
   foreach $rr ($query->answer) 
   {
      next unless $rr->type eq "NS";
      print $rr->nsdname, "\n";
   }
}
else 
{
   print "query failed: ", $res->errorstring, "\n";
}
