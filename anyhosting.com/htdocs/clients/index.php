<?php
  $name = 'Billing Administration';
  include_once('header.inc');
?>
    <ul>
      <li><a href="/clients/email.php?domain=<?=$domain?>">Email Administration</a></li>
      <li><a href="http://<?=$domain?>/webalizer">Usage Statistics</a></li>
      <li><a href="/clients/billing.php?domain=<?=$domain?>">Billing Info</a></li>
    </ul>
    <p><a href="/contact.html">Contact us</a><br>
    Copyright © 2004 AnyHosting Services<br>
    All rights reserved.</p>
  </div>
  </body>
</html>
<?php
  include_once('footer.inc');
?>
