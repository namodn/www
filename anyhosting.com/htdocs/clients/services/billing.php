<?php
  $name = 'Billing Administration';
  include_once('authcheck.inc');
  include_once('header.inc');
  include_once("billing.inc");
?>
    <h4>Current billing cycle:</h4>
      <pre>
<?php

  $currentCycle = currentCycle($domain);
  if (empty($currentCycle)) {
    print "None.";
  }else{
    foreach($currentCycle as $c){
?>
Payment Due: <strong><?=$c['dueDate']?></strong>
<?php
      foreach($c['item'] as $s){
?>
        <?=$s['description']?>

        <?=$s['time']?> @ <?=$s['price']?> = <strong><?=$s['total']?></strong>

<?php
      }
?>
Total due <?=$c['dueDate']?>: <strong><?=$c['total']?></strong>
<?php
    }
  }
?>
      </pre>
    <h4>Billing contact:</h4>
      <pre>
<?php
  $billingContact = billingContact($domain);
  if (empty($billingContact)){
    print "None.";
  }else{
    foreach($billingContact as $b){
?>
<?=$b['name']?>

<?=$b['street']?>

<?=$b['city']?>, <?=$b['state']?>

<?=$b['zip']?>


<?=$b['email']?>

<?=$b['phone']?>
<?php
    }
  }
?>
    </pre>
    <h4>Billing history:</h4>
      <pre>
<?php
  $received = billingHistory($domain);
  if(empty($received)){
    print "None.";
  }else{
    foreach($received as $r){
?>
Paid:  <?=$r['paid']?>
 
Due:   <?=$r['dueDate']?>
 
Total: <?=$r['total']?>
 
<?php
      foreach($r['item'] as $i){
?>
        Description: <?=$i['description']?>

        Time:        <?=$i['time']?>

        Price:       <?=$i['price']?>

        Total:       <?=$i['total']?>

<?php
      }
    }
  }
?>
      </pre>
    <p><a href="/contact">Contact us</a><br>
  </div>
  <p>&copy;2007 AnyHosting</p>
  </body>
</html>
<?php
  include_once('footer.inc');
?>
