<?php
  include_once('io.inc');
  $name = 'Administration';
  include_once('header.inc');

  $currentCycle = read($domain,'currentCycle');
  $billingContact = read($domain,'billingContact');
  $billingHistory = read($domain,'billingHistory');

  if (empty($currentCycle)){
    $currentCycle = array();
  }

  if (!empty($_REQUEST['paid'])){
    $paidCycle = key($_REQUEST['paid']['cycle']);
  }
  if (!empty($_REQUEST['addCycle'])){
    $blank = array(
      'dueDate' => null,
      'item' => array(),
      'total' => null,
    );
    array_push($currentCycle, $blank);
    write($domain,'currentCycle',$currentCycle);
    $currentCycle = read($domain,'currentCycle');
  }
  if (!empty($_REQUEST['add'])){
    $addCycle = key($_REQUEST['add']['cycle']);
    $blank = array(
      'description' => null,
      'time' => null,
      'price' => null,
      'total' => null,
    );
    array_push($currentCycle[$addCycle]['item'], $blank);
    write($domain,'currentCycle',$currentCycle);
    $currentCycle = read($domain,'currentCycle');
  } elseif (!empty($_REQUEST['remove'])){
    $removeCycle = key($_REQUEST['remove']['cycle']);
    if($_REQUEST['remove']['cycle'][$removeCycle] == "Remove Cycle"){
      unset($currentCycle[$removeCycle]);
      write($domain,'currentCycle',$currentCycle);
      $currentCycle = read($domain,'currentCycle');
    }else{
      $removeItem = key($_REQUEST['remove']['cycle'][$removeCycle]['item']);
      unset($currentCycle[$removeCycle]['item'][$removeItem]);
      write($domain,'currentCycle',$currentCycle);
      $currentCycle = read($domain,'currentCycle');
    }
  } elseif (!empty($_REQUEST['save'])){
    $currentCycle = $_REQUEST['cycle'];
    foreach(array_keys($currentCycle) as $cycles){
      if(empty($currentCycle[$cycles]['item'])){
        $currentCycle[$cycles]['item'] = array();
      }
    }
    write($domain,'currentCycle',$currentCycle);
    $currentCycle = read($domain,'currentCycle');
  }

?>
    <form name="admin" method="POST">
    <input type="hidden" name="domain" value="<?=$domain?>">
    <pre>
<input type="submit" value="Save All" name="save">
<input type="submit" value="Add Cycle" name="addCycle">

<?php
  foreach(array_keys($currentCycle) as $cycles){
    $c = $currentCycle[$cycles];
?>
Due date:    <input type="text" name="cycle[<?=$cycles?>][dueDate]" 
             value="<?=$c['dueDate']?>">
Grand total: <input type="text" name="cycle[<?=$cycles?>][total]" 
             value="<?=$c['total']?>">
Paid on: <input type="text" name="cycle[<?=$cycles?>][paid]" 
             value="<?=$c['paid']?>">
<input type="submit" value="Paid" name="paid[cycle][<?=$cycles?>]">  <input type="submit" value="Add Item" name="add[cycle][<?=$cycles?>]">  <input type="submit" value="Remove Cycle" name="remove[cycle][<?=$cycles?>]">

<?php
    if($c['item'])
      foreach(array_keys($c['item']) as $items){
        $s = $c['item'][$items];
?>
        Description: <input type="text" 
	             name="cycle[<?=$cycles?>][item][<?=$items?>][description]" 
                     value="<?=$s['description']?>">
        Time spent:  <input type="text" 
	             name="cycle[<?=$cycles?>][item][<?=$items?>][time]" 
		     value="<?=$s['time']?>">
        Price per:   <input type="text" 
	             name="cycle[<?=$cycles?>][item][<?=$items?>][price]" 
		     value="<?=$s['price']?>">
        Total:       <input type="text" 
	             name="cycle[<?=$cycles?>][item][<?=$items?>][total]" 
		     value="<?=$s['total']?>">
        <input type="submit" value="Remove Item" name="remove[cycle][<?=$cycles?>][item][<?=$items?>]">

<?php
      }
?>
<?php
  }
  print_r($currentCycle);
?>
    </pre>
    </form>
<?php


/*
  // billingContact
  $b = array(
  'name' => 'Robert Helmer',
  'street' => '532 Liberty Street',
  'city' => 'El Cerrito',
  'state' => 'CA',
  'zip' => '94530',
  'phone' => '510-555-1212',
  'email' => 'rhelmer@anyhosting.com',
  );
  $billingContact = array($b);
  write('foxtailsomersault.com','billingContact',$billingContact);

  // billingHistory
  $r1 = array(
    'date' => '09/01/2001',
    'period' => '12 months',
    'fee' => '$5/mo',
    'status' => 'PAID',
    'total' => '$60.00',
    'type' => 'Check'
  );
  $billingHistory = array($r1);
  write('foxtailsomersault.com','billingHistory',$billingHistory);
*/
   
  include_once('footer.inc');
?>
