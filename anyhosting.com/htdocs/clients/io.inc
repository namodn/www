<?php
function write($domain,$name,$object){
  $blob = serialize($object);
  $filename = "$domain/$name.obj";
  $handle = fopen($filename,"w");
  fwrite($handle, $blob);
  fclose($handle);

  return $filename;
};
function read($domain,$name){
  $filename = "$domain/$name.obj";
  $handle = fopen($filename,"r");
  $object = unserialize(fread($handle,filesize($filename)));
  fclose($handle);

  return $object;
}
?>
