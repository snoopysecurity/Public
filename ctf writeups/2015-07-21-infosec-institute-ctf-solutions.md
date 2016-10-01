---
layout:     post
title:      "Practical Web Hacking - InfoSec Institute CTF Solutions"
subtitle:   "A 13-level simple vulnerable Web App challenge focused on Owasp Top 10"
date:       2015-07-21 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/post-bg-06.jpg"
---
<p>In my spare time, I like to play CTFs and try and challenges to sharpen my basic skills and knowledge. I recently saw a practical web hacking challenge by InfoSec Institute and decided to have a go. For those who don't know, InfoSec Institute is a really good website with tons of free training resources and articles written by skilled professionals. </p>
<p> The challenge itself is a vulnerable web application aimed at rookies and web developers. Eventhough I am quite experienced, I decided to have a go at the challenges. Here are the solutions! </p>
<p>Practical Web Hacking CTF: <a href="http://ctf.infosecinstitute.com/ctf2/">CTF Link</a></p>
<p>Website: <a href="http://www.infosecinstitute.com">InfoSec Institute Main Website</a></p>
<h2 class="section-heading"> Level 1: Cross-Site Scripting</h2>
<p>Level 1 is an easy challenge. The goal of the challenge is to inject '<scrit> alert('Ex1') </script>' into a field. I started the challenge by looking at any external java scripts and any field validations. </p>

<img alt="" src="http://s12.postimg.org/aek5f1mxp/level_1.png" style="width: 689px; height: 67px;" />
<p>By looking at the DOM, It is obvious that the form field has validation in place. To inject an XSS payload, you will need to remove the 'pattern' and 'maxsize' attribute so you can inject anything without being blocked by client side validation. </p>
<p>If you inject a script tag now, the application will use ex1.js to trim and replace less than and greater than sign. I used the chrome developer tools to edit the page source and removed '.trim().replace()'. You can also use the edit source firefox add-on to edit ex1.js and remove the time and js function. </p>
<img alt="" src="http://s1.postimg.org/qumdw1sq7/level_1_final.png" style="width: 600px; height: 322px;"/>
<h2 class="section-heading"> Level 2: Injection</h2>
<p>The objective of level 2 is to inject PHP statements into an operand field. I found this challenge quite hard; I tried entering negative values, php code and float point numbers into the fields which resulted in error. The hints made it clear that I need to break an eval function and both operands are validated correctly. I searched the internet for answers and found a couple of solutions. </p>
<img alt="" src="http://s16.postimg.org/diov0drd1/level2_01.png" style="width: 543px; height: 281px;" />
<p> [ ;phpinfo();// ] means execute the operand, then execute the phpinfo and comment everything else. I intercepted the post request and added the payload to win the challenge. </p>
<img alt="" src="http://s2.postimg.org/mvccs3lc9/level_2_final.png" style="width: 500px; height: 459px;" />
<h2 class="section-heading"> Level 3: Data Validation</h2>
<p> The goal of this challenge was to create an admin account  by using some delimiters. The hints section will tell you that the delimiter needs to be used is new line. </p>
<img alt="" src="http://s11.postimg.org/lzivu06bn/Selection_048.png" style="width: 400px; height: 178px;" />
<p> I wasn't entirely sure how to change the role so I started making a couple of accounts and adding '\nrole:admin' after the test data. I used burp repeater to create accounts quickly and tried logging in to see if my roles were changed. </p>
<img alt="" src="http://s18.postimg.org/t786rtd15/Selection_049.png" style="width: 400px; height: 158px;" />
<img alt="" src="http://s1.postimg.org/scf8h4sz3/mew.png" style="width: 408px; height: 162px;" />
<h2 class="section-heading"> Level 4: Insecure Direct Object References</h2>
<p>This was an easy challenge about local file inclusion. The goal is to add a local URL to the file= parameter. I started by trying to add an URL which returned an error. The readme explains that the URL that needs to load is http://infosecinstitute.com/file.txt</p> 
<img alt="" src="http://s24.postimg.org/ye71m4ef9/Selection_050.png" style="width: 400px; height: 192px;" />
<p> It took me a while to understand that the application is doing some sort of validation and you can bypass this by adding 'HTTP' to the beginning of your URL. You will also need to add .php extension to your URL. The final payload was 'HTTP://infosecinstitute.com/file.txt.php'</p>
<img alt="" src="http://s28.postimg.org/74wg5ufq5/Selection_051.png" style="width: 400px; height: 75px;" />
<h2 class="section-heading">Level 5: Missing Function Level Access Control</h2>
<p>This was a confusing challenge. The user is presented with a page and the task is to somehow login. The first thing I looked for was a link or a hidden button to login. There is a hidden field which leads to a dead login page. </p>
<p><img alt="" src="http://s23.postimg.org/j2n2am917/levle5_new.png" style="width: 400px; height: 73px;" /></p>
<p>I didn’t fully understand the challenge and used to hints to help me. The hints explained that the objective of the challenge is to add an http refer header. So I refreshed the page and intercepted to request using Burp Suite and added 'Referrer: http://ctf.infosecinstitute.com/ctf2/exercises/ex5.php' to the request. </p>
<img alt="" src="http://s11.postimg.org/5p6iskx37/levle_5_qwert.png" style="width: 400px; height: 159px;" />
 <h2 class="section-heading"> Level 6: Cross Site Request Forgery</h2>
<p>Level 6 consisted of a basic CSRF challenge. The task was to create a CSRF payload to get a victim to transfer 555 on the site.com/bank.php. I started by searching the internet for CSRF examples and found a great example. I add the wanted parameters and created <img src=http://site.com/bank.php?transferTo=555/>. </p>
<img alt="" src="http://s24.postimg.org/kvnlm5zet/level6.png" style="width: 500px; height: 187px;" />
<p>Note: It took me a while to get the payload correct to complete the challenge.</p>
<h2 class="section-heading"> Level 7: A3 Cross-Site Scripting </h2>
<p>This is more of an HTML Injection than Cross-Site Scripting. The user needs to inject a h1 tag to win the challenge. I started by looking at the source code. There is a hidden field which reflects the URL on the page.</p>
<img alt="" src="http://s22.postimg.org/6iudxnnwh/level701.png" style="width: 500px; height: 147px;" />
<p>This means that I can try to html inject the page by adding the payload to the URL. I played around with the injection for a while and completed the challenge by adding &#39;/&#39;&gt;&lt;h1&gt;snoopyinjection&lt;/h1&gt;&#39; to the URL.</p>
<img alt="" src="http://s3.postimg.org/zbz654v8z/007final.png" style="width: 500px; height: 153px;" />
<h2 class="section-heading"> Level 8: File Inclusion </h2>
<p>The objective of level 8 was to take advantage of the image upload function on the page and execute a JS script with an alert. This was a very straightforward challenge. I started by creating a text file with '<script>alert('XSS')></script>' and saving it with the .html extension. If you try and upload a file with .html extension, you will get an error. This is because you need to add the proper extension in order to upload the file. </p>
<img alt="" src="http://s28.postimg.org/u6kr5vawt/level9_0004.png" style="width: 400px; height: 254px;" />
<p>To bypass this protection, you can intercept the request in a proxy and add the extension. Now if you forward the request, it would successfully upload. Now all you need to do is find the correct file include parameter and add the uploaded filename to it. This took me a while to figure out but the correct parameter is &quot;http://ctf.infosecinstitute.com/ctf2/exercises/ex8.php?file=yourimagename&quot;. This will give you the challenge completed page.</p>
<img alt="" src="http://s8.postimg.org/rfcx85r85/tlevel9success1.png" style="width: 425px; height: 246px;" />
<h2 class="section-heading"> Level 9: A2 Broken Authentication and Session Management </h2>
<p>Level 9 was easy. The user is presented with a page, authenticated as the user John Doe. To pass this challenge you need to change to user Mary Jane.</p>
<img alt="" src="http://s1.postimg.org/za0u5hw33/level9_11.png" style="width: 400px; height: 208px;" />
<p>To complete this challenge, you need to modify your cookie. The current value of the assigned cookie is&nbsp;&#39;Sk9ITitET0U=&#39; which is base64 encoded. This is equivalent to JOHN+DOE. To complete the challenge, change the cookie value to Mary Jane and Base64 encode it and use it to complete the challenge.</p>
<img alt="" src="http://s14.postimg.org/5dthd6wcx/levle9_cookie.png" style="width: 500px; height: 104px;" />
<img alt="" src="http://s4.postimg.org/60sbm3825/level9_ansert.png" style="width: 400px; height: 226px;" />
<h2 class="section-heading"> Level 10: Source Code Tampering </h2>
<p>This is was an interesting challenge. The goal of this challenge is to tamper the source code and change the win score to be 9999 and complete the game on extreme difficulty.</p>
<img alt="" src="http://s10.postimg.org/o0vzfkr6h/level10.png" style="width: 500px; height: 229px;" />
<p>I started this challenge by playing the game first and trying to understand what JavaScript files and functions are being called. The two interesting files I noticed were&nbsp;ex10.js and app.js files.</p>
<p>By looking at the ex10.js, the storageCompleted and extremeCompleted variable stood out. If the values of these functions are true, it will trigger the levelCompleted function.</p>
<img alt="" src="http://s24.postimg.org/8nqlnjtkl/level10_001.png" style="width: 300px; height: 193px;" />
<p>If you analyse app.js, you will notice the updateStats function which will set the storageCompleted variable to true. To complete this challenge, I copied the code from the app.js and modified the DOM to include it. So now when the game is played, the copied code will run instead of the app.js file.</p>
<img alt="" src="http://s1.postimg.org/qucql7cgf/level10_0002.png" style="width: 441px; height: 260px;" />
<p>Now you can edit parts of the code e.g. setting wins 99999 or points to 9999. This will set&nbsp;storageCompleted into true. To set the extremeCompleted into true, you will need to win the game in extreme difficulty. This can be done through cheating. If you inspect the DOM, you can see the colour of the objects.&nbsp;</p>
<img alt="" src="http://s30.postimg.org/v78qamttd/level10_000003.png" style="width: 400px; height: 307px;" />
<p>You can win the game is extreme difficulty by setting the all the objects to the same colour and selecting the appropriate colour.&nbsp;</p>
<img alt="" src="http://s11.postimg.org/48wnzib2r/newtscreen_shot_2015_06_25_at_5_40_30_pm.png" style="width: 450px; height: 188px;" />
<h2 class="section-heading"> Level 11: Bypassing blacklists </h2>
<p>This was quite an easy challenge to complete. The user is presented with a web page stating &#39;We do not want you around... You have been blacklisted.&#39;</p>
<img alt="" src="http://s9.postimg.org/yf2vjmn27/001.png" style="width: 507px; height: 300px; float: left;" />

<p>To solve this, all you need to do is intercept the HTTP request and responses in a proxy such as Burp Suite. The application sets a cookie called &#39;Welcome&#39; with the value &#39;no&#39;.</p>

<img alt="" src="http://s15.postimg.org/m4bphjf7f/002.png" style="width: 451px; height: 200px;" />
<p>The application state is dependent on the cookie value. If you modify the cookie to &#39;Yes&#39;, you will pass the challenge.</p>
<img alt="" src="http://s7.postimg.org/q00vmskpn/003.png" style="width: 332px; height: 200px; float: left;" />






<h2 class="section-heading"> Level 12: Dictionary Attack </h2>
<p>The goal of level 12 is to figure out the password of the admin user by brute forcing the application login page. The challenge page gives you a hint about the wordlist you should use by recommending the use of google dorking &#39;filetype: lst password&#39; &nbsp;</p>
<img alt="" src="http://s23.postimg.org/toemaigbv/004.png" style="width: 415px; height: 200px;" />
<p>When you use the filetype: operator, Google searches for files with that given filetype. If you do that search, the first result will be a common password list by openwall. The next step is to save the text file and use Burp intruder to brute force the login page.</p>
<p>Burp Intruder is a tool for automating customized attacks against web applications. It is extremely powerful and configurable, and can be used to perform a huge range of tasks, from simple brute-force guessing of web directories through to active exploitation of complex blind SQL injection vulnerabilities.</p>
<p>To start an intruder attack, you will need to intercept the login post request, then send in to intruder. Now you can highlight the parameter you want to enumerate and add payloads. Since only one parameter needs to be enumerated, you only need the pitchfork attack.</p>
<img alt="" src="http://s24.postimg.org/n5d3cz0sl/005.png" style="width: 544px; height: 350px;" />
<p>By going to the payload options, you can load a the wordlist you saved earlier through google dorks.</p>
<img alt="" src="http://s27.postimg.org/ri8p7fbkj/006.png" style="width: 695px; height: 250px;" />
<p>Now you can go to options and start an attack. If you wait a couple of minutes and look at the results, the only response with the different length is the password &#39;princess&#39;.</p>

<img alt="" src="http://s16.postimg.org/y902f5n39/007.png" style="width: 642px; height: 300px;" />
<p>You can type this this password with the username &#39;admin&#39; to log into the application and complete the challenge.</p>
<img alt="" src="http://s9.postimg.org/gx3478i0v/008.png" style="width: 456px; height: 300px;" />

<h2 class="section-heading"> Level 13: A10 Unvalidated Redirects and Forwards </h2>

<img alt="" src="http://s9.postimg.org/qk6mgyb0f/009.png" style="line-height: 100%; width: 375px; height: 250px;" />

<p>The final challenge is on Unvalidated redirects and forwards, Unvalided redirects are possible when a web application accepts untrusted input that could cause the web application to redirect the request to a URL contained within untrusted input. By modifying untrusted URL input to a malicious site, an attacker may successfully launch a phishing scam and steal user credentials.</p>

<p>To solve this challenge, I analysed the requests through Burp Suite and identified a GET request with a possible open redirect vulnerability.</p>

<img alt="" src="http://s22.postimg.org/ia55qemlt/010.png" style="width: 529px; height: 300px;" />
<p>The redirect parameter is vulnerable. If you try a URL like <a href="http://google.com/">http://google.com</a> or <a href="http://www.google.com/">www.google.com</a>, the redirect will fail and the result will be a bad parameter. To solve this challenge, you need to add a URL like the following :</font><font color="#212121">&#39;</font><font color="#212121">//google.com&#39;. </font><font color="#212121">This will succeed and you have successfully completed the challenge.</p>
<img alt="" src="http://s16.postimg.org/dvi4b8v8l/011.png" style="width: 500px; height: 157px;" />
<p> Thanks for reading my write-up. The challenge is still open so have a go! </p>