echo "Content-type: text/plain"                                  
echo ""

#!/usr/local/bin/perl -w
#
# Example CGI program that uses Path Info.
#
# This program is intended to be a "middle man" between
# a document and the http server.  The real document to be served is
# tacked on the URL as extra path info, allowing this program to count
# the number of times the document has been accessed, and then including
# that count on the bottom of the document.
#
# Sid Bytheway
# Administrative Computing Services
# August 1995
#

@valid_dirs = ( "/chpc/usrlocal/aix/mosaic/htdocs/cgi-programming",
        "/chpc/usrlocal/aix/mosaic/htdocs/cgi-forms",
        "/chpc/usrlocal/aix/mosaic/htdocs/cgi-forms" );
$count_root = "/chpc/usrlocal/aix/mosaic/countdir";

$path_info = $ENV{"PATH_INFO"};
$path_translated = $ENV{"PATH_TRANSLATED"};

#
# If no path info on URL, then we have nothing to do.
# --------------------------------------------------
if( !defined($path_info) || $path_info eq "" ||
    !defined($path_translated) || $path_translated eq "" ) {
        $msg = "This URL requires that the PATH_INFO environment variable ";
        $msg .= "be set to a document that can be sent to you.";
        html_die( $msg );
}
$path_info =~ s/\`|\"|\'|\;|\|//g;
# $path_info = `../../support/unescape $path_info`;
$path_translated =~ s/\`|\"|\'|\;|\|//g;
# $path_translated = `../../support/unescape "$path_translated"`;


#
# If path is not in a valid directory - send error.
# --------------------------------------------------
$valid = 0;
foreach $path ( @valid_dirs ) {
    if( $path_translated =~ m/^$path/ ) {
        $valid = 1;
        last;
    }
}
if( ! $valid ) {
    $msg = "The document you requested \"$path_translated\" is in ";
    $msg .= "a directory that is not accessable by this program.";
    html_die( $msg );
}

#
# If document does not exist - send error.
# --------------------------------------------------
if( ! -r $path_translated ) {
    html_die( "The document you requested \"$path_translated\" does not exist or is unaccessable by you." );
}

#
# If count file does not exist, create one.
# --------------------------------------------------
$path = $count_root;
@path_elements = split( "/", $path_info );
for( $i=0; $i<$#path_elements; $i++ ) {
    $path .= "/$path_elements[$i]";
    if( ! -d $path ) {
        mkdir( $path, 0755 ) || html_die( "Couldn't mkdir( $path )\n" );
    }
}

#
# Increment access count.
# --------------------------------------------------
$path = "$count_root/$path_info";
if( ! -e $path ) {
    open( CNT, ">>$path" ) || html_die( "Couldn't create the count file: \"$path\"" );
    close( CNT );
}
open( CNT, "+<$path" ) || html_die( "Couldn't open count file:\"$path\"" );
flock( CNT, 2 );          # Get exclusive lock on file.
seek( CNT, 0, 0 );        # Rewind to begining of file.
$count = <CNT>;           # Get old count.
$count ++;                # increment it.
seek( CNT, 0, 0 );        # Rewind to begining of file.
print( CNT $count."\n" ); # write back new count.
flock( CNT, 8 );          # unlock the file.
close( CNT );             # close the file.

#
# Send document, including access count on the bottom.
# --------------------------------------------------
$inserted_count = 0;
open( DOC, $path_translated ) || html_die( "Couldn't open document." );
print( "Content-type: text/html\n\n" ); # Assume it's an HTML document.
while( $line=<DOC> ) {
    if( ! $inserted_count && ($line =~ m/<\/body>|<\/BODY>|<\/Body>/) ) {
        $line =~ s/(<\/body>|<\/BODY>|<\/Body>)/<i><a href=\/cgi-programming\/>CGI Programming Tutorial Menu<\/a><br><a href=\/cgi-forms\/>HTML Forms Processing Tutorial Menu<\/a><br><font size=-1>Access Count = $count<\/font><\/i>$1/;
        $inserted_count = 1;
    }
    print( $line );
}
close( DOC );
if( ! $inserted_count ) {
    print( "<i><font size=-1>Access Count = $count</font></i>\n" );
