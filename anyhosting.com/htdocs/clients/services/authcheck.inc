<?php
  include_once('io.inc');
  $aliases = "/etc/exim-aliases"; 
  $domain = $_REQUEST['domain'];

  if(!isValid($domain)){
    echo "Invalid domain ".$domain;
    exit;
  }
?>
