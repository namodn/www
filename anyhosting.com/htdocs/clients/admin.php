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
  if (empty($billingContact)){
    $billingContact = array();
  }
  if (empty($billingHistory)){
    $billingHistory = array();
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
    if(!empty($currentCycle)){
      foreach(array_keys($currentCycle) as $cycles){
        if(empty($currentCycle[$cycles]['item'])){
          $currentCycle[$cycles]['item'] = array();
        }
      }
      write($domain,'currentCycle',$currentCycle);
      $currentCycle = read($domain,'currentCycle');
    }
    if(!empty($_REQUEST['billingContact'])){
      $billingContact = array($_REQUEST['billingContact']);
      write($domain,'billingContact',$billingContact);
      $billingContact = read($domain,'billingContact');
    }
  } elseif (!empty($_REQUEST['paid'])){
    $cycles = key($_REQUEST['paid']['cycle']);
    array_push($billingHistory, $currentCycle[$cycles]);
    unset($currentCycle[$cycles]);
    write($domain,'currentCycle',$currentCycle);
    $currentCycle = read($domain,'currentCycle');
    write($domain,'billingHistory',$billingHistory);
    $billingHistory = read($domain,'billingHistory');
  }

?>
    <form name="admin" method="POST">
    <input type="hidden" name="domain" value="<?=$domain?>">
    <pre>
<?php
  if(!empty($billingContact)) foreach($billingContact as $b){
?>
<input type="submit" value="Save All" name="save">
Name:    <input type="text" name="billingContact[name]" value="<?=$b['name']?>">
Street:  <input type="text" name="billingContact[street]" value="<?=$b['street']?>">
City:    <input type="text" name="billingContact[city]" value="<?=$b['city']?>">
State:   <input type="text" name="billingContact[state]" value="<?=$b['state']?>">
Zipcode: <input type="text" name="billingContact[zip]" value="<?=$b['zip']?>">
Phone:   <input type="text" name="billingContact[phone]" value="<?=$b['phone']?>">
Email:   <input type="text" name="billingContact[email]" value="<?=$b['email']?>">
<input type="submit" value="Add Cycle" name="addCycle">
<?php
  }
?>

<?php
  if(!empty($currentCycle)) foreach(array_keys($currentCycle) as $cycles){
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
  //print_r($currentCycle);
?>
    </pre>
    </form>
<?php


   
  include_once('footer.inc');
?>
