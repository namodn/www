#  modules/penemo/snmp.pm 
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

#########################
#########################
#########################
## snmp class
##
####
####
####

package penemo::snmp;

use lib '/usr/local/share/penemo/modules/';

use strict;

sub new {
	my ($class, %args) = @_;
	
	my $ref = {
		ip	    => $args{ip},
		mib	    => $args{mib},
		community   => $args{community},
		message	    => '',
		status	    => '',
		html	    => '',
		dir_plugin  => $args{dir_plugin},
		dir_ucd_bin => $args{dir_ucd_bin},
	};

	bless $ref, $class;
}


# functions to retrieve values for internal methods.
#
sub _get_dir_plugin { $_[0]->{dir_plugin} }
sub _get_mib { $_[0]->{mib} }
sub _get_dir_ucd_bin { $_[0]->{dir_ucd_bin} }
sub _get_community { $_[0]->{community} }
sub _get_ip { $_[0]->{ip} }


sub poll {
	my $self = shift;
	my $dir_plugin = $self->_get_dir_plugin() . "/snmp";
	my $mib = $self->_get_mib();
	my $ip = $self->_get_ip();
	my $community = $self->_get_community();
	my $dir_ucd_bin = $self->_get_dir_ucd_bin();
	my $snmpwalk = "$dir_ucd_bin/snmpwalk";
	my @output = ();
	

	unless (-f "$dir_plugin/$mib" . '.mib') {
		$self->{status} = 0;
		$self->{message} = "plugin: $dir_plugin/$mib.mib does not exist.\n";
		return;
	}

	if (`$dir_plugin/$mib.mib check`) {
		$self->{status} = 0;
		$self->{message} = "$dir_plugin/$mib.mib is not a valid penemo mib plugin. (failed check)\n";
		return;
	}

	@output = `$dir_plugin/$mib.mib $ip $community $snmpwalk`;

	unless (@output) {
		$self->{status} = 0;
		$self->{message} = "execution of $dir_plugin/$mib.mib failed (nothing returned).\n";
		return;
 	}

	unless ($output[0] =~ '--agentdump') {
		$self->{status} = 0;
		$self->{message} = "@output";
		return;
	}
	
	my $test = '';
	my @agentdump = ();
	my @htmldump = ();
	my @miberrors = ();
	foreach my $line (@output) {
		if ($line =~ '--agentdump') {
			$test = '1';
			next;
		}
		elsif ($line =~ '--htmldump') {
			$test = '2';
			next;
		}
		elsif ($line =~ '--miberrors') {
			$test = '3';
			next;
		}

		if ($test == '1') {
			push @agentdump, $line; 	
		}
		elsif ($test == '2') {
			push @htmldump, $line;
		}
		elsif ($test == '3') {
			push @miberrors, $line;
		}
	}

	unless ((@agentdump) && (@htmldump)) {
		$self->{status} = 0;
		$self->{message} = "internal error in snmp.pm (no information returned)\n";
	}
	elsif (@miberrors) {
		$self->{status} = 0;
		$self->{message} = "@miberrors";
		$self->{walk} = "@agentdump";
		$self->{html} = "@htmldump";
	}
	else {
		$self->{status} = 1;
		$self->{html} = "@htmldump";
		$self->{walk} = "@agentdump";
	}
	return;
}

sub status {
	$_[0]->{status};
}

sub message {
	$_[0]->{message};
}

sub html {
	$_[0]->{html};
}

sub walk {
	$_[0]->{walk};
}

1;
