---
layout:     post
title:      "Google XSS Challenge -  Solutions"
subtitle:   "Solutions to Google's online XSS Challenge"
date:       2014-10-24 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/post-bg-06.jpg"
---



<p>Link: <a href="https://xss-game.appspot.com/">Link to XSS Challenge</a></p>

<p>The Google XSS challenge is a 6 level game on executing XSS in different contexts. I found this challenge useful due to the actual code being shown so a player can get better understanding on how to execute different XSS payloads.</p>


<h2 class="section-heading"> Level 1: Hello, world of XSS</h2>

<p>This level was easy. All a challenger has to do is input a payload into the query parameter.</p>

<blockquote><svg/onload=alert(9)></blockquote>

<p>I like to use the svg tag since it is rarely used and is shorter than most payloads.</p>

<h2 class="section-heading"> Level 2: Persistence is key</h2>

<p> Level 2 is also pretty easy.  The payload inputted by the user is rendered back in a blockquote.  	

<blockquote>&quot;&gt;<svg/onload=alert(9)></blockquote>

<h2 class="section-heading"> Level 3: That sinking feeling…</h2>

<p>In the level, the image loaded on the page uses the window.location.hash javascript property. This can be confirmed by looking at the provided source code. This can be exploited by adding the following<p>

<blockquote>1.jpg' onload='javascript:alert(1);'</blockquote>


<h2 class="section-heading"> Level 4: Context matters</h2>

In this example, the time variable is reflected back within an existing script tag. This means that there is no need to breakout of the tag. The following payload can be used to execute JavaScript </p>

<blockquote>");alert(1);//</blockquote>

<h2 class="section-heading">Level 5: Breaking protocol</h2>

<p> In this example, the input is reflected back inside a href tag. The following payload can be used to execute alert to pass this challenge </p>

<blockquote>javascript:alert(1);</blockquote>


<h2 class="section-heading">Level 6: Follow the rabbit</h2>

<p> This challenge was quite tricky. To break out of this context, a challenger can use the data URI to execute an alert.<p> 

<blockquote>data:text/javascript,alert(1);</blockquote>

<p> Thanks for reading my write-up. The challenge is still open so have a try. Furthermore, I recently did a talk on XSS and different contexts; this presentation can be found <a href="http://www.slideshare.net/snoopythesecuritydog/xss-primer-snoopysecurity">here</a></p>