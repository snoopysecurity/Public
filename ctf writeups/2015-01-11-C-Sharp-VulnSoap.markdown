---
layout:     post
title:      "Csharp - VulnSoap"
subtitle:   "A Vulnhub web application challenge"
date:       2015-01-11 12:00:00
author:     "Snoopy, the Security Dog"
header-img: "img/b_1.png"
---

<h2>Vulnhub Challenge: Csharp -VulnSoap</h2>
<p>VulnSoap is a purposefully vulnerable SOAP service with backend PostgreSQL database.  The application is written in the C# programming language and uses apache+mod_mono to run. The application is mainly focused on SQL injections but it’s still interesting.
I started by mapping with the application with Burp Suite and spidering to get access to all pages. Browsing to the web application directly will give the VulnerableService’s service page. 
The application also reveals its WSDL file which can be parsed to make requests to the client.  Looking at the methods and its input types can give you a good idea of what the application is processing. Using this service, it is possible to create a user, query his password and delete him. </p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/vulnsoap1.png"/>

<p>There are several publicity available tools that can be used to parse XML to create requests. This includes
<li>SoapUI</li>
<li>Wsdler Burp plugin</li>
<li>SOA Client firefox plugin</li>
I used SOA Client to parse the WSDL file and create requests. This can then be intercepted using Burp Suite and used in Intruder or repeater.</p>

<strong>Methods available:</strong>
<li>AddUser – Create a user. </li>
<li>ListUsers – List all users available in the database. </li>
<li>GetUser – Get a users password from the given username value. </li>
<li>DeleteUser – Delete a user</li>

<h2>Username Enumeration</h2>
<p>Since the webservice has a GetUser method publicly available, this can be used to enumerate through a list of users to find any users available on the web service. This can be done by using Burp Intruder.</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/vulnsoap2.png"/>


<h2>SQL Injection</h2>
<p>Since all methods are vulnerable to error based SQL Injection, let’s try and exploit one manually. The getuser method seems like a good choice since it is in a select statement.
<blockquote> select GetUserResult from vulnerableDB where username=’userinput’ </blockquote>
To identify a SQL Injection, you can try to input a single or a double quote to break the SQL syntax.</p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/vulnsoap3.png"/>

<p>To conduct more recon to understand the back-end database, you can use the union operator. The SQL UNION operator combines the result of two or more SELECT statements. Using this, an attacker can start select data from other tables.

<strong>foo' union select user,current_database()-- </strong><br>
This will give you the user the database is running as and the current database it is retrieving data from. In this case, the user is called ‘postgres ‘and the database is ’ vulnerable’.
To start extracting data from the database, you will first need to know all available tables and columns. This can be found by querying the database’s information_schema. A database’s information schema provides information about all of the tables, views, columns, and procedures in a database.
<strong>snoopy' union select COLUMN_name,table_name from information_schema.columns--</strong>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/vulnsoap4.png"/>


Now you can start looking for interesting table_name by using the where clause. 
<strong>snoopy' union select COLUMN_name,table_name from information_schema.columns where table_name!='routines’--  </strong>
This technique can be used multiple times to add column names you already retrieved.
<strong>where table_name='users' and column_name!='password'  AND column_name!='confrelid'-- </strong>
Using this SQL statement, it was possible to enumerate through different records and find a table called users.
<strong>snoopy' union select username,password from users-- </strong></p>

<img alt="" src="http://snoopythesecuritydog.github.io/img/ssrf/vulnsoap5.png"/>

<p>SQL Injection Wiki: <a href="http://www.sqlinjectionwiki.com/Categories/4/postgresql-sql-injection-cheat-sheet/">Link</a></p>
<h2>Automating with SQLmap</h2>
<p>The exploitation of this vulnerability can be automated using Sqlmap. Sqlmap is an open source pentesting tool that automates the process of detecting and exploiting SQL injection flaws and taking over of database servers. It comes with a powerful detection engine, many niche features for the ultimate penetration tester and a broad range of switches lasting from database fingerprinting, over data fetching from the database, to accessing the underlying file system and executing commands on the operating system via out-of-band connections (source: sqlmap.org). It is written in python.
To exploit this vulnerability using Sqlmap, first take the raw request and save it in a text file. Now, try the following Sqlmap command.
<blockquote>sqlmap -r savedrequest.txt -p username --dbms=PostgreSQL  --dump</blockquote>

<li>--dbs - To get all available database</li>
<li>-D - database name </li>
<li>-T - table name</li>
<li>--tables  - To get all tables in a database</li>
<li>--columns  -  to get all columns</li>
<li>--technique=U uses union technique</li>
</p>
