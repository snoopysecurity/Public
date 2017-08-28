---
layout:     post
title:      "6 things you didn't know Drozer could do"
subtitle:   "Some useful Drozer tricks"
date:       2015-10-23-01 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/burppost/drozer.png"
---

<h3>1 : Intent Sniffing</h3>

<p>Intent sniffing is an attack vector use to capture exposed intents.  In certain cases, applications will broadcast intents and will not define any permissions that in need to receive the intent.  This can then be captured by a malicious application.
So passing sensitive data via Intents might potentially be dangerous. A popular tool used by most consultants (Link here:https://www.nccgroup.trust/us/about-us/resources/intent-sniffer/) called intent sniffer can be used. But it is possible to test for this vulnerability using Drozer.</p> 

<p>Drozer has a module called <blockquote>app.broadcast.sniff</blockquote> which can be used to sniff rogue intents. The below example is Drozer capturing all intents sent to battery changed receiver.
</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/sniff.png" />


<h3>2 : Finding debuggable applications quickly</h3>

<p>If application is marked as debuggable, then a user can step through code, view variable values, and pause execution of an application. This can be very useful for an attacker since he can try to run arbitrary code under that application permission, hook into certain methods and modify set variables. </p>

<p> Drozer has a module called <blockquote>app.package.debuggable</blockquote> which can be used to find exploitable applications.  This simply looks for android:debuggable value in the AndroidManifest.xml but it is a more efficient way of searching for debuggable applications.</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/sniff2.png" />


<h3>3 :  Finding applications with backup enabled</h3>

<p>Android functionality allows backups and restoration of its data without having root permissions. This feature of android uses ADB backup that allows applications to be backed up to the cloud. This means that if a user replaces or wipes their phone, they can restore app settings. But if an attacker can get physical access to the device and take the backup of the app, he can modify the headers and restore it to the application’s original state.</p>
<p>This is a low hanging vulnerability but it is still useful to find in applications. As always, the Drozer module run <blockquote>app.package.backup</blockquote> can be used to find applications with backup flag enabled in its manifest file.  
</p>

<img alt="" src="http://snoopysecurity.github.io/img/burppost/sniff3.png"/>


<h3>4 :  Capturing Clipboard content with Drozer</h3>

<p>All android mobile system has a clipboard which is used by all applications installed on the device. In certain scenarios, applications will store sensitive values such as passwords which can be read and altered by any application. More information about clipboard here: http://developer.android.com/reference/android/content/ClipboardManager.html</p>

<p>The drozer module post.capture.clipboard can be used to view clipboard content from any application. It should be noted that the clipboard module will need to be installed in Drozer first.</p>



<img alt="" src="http://snoopysecurity.github.io/img/burppost/sniff4.png" />


<h3>5 :  AddJavaScriptInterface Arbitrary Code Execution</h3>

<p>The Add JavaScript Webview code execution is a vulnerability found in most applications. WebView supports usage of JavaScript which allows execution of remote code through a man in the middle attacker. <p>

<p>The Drozer module scanner.misc.checkjavascriptbridge can very useful when trying to identify the vulnerability.  By running the command <blockquote>run scanner.misc.checkjavascriptbridge</blockquote> it is possible to identify vulnerable applications</p>


<img alt="" src="http://snoopysecurity.github.io/img/burppost/sniff5.png" />


<h3>6 :  Rebuilding Drozer Agent with permissions</h3>

<p>By default, Drozer agent apk only comes with internet access permission. Sometimes you might have to rebuild Drozer agent with certain permissions for various tasks. e.g. Querying permission protected providers, testing custom permissions etc. <p>

<p> This can be done in command line by using<blockquote> Drozer agent build --permission android.permission.[PERMISSION YOU WANT]</blockquote> This is easier than decompiling the app, making edits to the manifest and recompiling again.</p>



<h3>Bonus :  Drozer built in scanning capabilities</h3>

<p> Other useful commands that are worth knowing
<ul>
  <li>scanner.provider.injection - Test content providers for SQL injection vulnerabilities.</li>
  <li>scanner.provider.sqltables - Show all table names accessible through any SQL injection vulnerabilities.</li>
  <li>scanner.provider.traversal - Test content providers for directory traversal.</li>
  <li>scanner.misc.readablefiles & writablefiles - Find world-readable files and world-writable files in the given folder. This is easier than browsing each possible directories and using 'ls -la' to see permissions.</li>
  <li>scanner.provider.finduris - Search for content providers that can be queried. </li>  
 
</p>



