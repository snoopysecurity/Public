---
layout:     post
title:      "TopHatSec : Freshly"
subtitle:   "A VulnHub VM challenge created by TopHatSec"
date:       2015-02-20 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/post-bg-02.jpg"
---

<a href="https://www.vulnhub.com/entry/tophatsec-freshly,118/">Link to Challenge</a>

<p>This is a boot to root vm challenge written by TopHatSec. Here are my solutions to the challenge. I started by portscanning the virtual machine with nmap</p>


<blockquote>nmap -A 192.168.0.12</blockquote>

<p>which gave me results indicating port 80 was open. I opened up Burp Suite and started mapping the application with content discovery.</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/freshly1.png" />

<p>This led me to the login page. Since I don’t have any credentials, I tried sql injection. It is obvious that the application is vulnerable to a blind SQL injection.</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/freshly2.png" />

<p>So I enumerated all the databases looking for user credentials to the previously found phpadmin page or the login page which is vulnerable to SQL injection.</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/freshly3.png" />


<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/freshly4.png" />

<p>
These credentials didn’t work for both login pages. So I was stuck for a while.
</p><br>

<p>So I initialised a full dump of the database and looked for clues. I found a database called <strong>wordpress8080</strong>; so it is possible that the virtual machine is running wordpress as well. This can be found using a full port scan.</p>

<blockquote>nmap -p 1-65535 –sV -sT -T4 192.168.0.12</blockquote>

<p>This led me to port 8080 open on the application which leads to a Wordpress installation.</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/freshly5.png" />

<p>Since we already have an exploitable SQL injection vulnerability, we can use this to look for WordPress admin credentials. This can be found under table users in the worpress8080 database.<p>

<li>Username : admin</li>
<li>Password : SuperSecretPassword</li>

<p>
Now that you have admin privileges, you can just edit of the existing WordPress pages with a PHP reverse shell. This will then be processed and will make a connection back your listener.
</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/freshly6.png" />
<br>

<a href="http://pentestmonkey.net/tools/web-shells/php-reverse-shell">PHP Reverse Shell from pentestmonkey</a><br>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/freshly7.png" />

<p>It is also possible to add a vulnerable plugin and get a shell that way.</p>

