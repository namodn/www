<?php  
  $name = 'Billing Administration';
  include_once('header.inc');
  $aliases = "/etc/exim-aliases"; 

  function get_users(){
    $properties = explode("\n", trim(_get_file()));
    $users = array();
    foreach ($properties as $nameValue){
      if (preg_match("/^#/", $nameValue)){
        continue;
      }
      list($propName, $propValue) = explode(":", trim($nameValue), 2);
      $users[$propName] = trim($propValue);
    }
    return $users;
  }

  function _get_file(){
    global $aliases;
    global $domain;
    $filename = "$aliases/$domain.aliases";
    $handle = fopen("$filename","r");
    $contents = fread($handle, filesize($filename));
    fclose($handle);
    return $contents;
  }
?>
    <pre>
<?php
  $users = get_users();
  foreach ($users as $alias => $email){
    if ($alias == '*'){
      $alias = 'everything else';
    }
    if ($email == ':blackhole:'){
?>
<input type="text" name="<?=$alias?>" value="<?=$alias?>"><select name="reject">
<option value="blackhole" selected>goes nowhere
<option value="fail">fails with message:
</select><input type="text" name="fail_message" value="">
<?php
    } elseif (preg_match("/^:fail:/", $email)){
      $fail = explode(":fail:", $email);
      $fail_message = trim($fail[1]);
?>
<input type="text" name="<?=$alias?>" value="<?=$alias?>"><select name="reject">
<option value="blackhole">goes nowhere
<option value="fail" selected>fails with message:
</select><input type="text" name="fail_message" value="<?=$fail_message?>">
<?php
    } else {
?>
<input type="text" name="<?=$alias?>" value="<?=$alias?>"> is emailed to <input type="text" name="<?=$email?>" value="<?=$email?>" size="30">
<?php
    }
  }
?>

<input type="submit" value="Submit">
    </pre>
<?php
  include_once('footer.inc');
?>

