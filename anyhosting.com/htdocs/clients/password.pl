#!/usr/bin/perl -w

# Here's the correct password:
$correct = "password";

# Define the page they should go to if the password is correct:
$right_location = "anyhosting.com/";

# Define the page they should go to if the password is wrong:
$wrong_location = "password.html";

# No need to change anything after this point, but feel free to mess around. You might want to try replacing the 'print "Location: $right_or_wrong_location\n\n";' with embeded HTML contents in the way that Perl Dynamic Anything does.

read(STDIN, $input, $ENV{'CONTENT_LENGTH'});
@pairs = split(/&/, $input);

foreach $pair (@pairs) {
        ($name, $value) = split(/=/, $pair);
        $value =~ tr/+/ /;
        $value =~ s/%([a-fA-F0-9][a-fA-F0-9])/pack("C", hex($1))/eg;
        $FORM{$name} = $value;
}
if ($correct eq $FORM{password}) {
        print "Location: $right_location\n\n";
}

else {
        print "Location: $wrong_location\n\n";
}
