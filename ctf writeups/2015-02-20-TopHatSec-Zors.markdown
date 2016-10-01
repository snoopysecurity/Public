---
layout:     post
title:      "TopHatSec : Zorz"
subtitle:   "A VulnHub File Upload challenge created by TopHatSec"
date:       2015-02-15 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/post-bg-03.jpg"
---

<a href="https://www.vulnhub.com/entry/tophatsec-zorz,117/">Link to Challenge</a>

<p>ZORZ is another VM created by TopHatSec. This vm involves three malicious file upload challenges.  The challenger will need find ways to bypass different filters to execute system commands on the server. 
I started by port scanning the application with Nmap.
</p>
<blockquote>nmap -A 192.168.0.15</blockquote>
<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/zorz1.png" />
<p>The results indicate port 22 and 80 open. Let’s get started with the application</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/zorz2.png" />

<p>I started by uploading a basic shell which as successful. But, I had trouble finding the upload location. I used the Burp content discovery function to find any hidden directories but this was unsuccessful. </p>
<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/zorz4.png" />

<p>However, I was able to find the uploads directories using custom word lists. </p>
<blockquote>wfuzz -c -z file, /fuzzdb/Discovery/PredictableRes/raft-small-directories-lowercase.txt --hc 404 http://192.168.0.15/FUZZ</blockquote>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/zorz3.png" />

<p>A directory called uploads1 and uploads2 exists and I am able to execute a shell</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/zorz5.png" />

<h3>Level 2</h3>
<p>Level 2 seems to checking the file extension of the uploaded file.</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/zorz6.png" />


<p>
I first tried to bypass this filter by using double extensions. For example, if the application is looking for file image.png. A malicious user can upload a file with double extensions such as image.php.png. This is then process and rendered by the server. But, this didn’t work.
I then tried to add php code to a png image with the double extension; this was successfully accepted by the application.<br>
I used the following reverse shell for the upload : <a href="http://pentestmonkey.net/tools/web-shells/php-reverse-shell">PHP Reverse Shell</a>
</p>


<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/zorz7.png" />



<h3>Level 3</h3>

<p>The Level 3 of the application seems to have a similar sort of check for file uploads. Any invalid format returns an error.</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/zorz8.png" />

<p>To bypass this, I used the same payload from level 2 but I changed the content type to <strong>Content-Type: image/jpeg</strong>. This was accepted by the server as a valid format. </p>


<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/zorz9.png" />


