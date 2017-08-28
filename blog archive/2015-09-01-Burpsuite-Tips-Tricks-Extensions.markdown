---
layout:     post
title:      "Burp Suite – Tips, Preferences and Extensions"
subtitle:   "Some useful tips,preferences and my favourite extensions."
date:       2015-09-01-01 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/b_1.png"
---

<p>Burp Suite is one of my favourite tools when looking for vulnerabilities in Web Applications. Burp Suite has multiple tools with it including spider, scanner, fuzzer for numerous test cases. In this blog post, I will share some of my preferences, tricks and extensions that I like to use.</p>

<p>Note: Most of these features are only available for Burp Suite Pro version.</p>

<h2>Preferences – Make Burp Suite more efficient</h2>

<p><b><u>Burp Filter</u></b></p>

<p>Burp Filter is a very useful functionality for clearing out unwanted requests. I like to use the 'Show only in-scope items' to clear out any site that are not it scope. Furthermore, the 'Show only parameterized requests' can be useful when identifying suspicious parameters quickly. I also like to hide empty folders and filter responses by MIME type depending on the application I am testing.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/01.png" style="width: 1089px; height: 307px;" />
<p>Location: [Target][Filter]</p>

<p><b><u>Starting Burp Suite with assigned memory</u></b></p>

<p>Burp Suite can sometimes take up a lot of memory if you running content discovery or Spider with a lot of threads. This can be prevented by starting Burp Suite with allocated memory. Run the following command in your terminal to start Burp Suite with allocated memory.</p>

<blockquote>Java –Xmx2g –jar /pathtoburp/burp.jar</blockquote>

<p><b><u>Form Submission</u></b></p>

<p>Form Submission is a useful setting that controls how the Burp Spider submits forms. Depending on the application you are testing, it is useful to set the appropriate setting. E.g. if you are testing a live functional site and don't want to submit random junk data, it is a good idea to select 'Prompt for guidance'</p>

<p>Furthermore, if you are testing a live functional site it is best to reduce the spider engine throttle to a lower setting. The Burp default values can also be changed to uniquely identify your spider.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/02.png" style="width: 1089px; height: 367px;" />
<p>Location: [Spider][Options](Form Submission)</p>

<p><b><u>Authenticated Spidering</u></b></p>

<p>If you scroll down Spider Options page, there is an Application Login setting. This can be used if you want to use spider while being authenticated to your target site. If you enable this setting, Burp will submit your configured username and password when interacting with login forms. This is useful when trying to find any hidden functionalities a standard use might have.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/03.png" style="width: 800px; height: 400px;" />
<p>Location: [Spider][Options](Application Login)</p>

<p><b><u>Exclude from scope</u></b></p>

<p>Exclude from scope is a useful function to make sure that you Spider and Scanner is not crawling or scanning any logout or sign-out pages. By default, Burp has some values excluded from scope. If you are attacking a application which has custom functions to delete or edit users, it is a good idea to add them to exclude for scope. It is always best to manually browse the site to understand what functionality is available to the user first.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/04.png" style="width: 728px; height: 250px;" />
<p>Location: [Target][Scope](Exclude from scope)</p>

<p><b><u>Active Scan optimization</u></b></p>

<p>By default, Burp scanner is configured with normal scan speed and accuracy. You change this setting to make the scanner more thorough and minimize false positives.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/05.png" style="width: 870px; height: 223px;" />
<p>Location: [Scanner][Options](Active Scanning Optimization)</p>

<p><b><u>Burp Automatic Backup</u></b></p>

<p>Burp’s Automatic Backup feature makes it very convenient to save the current Burp state and configuration at a specific time or interval. This useful feature stores a backup copy of your tasks in the event that Burp crashes or exits abnormally. This is a good alternative to saving Burp State and configuration manually.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/06.png" style="width: 850px; height: 370px;" />
<p>Location: [Options][Misc](Automatic Backup)</p>

<p><b><u>Turning off interception at start-up</u></b></p>

<p>Burp's Interception mode is turned on by default when starting Burp Suite. This can be aggravating in due time. You can turn off interception at start-up by going to /Proxy/Options and selecting the 'disable interception at start-up' checkbox.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/07.png" style="width: 735px; height: 253px;" />
<p>Location: [Proxy][Options](Miscellaneous)</p>

<h2>Tips – Information that might be useful</h2>

<p><b><u>Adding exception to Scanner</u></b></p>

<p>Often when scanning applications, you might find a web application firewall or Intrusion Detection System blocking you if a certain parameter is tampered with. You can configure Burp Scanner to skip these parameters by adding a skip parameter rule.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/08.png" style="width: 900px; height: 241px;" />
<p>Location: [Scanner][Options](Attack Insertion Points)</p>

<p><b><u>Active Scan specific parameters</u></b></p>

<p>Active Scan can be dangerous depending on the setting you are using and the application you are analyzing. Passive scan only checks your existing requests and responses and does not send any new requests. Sometimes, it is more efficient to have passive scan on by default and just active scanning selected parameters. This can be achieved by sending a request into intruder, then right-clicking the parameter and selecting 'Actively scan defined insertion points'.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/09.png" style="width: 853px; height: 419px;" />
<p>Location: [Intruder][Positions](Right-Click selected parameter)</p>

<p><b><u>Scheduling automatic tasks</u></b></p>

<p>If you are developer who just likes to use the scanner or a Pentester short of time, the Schedule task function is useful to automate tasks such as active/passive scanning, spidering etc. This can be useful in a scenario where you want Burp running in the background on certain intervals.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/10.png" style="width: 796px; height: 296px;" />
<p>Location: [Options][Misc](Scheduled Tasks)</p>

<p><b><u>Intruder Grep matching</u></b></p>

<p>Burp Intruder is a tool for automating attacks against web applications. This is particular useful when fuzzing an application to find vulnerabilities. This can sometimes be a hard task if the there are many payloads which makes it is hard to filter for results</p>

<p>Using the Grep Match function in Burp Intruder is a useful way to fuzz an application and look for a specific errors quickly. You can add different keywords and flag responses that match the given keyword.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/11.png" style="width: 731px; height: 449px;" />
<p>Location: [Intruder][Options](Grep - Match)</p>

<p><b><u>Payload Processing</u></b></p>

<p>Payload processing is another useful feature of the Burp Intruder. This can be used define rules to perform various processing tasks on each payload before it is used. This can be used if you want to add prefix, suffix and hashes to your payload list. This is quicker than adding prefixes manually and loading up lists.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/12.png" style="width: 1027px; height: 347px;" />
<p>Location: [Intruder][Payloads](Payload Processing)</p>

<p><b><u>Using Macros</u></b></p>

<ul><li>Authentication</li><li>Checking for valid sessions</li><li>Any multi-stage process such as two-step authentication and more.</li></ul>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/13.png" style="width: 867px; height: 307px;" />
<p>Location: [Options][Sessions](Macros)</p>

<p>I mainly use this feature to create login macros so I don’t have to login repeatedly. Here is an example written by @ccampbell232</p>

<p>Step by Step instructions here:  <a href="http://fvaahe.com/creating-a-login-macro-for-burp-suite/">Burp Login Macro</a></p>

<p><b><u>Using Custom payloads and wordlists</u></b></p>

<p>Burp Intruder comes with some default payloads for fuzzing including usernames, password and directory lists. Sometimes, it can be useful to use custom wordlists and payloads which could reveal additional vulnerabilities. Here are two of my favourites:</p>

<p>FuzzDB:  <a href="https://github.com/rustyrobot/fuzzdb">Click Here</a></p>
<p>Seclists:  <a href="https://github.com/danielmiessler/SecLists">Click Here</a></p>

<p>Also, you can extract Burp payloads to use with any other tools by opening the burp.jar file with any rar archiver tool. You can find the payloads by going to /resources/PayloadStrings.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/14.png" style="width: 603px; height: 422px;" />

<p><b><u>Useful Hotkeys</u></b></p>

<ul><li>Ctrl+R : Send to repeater</li><li>Ctrl+I: Send to Intruder</li><li>Ctrl+F: Forward intercepted Proxy message</li><li>Ctrl+Shift+S: Switch to Scanner</li><li>Ctrl+Equals: Go to next tab</li></ul>

<p>The default keys can be changed by going to /Options/Misc/Hotkeys</p>

<p><b><u>Other Useful Information</u></b></p>

<p>Use Burp Suite over Tor Network: <a href="https://www.youtube.com/watch?v=Z9s0CS6x00s">Link</a></p>
<p>Configuring an IOS device to proxy through Burp: <a href="https://support.portswigger.net/customer/portal/articles/1841108-configuring-an-ios-device-to-work-with-burp">Link</a></p>
<p>Configuring an android device to proxy through Burp:  <a href="https://support.portswigger.net/customer/portal/articles/1841101-configuring-an-android-device-to-work-with-burp">Link</a></p>

<p><b><u>My favourite extensions</u></b></p>

<ul><li>ActiveScan++: Checks for Host header attacks and OS command injection.</li><li>HTML5 Auditor: Checks for HTML5 features in target e.g. web sockets, client side storage etc.</li><li>CO2: Has numerous modules including SQLMapper, JS Beautifier and ASCII Payload processor.</li><li>Crypto Attacker: Looks for common cryptography flaws such as ECB and padding Oracle attacks.</li><li>Hackvector: A conversion extension to aid in XSS, SQL Injection and fuzzing.</li><li>CSRF Scanner: Passively scan for CSRF vulnerabilities but has a lot of false positives and unwanted alerts. I like to look for CSRF manually and using CSRF POC in engagement tools to validate the finding.</li></ul>

<p>This is just a short introduction of Burp's full power! Thanks for reading.</p>

