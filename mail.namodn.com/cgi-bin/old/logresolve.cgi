#!/usr/bin/perl -w

use strict;
use Net::DNS;
use IO::Select;
use Getopt::Std;
use POSIX qw(strftime);

my %opts;
my $usage =<<"-x-";
Usage: $0 [-hvnr] [-d <level>] [-m <mask>] [-l <line cache>] [-t <timeout>] [-s <number of sockets>] <LOG FILE>
-x-
my $version =<<"-x-";
Logresolve.pl v0.3 - Author: John Douglas Rowell (me\@jdrowell.com)
Homepage: http://www.jdrowell.com/Linux/Projects/Logresolve
-x-
getopt("dmlts", \%opts);

if (exists $opts{h}) {
	print <<"-x-"; exit;
$version
$usage

Resolves ip numbers to host names for Apache "combined" style log files.

   -h            help (this text).
   -v            display version information.
   -n            don't display stats after processing
   -r            recurse into C, B and A classes when there is no PTR.
                 default is no recursion 
   -d <level>    debug mode (no file output, just statistics during run).
                 verbosity level range: 1-2
   -t <timeout>  timeout in seconds (for each host resolution).
                 default is 30 seconds
   -s <sockets>  maximum number of concurrent sockets to use.
                 default is 32
                 (use ulimit -a to check the max allowed for your 
                 operating system)
   -m <mask>     <mask> accepts %i for IP and %c for class owner.
                 ex: "somewhere.in.%c" or "%i.in.%c"
                 default if "%i.%c"
   -l <lines>    numbers of lines to cache in memory.
                 default is 10000
   <LOG FILE>    the log filename or '-' for STDIN

-x-
}

if (exists $opts{v}) {
	print <<"-x-"; exit;
$version
try $0 -h for help
-x-
}

if (!defined $ARGV[0]) {
	print <<"-x-"; exit;
$usage
-x-
}

my $filename = $ARGV[0];

!exists $opts{d} and $opts{d} = 0;

my $timeout = exists $opts{t} ? $opts{t} : 30;
my $blocksize = exists $opts{"s"} ? $opts{"s"} : 32;
my $maxlines = exists $opts{l} ? $opts{l} : 10000;
my $ipmask = '^(\d+)\.(\d+)\.(\d+)\.(\d+)';
!exists $opts{"m"} and $opts{"m"} = '%i.%c';

my $res = new Net::DNS::Resolver;
my $sel = new IO::Select;
my %hosts;
my %class;
my %q;
my %socks;
my @lines;
my %stats = ( SENT => 0, RECEIVED => 0, BOGUS => 0, RESOLVED => 0, HRESOLVED => 0, TIMEOUT => 0, STARTTIME => time(), MAXTIME => 0, TOTTIME => 0, TOTLINES => 0, TOTHOSTS => 0);

$filename ne '-' and !-f $filename and print("can't find log file '$filename'\n"), exit;
open FILE, $filename or die "error trying to open log file '$filename'";

while (1) {
	getlines();
	$#lines == -1 and last;
	makequeries();
	checkresponse();
	checktimeouts();
	printresults();
}

printstats();


sub addhost {
	my $ip = shift;

	if (exists $hosts{$ip}) { $hosts{$ip}{COUNT}++ } 
	else { $hosts{$ip}{NAME} = '-1'; $hosts{$ip}{COUNT} = 1; $q{$ip} = 0; $stats{TOTHOSTS}++ }

	!$opts{r} and return;

	$ip =~ /$ipmask/;

	for ("$3.$2.$1", "$2.$1", "$1") {
		if (exists $class{$_}) { $class{$_}{COUNT}++ }
		else { $class{$_}{NAME} = '-1', $class{$_}{COUNT} = 1, $q{$_} = 0 }
	}
}

sub removehost {
	my $ip = shift;

	if (--$hosts{$ip}{COUNT} < 1) {
		my $resolved = getresolved($ip);
		$resolved ne '-1' and $resolved ne '-2' and $stats{HRESOLVED}++;
		delete $hosts{$ip};
	}

	$ip =~ /$ipmask/;

	for ("$3.$2.$1", "$2.$1", "$1") {
		--$class{$_}{COUNT} < 1 and delete $class{$_};
	}
}

sub getresolved {
	my $ip = shift;

	$hosts{$ip}{NAME} eq '-1' and return -1;
	$hosts{$ip}{NAME} ne '-2' and return $hosts{$ip}{NAME};
	!defined $opts{r} and return '-2';
	
	$ip =~ /$ipmask/;

	for ("$3.$2.$1", "$2.$1", "$1") {
		$class{$_}{NAME} eq '-1' and return '-1';
	}

	for ("$3.$2.$1", "$2.$1", "$1") {	
		$class{$_}{NAME} ne '-2' and return maskthis($ip, $class{$_}{NAME});
	}

	return '-2'; # totally unresolved
}

sub maskthis {
	my ($ip, $domain) = @_;
	my $masked = $opts{"m"};

	$masked =~ s/%i/$ip/;
	$masked =~ s/%c/$domain/;
	
	return $masked;
}

sub getlines {
	my $line;
	while ($#lines < $maxlines - 1 and $line = <FILE>) {
		$stats{TOTLINES}++; 
		push @lines, $line;
		!($line =~ /^$ipmask\s/) and next;
		addhost(($line =~ /^(\S+)/));
	}
}

sub makequeries {
	my @keys = keys %q;

	for (1..($blocksize - $sel->count)) {
		my $query = shift @keys;
		!$query and last;
		($query =~ /$ipmask/) ? query($query, 'H') : query($query, 'C');
		delete $q{$query};
	}
}

sub checkresponse {
	for ($sel->can_read(5)) {
		my $resolved = 0;
		my $fileno = fileno($_);
		my $query = $socks{$fileno}{QUERY};
		my $type = $socks{$fileno}{TYPE};
		my $dnstype = ($type eq 'H') ? 'PTR' : 'SOA';
		my $timespan = time() - $socks{$fileno}{TIME};
		$stats{TOTTIME} += $timespan;

		my $packet = $res->bgread($_);
		$stats{RECEIVED}++;
		$sel->remove($_);
		delete $socks{$fileno};

		if ($packet) {
			for ($packet->answer) {
				$_->type ne $dnstype and next;
				$timespan > $stats{MAXTIME} and $stats{MAXTIME} = $timespan;

				if ($type eq 'H') {
					$resolved = 1;
					$hosts{$query}{NAME} = $_->{ptrdname};
				} else {
					my ($ns, $domain) = $_->{mname} =~ /([^\.]+)\.(.*)/;
					if (defined $domain) {
						defined $class{$query} and $class{$query}{NAME} = $domain;
						$resolved = 1;
					}
				}
			}
		}
		
		if ($resolved) {
			$stats{RESOLVED}++;
		} else {
			$stats{BOGUS}++;
			if ($type eq 'H') { $hosts{$query}{NAME} = '-2' }
			else { defined $class{$query} and $class{$query}{NAME} = '-2' } 
		}
	}
}

sub checktimeouts {
	my $now = time();

	for ($sel->handles) {
		my $fileno = fileno($_);
		my $query = $socks{$fileno}{QUERY};

		my $timespan = $now - $socks{$fileno}{TIME};
		if ($timespan > $timeout) {
			$stats{TIMEOUT}++;
			$stats{TOTTIME} += $timespan;

			if ($socks{$fileno}{TYPE} eq 'H') { $hosts{$query}{NAME} = '-2' } 
			else { defined $class{$query} and $class{$query}{NAME} = '-2' }

			$sel->remove($_);
			delete $socks{$fileno};
		}
	}
}

sub printresults {
	$opts{d} >= 1 and print STDERR "Sent: $stats{SENT}, Received: $stats{RECEIVED}, Resolved: $stats{RESOLVED}, Bogus: $stats{BOGUS}, Timeout: $stats{TIMEOUT}\n";

	while ($#lines != -1) {
		my $line = $lines[0];
		!($line =~ /^$ipmask\s/) and print($line), shift @lines, next;

		my ($ip) = $line =~ /^(\S+)/;
		my $resolved = getresolved($ip);
		$resolved eq '-1' and last;
		$resolved ne '-2' and $line =~ s/^(\S+)/$resolved/;

		print $line;
		shift @lines;
		removehost($ip);
	}
}

sub printstats {
	exists $opts{n} and return;

	$stats{SENT} == 0 and $stats{SENT} = 1;
	my $timespan = time() - $stats{STARTTIME};

	print STDERR 
		"     Total Lines: $stats{TOTLINES}\n",
		"     Total Time : ", strftime("%H:%M:%S", gmtime($timespan)), " (", sprintf("%.2f", $stats{TOTLINES} / $timespan), " lines/s)\n",
		"     Total Hosts: $stats{TOTHOSTS}\n",
		"  Resolved Hosts: $stats{HRESOLVED} (", sprintf("%.2f", $stats{HRESOLVED} / $stats{TOTHOSTS} * 100), "%)\n",
		"Unresolved Hosts: ", $stats{TOTHOSTS} - $stats{HRESOLVED}, " (", sprintf("%.2f", ($stats{TOTHOSTS} - $stats{HRESOLVED}) / $stats{TOTHOSTS} * 100), "%)\n",
		"Average DNS time: ", sprintf("%.4f", $stats{TOTTIME} / $stats{SENT}), "s per request\n",
		"    Max DNS time: ", $stats{MAXTIME}, "s (consider this value for your timeout)\n";
}

sub query {
	my ($find, $type) = @_;
	my $send = ($type eq 'H') ? $find : ("$find.in-addr.arpa");

	my $sock = $res->bgsend($send, ($type eq 'H') ? 'PTR' : 'SOA');
	!$sock and die "Error opening socket for bgsend. Are we out of sockets?";
	$stats{SENT}++;
	$sel->add($sock);
	my $fileno = fileno($sock);
	$socks{$fileno}{TIME} = time();
	$socks{$fileno}{QUERY} = $find;
	$socks{$fileno}{TYPE} = $type;

	return $fileno;
}

