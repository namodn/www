#!/usr/bin/php4 -q
<?php
  include_once('billing.inc');
  
  $today = date("m/d/Y");
  $domain='customweather.com';
  $currentCycle = currentCycle($domain);

  foreach($currentCycle as $c){
    if($today == $c['dueDate']){
      print "$domain is due today.\n";
    }
  }
?>
