---
layout:     post
title:      "Content Provider Injection"
subtitle:   "A small introduction to Content Provider Injection using Drozer"
date:       2015-03-12-01 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/contact-bg.png"
---

<h3>Introduction</h3>

<p>In Android applications, content providers are used to supply data to an application’s queries. Content providers can be used to access an application’s own data saved within a SQL Lite database or somewhere in the system. Content providers can be easily identified by looking for values with the ‘content://’ URI schema. </p>


<img alt="" src="http://snoopysecurity.github.io/img/ssrf/contentp1.jpg" />
<p>The above illustration shows how different apps can access information through a content provider.</p>
<br>
<p>A Content provider of an application can centralize its contents in one location so many different applications access it as needed. In order to do this, an application will need to define its content provider in its manifest file. </p>

<blockquote>
&#x3C;provider
android:name=&#x22;com.test.example.DataProvider&#x22;
android:authorities =&#x22;com.test.example.DataProvider&#x22;&#x3E;
&#x3C;/provider&#x3E;
</blockquote>

<p> The above is an example of a content provider defined in the AndroidManifest.xml file. The AndroidManifest.xml file of an application can be viewed by decompiling the application using a tool such as apktool or Jadx.</p>

<h3>A working example</h3>

<p>Vulnerabilities can occur if the content provider of an application can be queried by other applications installed on the same system. This can lead to Content Provider Leakage, Traversal or Injection by exporting vulnerable content providers.
<br>
Exported content providers generally allow other applications on a device to request and share data. If sensitive information are accidentally leaked in one of these content providers, an attacker can query the vulnerable content provider to expose the sensitive data. 
<br>
To understand this flaw further, let’s analyse the Yahoo Weather application for Android. The Yahoo Weather application returns accurate weather forecasts based on a user's input and settings. This application uses a content provider to store all weather data which is exportable.
</p>
<img alt="" src="http://snoopysecurity.github.io/img/ssrf/contentp2.png" />

<p>To identify all content providers used by the application, it is better to review the source code and the android manifest file. This is because applications sometimes can use custom defined permissions to protect a content provider. This means that the specified content provider cannot be queried by a malicious android app without having the same custom permission.  So by having custom permissions, developers believe that only system applications or applications with the same signature can access these permissions. But, this is still considered a vulnerability because a malicious developer can copy and extract the custom permission from a target application and recompile the malware to have the same permission. This is accept by the android system as a legit request and can give malware access to applications with custom defined permissions.
<br>
It should also be noted the more permission you give a malicious application, the more data it can access through exploiting content providers. But, the android permission model dictates that each application should have its own UID and GID. This means that even if a malicious application has all permissions, it can only access exported activities, providers or receivers. 
<br>
To search for all possible content providers defined in a java source, you can use a recursive ‘grep’.
</p>

<img alt="" src="http://snoopysecurity.github.io/img/ssrf/contentp3.png" />

<p>The grep search will look at the entire content of the decompile code to find strings starting with the content URI schema.</p>

<h3>Technical Analysis</h3>

<p>To test the application for content provider leakage, it is best to fill the application with sample data and to better understand the attack surface. This can be done by adding different locations to the ‘Yahoo Weather Settings’ and setting a current location as any valid country.</p>

<img alt="" src="http://snoopysecurity.github.io/img/ssrf/contentp4.png" />

<p>In order to take the role of a malicious application to attack the yahoo app, we can use Drozer. Drozer is a security assessment framework that can be used to emulate an android app. It can be used to discover and interact with any attack surfaces exposed by a target Android application.
<br>
After your Drozer setup is complete, you can query the application for any content providers that are exportable by using the below command.
</p>

<blockquote>dz> run app.provider.finduri [packagename]</blockquote>

<img alt="" src="http://snoopysecurity.github.io/img/ssrf/contentp5.png" />

<p>In this example, the Drozer agent scanned the yahoo weather application and returned all exported content providers.  This is a useful function since only exported providers can be used by a malicious application.

Querying the <strong>content://com.yahoo.mobile.client.android.weather.provider.Weather/locations</strong> URI returns all weather forecast data stored by the application.  This is the data stored by the yahoo application depending on a user’s preference.
<br>
By looking at the returned data, it is possible for an attacker to identify the current location of a user.  This is because the 'isCurrentLocation' column has the value 1 or 0 depending on a user’s setting.  Furthermore, no permissions are needed for a malicious application to query the vulnerable content provider.
</p>

<img alt="" src="http://snoopysecurity.github.io/img/ssrf/contentp6.png" />

<p>The above illustration is an example of data that is accessible to a possible attacker. 

If Drozer is able to query and show the data from the content provider, it means that the content provider is leaking data. This is because Drozer has not been explicitly granted any permission to use or query the data.
</p>
<br>
<p>This is cause for concern as any 3rd party application containing malicious code does not require any granted permissions in order to obtain sensitive information from this application. Furthermore, it is possible to inject data into any of the fields of the content provider making in vulnerable to Injection. This is not considered a high risk due to the nature of the data but it should still be taken under consideration.
In many cases, Client SQL Injection is possible if a content provider is using a SQLite database to store data. To test for SQL Injection through drozer, a user can try to do the following:
</p>

<blockquote> run app.provider.query content://fulluri/ --selection "1=1"</blockquote>

<p>This will try to inject a logical tautology into the SQL statement being parsed by the content provider and eventually the database query parser.  If the query returns all rows in the database, it means the application is vulnerable to SQL Injection. This is because “1=1” is a true statement and it returns all rows in the database due to the statement being always true.</p>

<p>Furthermore, Drozer can be used to quickly check for injection or content provider leakage vulnerabilities in any application. This can be done by using the default scanner modules.
 <li>scanner.provider.finduris </li>
 <li>scanner.provider.injection</li>
</p>

<h3>Remediation</h3>

<p>To fix this vulnerability, the android manifest file of the application should be amended to add ‘android:exported = false ’. Furthermore, a developer can add permissions which must be requested by another application before accessing the provider.
<br>
The below screenshot is a snippet of the Yahoo weather client’s manifest file. The manifest file defines that the weather provider can be exported. The application should be recompiled and signed with that value set to false to avoid content provider leakage.

</p>

<img alt="" src="http://snoopysecurity.github.io/img/ssrf/contentp7.png" />
<p>To fix against possible any SQL Injection, any use of the function ‘SQLiteDatabase.rawQuery()’ should be avoided. Any use of raw queries should be replaced by parameterised statements. But, it should be noted that there is no way for a user to exploit this particular SQL injection without accessing the content provider directly. This is due to all values being inserted by accessing an API, rather than a user.</p>
