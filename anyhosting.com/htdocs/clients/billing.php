<?php
  $name = 'Billing Administration';
  include_once('header.inc');
  include_once("billing.inc");
?>
    <h4>Current billing cycle:</h4>
<?php

  $currentCycle = currentCycle($domain);
  if (!empty($currentCycle)) foreach($currentCycle as $c){
?>
    <p>Payment Due: <strong><?=$c['dueDate']?></strong><br>
<?php
    foreach($c['item'] as $s){
?>
    <?=$s['description']?>
    <?=$s['time']?> @ <?=$s['price']?> = <strong><?=$s['total']?></strong><br>
<?php
    }
?>
    Total due <?=$c['dueDate']?>: <strong><?=$c['total']?></strong>
    </p>
<?php
  }
  
  $billingContact = billingContact($domain);
  if (!empty($billingContact)) foreach($billingContact as $b){
?>
    <h4>Billing contact:</h4>
    <p>
    <?=$b['name']?><br>
    <?=$b['street']?><br>
    <?=$b['city']?>, <?=$bState?><br>
    <?=$b['zip']?><br>
    </p>
    <p>
    <?=$b['email']?><br>
    <?=$b['phone']?><br>
    </p>
    <h4>Billing history:</h4>
    <p>
      <pre>
<?php
  }
  $received = billingHistory($domain);
  if(!empty($received)) foreach($received as $r){
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
?>
      </pre>
    <p><a href="/contact.html">Contact us</a><br>
    Copyright © 2004 AnyHosting Services<br>
    All rights reserved.</p>
  </div>
  </body>
</html>
<?php
  include_once('footer.inc');
?>
