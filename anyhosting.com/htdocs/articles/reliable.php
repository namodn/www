<?php include 'header.php'?>
    <h1>Reliable, scalable, and growable web services</h1>
    <h3>Author: Robert Helmer <a href="mailto:rhelmer@anyhosting.com">rhelmer@anyhosting.com</a></h3>
    <b>Reliability</b>
    <p>Unexpected events happen all the time; your server's hard drive stops
    working, software malfunctions, the network connection goes down.
    Building <a href="http://en.wikipedia.org/wiki/Fault-tolerance">fault-tolerant</a>
    systems is essential to keep your customers happy.
    </p>
    <p>
    How can you approach this? Consider one of the above scenarios: your
    server's hard drive crashes. One simple approach is, for every server,
    to have a "cold standby", that is, an idle server that is waiting to
    fail in if the first should stop working. This works well enough, but
    has two large drawbacks:
    <ul>
      <li>One of your servers sits unused most of the time</li>
      <li>There must be some sort of failover monitoring in place, which can
      be complex and must be tested often to make sure that it will work
      in the critical moment</li>
    </ul>
    </p>
    <p>
    More importantly, you want to build an infrastructure that scales; one
    that you can add servers to as you acquire more customers, without
    having a large setup cost.
    </p>
    <b>Scalability</b>
    <p>One easy way to handle the above "dead hard drive" scenario is 
    to make your services <a href="http://en.wikipedia.org/wiki/Scalability">scalable</a> by default. For instance, have multiple servers (at least 2) behind
    some kind of <a href="http://en.wikipedia.org/wiki/Load_balancing_(computing)">load-balancing</a> equipment. As you need to service more requests, you can
    add more servers.</p>
    <center>
      <img src="scalable_before.png" 
       alt="Diagram of simple load-balanced network.">
    </center>
    <p>Note that all network requests from the internet first go to your
    load balancer, which forwards the requests on to the actual web servers.
    You can add fault-tolerance to the load-balancers too; they can be
    connected to eachother and take over as-needed<p>
    <center>
      <img src="scalable_after.png" 
       alt="Diagram of simple load-balanced network, adding a server.">
    </center>
    <p>Keep in mind that you can add or remove servers anytime you want, to
    upgrade or replace faulty components.
    <b>Growability</b>
    <p>Eventually, you'll want to put newer servers in; whether for software
    compatibility, or because you've hit the expansion limit for that model.
<?php include 'footer.php'?>
