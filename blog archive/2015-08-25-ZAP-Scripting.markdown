---
layout:     post
title:      "ZAP Scripting"
subtitle:   "Useful for developers, functional testers and pentesters"
date:       2015-08-25 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/zapcover.png"
---

<p>Zed Attack Proxy (ZAP) is an open-source web application security scanner/proxy that can be used to find vulnerabilities. This blog post is about Zed Attack Proxy’s Scripting capabilities and how it can be very useful. </p>

<p>ZAP’s scripting feature allows a user to create a script in JavaScript or Zest to further improve ZAP Scanner capabilities.  A user can write numerous scripts to work with ZAP’s active scanning, passive scanning, proxy and more.  ZAP supports JavaScript and Zest scripts, but it also supports Jython and JRuby via the ZAP Marketplace.</p>

<img alt="" src="http://snoopysecurity.github.io/img/pic-11.png" style="width: 1689px; height: 367px;" />

<p>I don’t use ZAP a lot but I like the scripting feature due to how quick and easy it is. This can be useful if a user runs into a specific problem during a web application test and needs a quick fix through scripting. E.g. If a user wants the ZAP passive scanner to analyze and report all Base64 encoded data. This can be done by writing a ZAP script and enabling it on the script console.</p>

<p>Lastly, here is a repo of ZAP Scripts written by the community. I’ve written a couple as part of the ZAP Community Scripts Competition.</p>
<p>ZAP Community Scripts Repo: <a href="https://github.com/zaproxy/community-scripts">Community Scripts</a></p>
<p>ZAP Development Wiki: <a href="https://github.com/zaproxy/zaproxy/wiki/Development">ZAP Development</a></p>
