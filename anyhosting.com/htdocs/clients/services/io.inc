<?php
function create($dirname){
  $filename = "/var/www/DOMAINS.list";
  $handle = fopen($filename,"r");
  $contents = fread($handle,filesize($filename));
  fclose($handle);
  $lines = explode("\n", $contents);
  $isValid = false;
  foreach($lines as $l){
    if ($l == $dirname){
      $isValid = true;
    }
  }
  if($isValid == true){
    if(!is_dir($dirname)){
      mkdir($dirname, 0700);
    }
  } else {
    print "Domain $domain unknown.";
    include_once('footer.inc');
    exit;
  }
}
function write($domain,$name,$object){
  create($domain);
  $filename = "$domain/$name.obj";
  $blob = serialize($object);
  $handle = fopen($filename,"w");
  fwrite($handle, $blob);
  fclose($handle);
  return $filename;
};
function read($domain,$name){
  create($domain);
  $filename = "$domain/$name.obj";
  if(is_readable($filename)){
    $handle = fopen($filename,"r");
    $object = unserialize(fread($handle,filesize($filename)));
    fclose($handle);
  } else{
    //print "$filename is not readable.";
  }
  return $object;
}
?>
