<?php
  $name = 'Billing Administration';
  include_once('header.inc');
  include_once("billing.inc");
?>
    <h4>Current billing cycle:</h4>
<?php

  $currentCycle = currentCycle($domain);
  foreach($currentCycle as $c){
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
  foreach($billingContact as $b){
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
    Received Period Fee Status Amount Type<br>
<?php
  }
  $received = billingHistory($domain);
  foreach($received as $r){
?>
    <?=$r['date']?>
    <?=$r['period']?>
    <?=$r['fee']?>
    <?=$r['status']?>
    <?=$r['total']?>
    <?=$r['type']?>
    <br>
<?php
  }
?>
    <p><a href="/contact.html">Contact us</a><br>
    Copyright © 2004 AnyHosting Services<br>
    All rights reserved.</p>
  </div>
  </body>
</html>
<?php
  include_once('footer.inc');
?>
