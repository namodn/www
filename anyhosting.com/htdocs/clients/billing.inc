<?php

include_once("io.inc");

function currentCycle($domain){
  $currentCycle = read($domain, 'currentCycle');
  return $currentCycle;
}
function billingContact($domain){
  $billingContact = read($domain, 'billingContact');
  return $billingContact;
}
function billingHistory($domain){
  $billingHistory = read($domain, 'billingHistory');
  return $billingHistory;
}
?>
