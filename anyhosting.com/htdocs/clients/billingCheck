#!/usr/bin/php4 -q
<?php
  include_once('billing.inc');
  $today = date("m/d/Y");
  $filename = "/var/www/DOMAINS.list";
  $handle = fopen($filename,"r");
  $contents = fread($handle,filesize($filename));
  fclose($handle);
  $lines = explode("\n", $contents);
  foreach($lines as $domain){
    if(!empty($domain)){
      $currentCycle = currentCycle($domain);
      if(!empty($currentCycle)) foreach($currentCycle as $c){
        if($today == $c['dueDate']){
          print "$domain is due today.\n";
        }
      }
    }
  }    
?>
