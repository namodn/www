<?php
  $name = 'Billing Administration';
  include_once('authcheck.inc');
  include_once('header.inc');
?>
    <ul>
      <li><a href="/clients/services/email?domain=<?=$domain?>">Email Administration</a></li>
      <li><a href="http://<?=$domain?>/webalizer">Usage Statistics</a></li>
      <li><a href="/clients/services/billing?domain=<?=$domain?>">Billing Info</a></li>
    </ul>
    <p><a href="/contact">Contact us</a><br>
  </div>
  <p>&copy;2009 AnyHosting</p>
  </body>
</html>
<?php
  include_once('footer.inc');
?>
