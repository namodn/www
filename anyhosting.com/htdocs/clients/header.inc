<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
"http://www.w3.org/TR/html4/strict.dtd">

<html>
  <head>
    <title><?=$name?></title>
     <link type="text/css" title="normal" rel="stylesheet" href="/normal.css">
  </head>
  <body>
  <div id="main">
    <h1>AnyHosting Services</h1>
    <h2><?=$name?></h2>
    <h3>Domain: <?=$domain?></h3>

<?php
  $aliases = "/etc/exim-aliases"; 
  $domain = $_REQUEST['domain'];
?>
