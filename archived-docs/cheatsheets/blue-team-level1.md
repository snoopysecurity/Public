*These notes will come handy in exam.*


Some great sources of free and open-source intelligence include:

* Spamhaus
* URLhaus
* AlienVault Open Threat Exchange
* Virus Share
* List of Free Threat Feeds
* Anomali Weekly Threat Briefing
* US Cybersecurity and Infrastructure Security Agency – Automated Indicator Sharing
* SANS Internet Storm Center
* Talos Intelligence – Free Version
* https://threatfox.abuse.ch/browse/




## SOC Fundamentals

List of common ports.

|Port|Service|Description|
|:---:|:---:|:---:|
|20,21|FTP|File Transfer Protocol used to transfer files b/w systems.|
|22|SSH|Secure Shell Protocol allows users to securely connect to a remote host.|
|23|Telnet|Used before SSH, allows users to connect to a remote host, doesn't offer encryption.|
|25|SMTP|Simple Mail Transfer Protocol used to send emails between servers within the network, or over the internet.|
|53|DNS|Domain Name System converts human-readable domain names to machine-readable IP address.|
|67,68|DHCP|Dynamic Host Configuration Protocol assign IP address-related information to any hosts on the network automatically.|
|80|HTTP|Hypertext Transfer Protocol allows browsers (Chrome, Firefox, etc) to connect to web servers and request contents.|
|443|HTTPS|Hypertext Transfer Protocol Secure is a secure version of HTTP Protocol which allows browsers to securely connect to web servers and request contents.|
|514|Syslog|Syslog server listens for incoming Syslog notifications, transported by UDP packets.|

## Phishing Analysis

##### Types of emails: 

###### Recon Emails

Recon emails are used to check if the destination mailbox is in use so that it can be targeted in future phishing attacks. Recon emails can vary in sophistication, there are three types we tend to see in the real world:

* Recon spam emails that contain nothing except random letters in the body text such as "adjdfkaweasda".
* Emails that use social-engineering techniques to try and get the recipient to respond.
* More complex emails use tracking pixels to see if the email has been viewed in an email client.

###### Credential Harvester

Below is a list of key points that often apply to credential harvester emails.

* Imitates commonly-used websites and services (such as Outlook, Amazon, HMRC, DHL, FedEx, and many more).
* Entices the recipient to enter credentials into a fake login portal.
* Uses social-engineering tactics including; creating a sense of urgency, and using false authority.
* URLs may be completely random or attempt to copy the legitimate domain name of the organization they are masquerading as.
* Often have small spelling or styling mistakes, something that is extremely rare with legitimate emails coming from big brands and organizations.

###### Social Engineering

Commonly used social engineering tactics in phishing emails include:

* Convincing the recipient to reply to an attacker's initial email (recon emails).
* Convincing the recipient to transfer money by posing as the CEO, CTO, CFO, or another employee on the executive board.
* Convincing the recipient to provide the attackers with information that is confidential or private by posing as the data subject or someone in a higher position within the company.


Other attacks
* Vishing and Smishing
* Whaling - Whaling is a highly-targeted phishing attack that looks to target individuals within management positions in an organization, often C-level executives, due to the wealth of information they have access to,
* and that stereotypically they are not highly educated around cybersecurity and phishing.


###### Spam Emails

Spam emails (also known as "junk mail") are messages that are unsolicited, unwanted, or unexpected but are not necessarily malicious in nature. Examples of spam emails are:

* Newsletters that the user has unknowingly signed up for
* Marketing emails trying to promote products and services
* Update announcements from companies and services the user has registered with


###### Malicious Attachments

Along with credential harvesters, emails that convince targets to open malicious files are the most common phishing email classifications. 
Malicious actors can get recipients to open malicious files, and what these can include. There are two main methods of delivering malware via phishing: 
* as an attachment,
* or as a hyperlink taking the target to a web server that is hosting malware available for download.

### Gathering IOCs

1. **Email Artifacts** :

- [ ] Sending Email Address
- [ ] Subject Line
- [ ] Recipient Email Addresses
- [ ] Sending Server IP & Reverse DNS
- [ ] Reply-To Address
- [ ] Date & Time

2. **Web Artifacts** :

- [ ] Full URLs
- [ ] Domain Names

3. **File Artifacts** :

- [ ] Attachment Name
- [ ] MD5, SHA1, SHA256 Hash Value

### Analyzing Artifacts

artifact collection - phish tool


1. **Visualization Tools** - [URL2PNG](https://www.url2png.com/), [URLScan](https://urlscan.io/), [AbuseIPDB](https://www.abuseipdb.com/)
2. **URL Reputation Tools** - [VirusTotal](https://www.virustotal.com/gui/), [URLScan](https://urlscan.io/), [URLhaus](https://urlhaus.abuse.ch/), [WannaBrowser](https://www.wannabrowser.net/)
3. **File Reputation Tools** - [VirusTotal](https://www.virustotal.com/gui/), [Talos File Reputation](https://www.talosintelligence.com/talos_file_reputation)
4. **Malware Sandboxing** - [Hybrid Analysis](https://www.hybrid-analysis.com/), [Any.run](https://any.run/), [VirusTotal](https://www.virustotal.com), [Joe Sandbox](https://www.joesandbox.com/)

## Digital Forensics

* FTK Imager - identify file systems from img
* KAPE: the Kroll Artifact Parser and Extractor - KAPE is an efficient and highly configurable triage program that will target essentially any device or storage location,
  find forensically useful artifacts, and parse them within a few minutes. 
* Windows File Analyzer -  Analyze the .LNK files in the Shortcuts folder using Windows File Analyzer
* PECMD - Analyze the Prefetch files using PECmd.exe
* JumpList Explorer. - analyse jumplists

three main tools, and approaching this from a live acquisition view, meaning that we are investigating a powered-on system that we have access to. We will be using:

* KAPE
* Browser History Viewer
* Browser History Capturer

1. Data Representation can be done in following ways,

- Base64
- Hexadecimal
- Octal
- ASCII
- Binary

2. File Carving :

retrieve deleted files using the Linux command-line tool scalpel

```bash
scalpel -b -o <output> <disk image file>
```

3. Hashes :

- **Windows** -

By default, `get-filehash` command will generate SHA256 sum of a file,

```powershell
get-filehash <file>
```

To generate MD5 hash of a file,

```powershell
get-filehash -algorithm MD5 <file>
```

To generate SHA1 hash of a file,

```powershell
get-filehash -algorithm SHA1 <file>
```

- **Linux** - 

```bash
md5sum <file>
sha1sum <file>
sha256sum <file>
```

4. Find digital evidence with 
	- **FTK Imager** - Import .img file in FTK imager
	- **KAPE** - Can be used for fast acquisition of data.

5. **Windows Investigations** :

- **LNK Files** - These files can be found at 

```md
C:\Users\$USER$\AppData\Roaming\Microsoft\Windows\Recent
```

- **Prefetch Files** - 
	- **PECmd** - This tool can be used to view the prefetch files. `PECmd.exe -f <path/to/file.pf>`

These files can be found at 
```md
C:\Windows\Prefetch
```

- **Jumplist Files** - These files can be found at

```md
C:\Users\% USERNAME%\AppData\ Roaming\Microsoft\Windows\Recent\AutomaticDestinations
C:\Users\%USERNAME%\AppData\ Roaming\Microsoft\Windows\Recent\CustomDestinations
```

- **Logon Events**
	- **ID 4624** - successful logons to the system.
	- **ID 4672** - Special Logon events where administrators logs in.
	- **ID 4625** - Failed Logon events.
	- **ID 4634** - Logoffs from the current session.

These event logs can be found at and viewed by EVENT VIEWER
```md
C:\Windows\System32\winevt\Logs
```

- Capture and view the browser history with 
	- **Browser History Viewer** 
	- **Browser History Capturer**

* Windows Registry Hives

```
    DEFAULT (mounted on HKEY_USERS\DEFAULT)
    SAM (mounted on HKEY_LOCAL_MACHINE\SAM)
    SECURITY (mounted on HKEY_LOCAL_MACHINE\Security)
    SOFTWARE (mounted on HKEY_LOCAL_MACHINE\Software)
    SYSTEM (mounted on HKEY_LOCAL_MACHINE\System)
```
Can be obtained using zimmerman tools and registry explorer

6. **Linux Investigations** :
	- **/etc/passwd** - contains all information about users in the system. 
	- **/etc/shadow** - contains encrypted passwords
	- **Unshadow** - used to combine the passwd and shadow files.
	- **/var/lib** - In `/var/lib/dpkg/status` location, this file includes a list of all installed software packages.
	- **.bash_history** - contains all the issued commands by the users.
	- **Hidden Files** - isuch files whose name begins with **.**
	- **Clear Files** - files that are accessible through standard means.
	- **Steganography** - practice of concealing messages or information within other non-secret text or data.


To collect and triage Recycle Bin artifacts, we're going to use the following tools:

* Command Prompt (CMD)
* RBCmd - GitHub - EricZimmerman/RBCmd: Recycle bin artifact parser
* CSVQuickViewer


7. **Volatility** - 

Find the imageinfo of the file, 

```bash
volatility -f /path/to/file.mem imageinfo
```

List the processes of a system,

```bash
volatility -f /path/to/file.mem --profile=PROFILE pslist
```

View the process listing in tree form,

```bash
volatility -f /path/to/file.mem --profile=PROFILE pstree
```

View command line of the specific process with PID XXXX,

```bash
volatility -f /path/to/file.mem --profile=PROFILE dlllist -p XXXX
```

View Network Connections,

```bash
volatility -f /path/to/file.mem --profile=PROFILE netscan
```

Dumping the process with a specific PID XXXX,

```bash
volatility -f /path/to/file.mem --profile=PROFILE procdump -p XXXX -D /home/ubuntu/Desktop
```

Print all available processes,

```bash
volatility -f memdump.mem --profile=PROFILE psscan
```

Print expected and hidden processes,

```bash
volatility -f memdump.mem --profile=PROFILE psxview
```

Create a timeline of events from the memory image,

```bash
volatility -f memdump.mem --profile=PROFILE timeliner
```

Pull internet browsing history,

```bash
volatility -f memdump.mem --profile=PROFILE iehistory
```

Identify any files on the system from the memory image,

```bash
volatility -f memdump.mem --profile=PROFILE filescan
```

```
Command Purpose	Volatility 2 Command	Volatility 3 Command
Get process tree	volatility --profile=PROFILE pstree -f file.dmp	python3 vol.py -f file.dmp windows.pstree
List services	volatility --profile=PROFILE svcscan -f file.dmp	python3 vol.py -f file.dmp windows.svcscan
List available registry hives	volatility --profile=Win7SP1x86_23418 -f file.dmp hivelist	python3 vol.py -f file.dmp windows.registry.hivelist
Print cmd commands	volatility --profile=PROFILE cmdline -f file.dmp	python3 vol.py -f file.dmp windows.cmdline
```

Volatility Workbench is a standalone graphical user interface (GUI) variant of Volatility 3.

8. **Metadata** - Data about data
	
- **Exiftool** 

```bash
exiftool <file>
```


Autopsy is a forensic-grade tool that is used by the military, law enforcement, and corporate examiners to investigate what happened on a smartphone or a computer. 
Autopsy has a plug-in architecture that allows the user to find add-on modules or even develop custom modules written in Java or Python, 
providing additional functionality and automation. This awesome tool comes built-in with Kali Linux, and can also be downloaded and used on systems running the Windows operating system 
for free.

```
    Multi-User Cases: Collaborate with your fellow examiners on large cases.
    Keyword Search: Text extraction and the index searched modules allow you to find the files which mention specific terms and find the regular expression patterns.
    Timeline Analysis: Displays system events in a graphical interface to help identify activity.
    Web Artifacts: Extracts web activity from common browsers to help identify user activity.
    LNK File Analysis: Identifies shortcuts and accessed documents.
    Email Analysis: Parses MBOX format messages, such as Thunderbird.
    Registry Analysis: Uses RegRipper to identify recently accessed documents and USB devices.
    EXIF: Extracts geolocation and camera information from JPEG files.
    File Type Sorting: Group files by their type to find all images or documents.
    Media Playback: View videos and images in the application and not require an external viewer.
    Thumbnail viewer: Displays thumbnail of images to help quick view pictures.
    Robust File System Analysis: Support for common file systems, including NTFS, FAT12/FAT16/FAT32/ExFAT, HFS+, ISO9660 (CD-ROM), Ext2/Ext3/Ext4, Yaffs2, and UFS from The Sleuth Kit.s.
    Tags: Tag files with arbitrary tag names, such as ‘bookmark’ or ‘suspicious’, and add comments.
    Unicode Strings Extraction: Extracts strings from unallocated space and unknown file types in many languages (Arabic, Chinese, Japanese, etc.).
    File Type Detection based on signatures and extension mismatch detection.
    Interesting Files Module will flag files and folders based on name and path.
    Android Support: Extracts data from SMS, call logs, contacts, Tango, Words with Friends, and more.
```

*  Recent Activity
* File Type Identification
* Embedded File Extractor
* Exif Parser
* Email Parser
* Encryption Detection



## Security Information and Event Management

“Windows Event logs” or “Event Logs” are files in binary format (with .evtx extension) stored locally in the Windows directory of a computer with that operating system:
```
    Windows 2000 to WinXP/Windows Server 2003:
    %WinDir%\system32\Config*.evt
    Windows Server 2008 to 2019, and Windows Vista to Win10:
    %WinDir%\system32\WinEVT\Logs*.evtx
```
 

These logs keep a detailed record of the vast majority of events that have occurred on the system (hardware events, user logins, program execution and installation, etc.), 
allowing system administrators to keep track of everything that happens within a system during its execution and being able to diagnose and foresee potential issues. Categories of registered events include:

```
    Application: Events logged by an application (Execution, Deployment error, etc.)
    System: Events logged by the Operating System (Device loading, startup errors, etc.)
    Security: Events that are relevant to the security of the system (Logins and logouts, file deletion, granting of administration permissions, etc.)
    Directory Service: This is a record available only to Domain Controllers, it stores Active Directory (AD) events.
    DNS Server: It is a record available only to DNS servers; logs of DNS service are stored.
    File Replication Service: Is a record available only for Domain Controllers, it stores Domain Controller Replication events.
```
 

If you are interested in learning more about these types of records, how they work and how to visualize them, visit the following links:
* https://www.manageengine.eu/network-monitoring/Eventlog_Tutorial_Part_I.html
* https://www.loggly.com/ultimate-guide/windows-logging-basics/#


Security Event Logs are events stored by the system that contain information related to the “Windows Security audit policies” (elements of systematic monitoring that helps with the evaluation of system security), which are used to allow precise control over any possible incident present in the system.
Some of these elements are:
```
    Account logon events (valid and invalid sign-ons and sign-offs)
    Account management (creation, modification, interaction and deletion of user accounts)
    Privilege use.
    Resource usage (file creation, modification, interaction and deletion)
```
 

If you want to learn more about the Windows Security Audit, it’s settings, and how to apply it, visit the following link: `https://docs.nxlog.co/integrate/windows-security-audit.html`

On Windows 10 we can view Windows Events using the Event Viewer. Search for it in the Windows search bar and run it.

We can use this program to view all different types of logs, and we highly recommend that students check it out to view the logs on their own systems. For this purposes of this walkthrough, we’re going to focus primarily on security-related events. When opening Event Viewer you should see a display similar to the below screenshot.

Sysmon is a Windows system service and device driver that, once installed on a system, remains resident across system reboots to monitor and log system activity to the Windows event log. It provides detailed information about process creations, network connections, and changes to file creation time. By collecting the events it generates using Windows Event Collection or SIEM agents and subsequently analyzing them. In this way, you can identify malicious or anomalous activity and understand how intruders and malware operate on your network.


### What is Sigma?


Sigma is a generic and open signature format that allows you to describe relevant log events in a straightforward manner. 
The rule format is very flexible, easy to write, and applicable to any type of log file.The main purpose of this project is to provide a structured form in which researchers or 
analysts can describe their detection methods and make them shareable with others.


### SPLUNK

Queries must start by referencing the dataset,

```md
index="botsv1"
```

To search for a source IP (src) address with a value of 127.0.0.1,

```md
index="botsv1" src="127.0.0.1"
```

To search for a destination IP (dst) address that this source IP address made a connection with a value of X.X.X.X,

```md
index="botsv1" src="127.0.0.1" dst="X.X.X.X"
```
The simplest search we can conduct is for a field and a value, for example, searching against our data for the source IP field (src) and the IP address value 10.10.10.50.

search src="10.10.10.50"

 

With the above query, we’re looking for any logs where the source IP is listed as 10.10.10.50. If we wanted to look for any logs or network traffic associated with this IP, we could also search for logs where the destination IP is stated as 10.10.10.50:

search src="10.10.10.50" OR dst="10.10.10.50"


Let’s go through a simple scenario together. The Customer Support team have received a number of complaints that the company website is extremely slow, and some customers aren’t able to access the site. The security team believes this may be a distributed denial-of-service attack, where multiple remote systems attempt to crash or use up all of the server’s resources so that legitimate clients can’t access it. Using the following simple query we could see what traffic is being directed towards the web server:

search dst="10.10.100.5"

 

While this would show us any logs where the destination IP is the web server, it will also show any other logs or traffic going to that server, which could result in a lot of logs that we are not interested in. We can apply additional arguments in our search query to perform actions such as filtering on HTTP traffic only.


Now that you know how we can find data within Splunk, we're going to cover Search Commands, and how they can help us better understand the data we've found in our search results. We'll cover the following commands:
```
    Sort
    Stats
    Table
    Uniq
    Dedup
```
 

## Incident Response

1. **Network Analysis** - use Wireshark to import .pcap, .pcapng files.

2. **CMD** : Command prompt can be used to view the valuable information,

To view the network configuration of the system,

```cmd
ipconfig /all
```

To check running processes and programs,

```cmd
tasklist
```

Display running processes and the associated binary file that was executed to create the process,

```cmd
wmic process get description, executablepath
```

To view all number of users in the command prompt

```cmd
net users
```

List all users that are in the administrators user group,

```cmd
net localgroup administrators
```

List all users in RDP group,

```cmd
net localgroup "Remote Desktop Users"
```

List all services and detailed information about each one,

```cmd
sc query | more
```

List open ports on a system, which could show the presence of a backdoor,

```cmd
netstat -ab
```

3. **Powershell** - Can also be used often retrieve much more information.

These commands will get network-related information from the system,

```powershell
Get-NetIPConfiguration
Get-NetIPAddress
```

List all local users on the system,

```powershell
Get-LocalUser
```

Provide a specific user to the command to only get information about them,

```powershell
Get-LocalUser -Name BTLO | select *
```

Quickly identify running services on the system in a nice separate window,

```powershell
Get-Service | Where Status -eq "Running" | Out-GridView
```

Group running processes by their priority value,

```powershell
Get-Process | Format-Table -View priority
```

Collect specific information from a service by including the name in the command (-Name ‘namehere’) or the Id, as shown above and below,

```powershell
Get-Process -Id 'idhere' | Select *
```

Scheduled Tasks are often abused and utilized a common persistence technique,

```powershell
Get-ScheduledTask
```

Specify the task, and retrieving all properties for it,

```powershell
Get-ScheduledTask -TaskName 'PutANameHere' | Select *
```

Changing the Execution Policy applied to our user,

```powershell
Set-ExecutionPolicy Bypass -Scope CurrentUser
```

4. **DeepBlueCLI** - PowerShell script that was created by SANS to aid with the investigation and triage of Windows Event logs.

To process log.evtx,

```powershell
./DeepBlue.ps1 log.evtx
```

DeepBlue will point at the local system's Security or System event logs directly,

```powershell
# Start the Powershell as Administrator and navigate into the DeepBlueCli tool directory, and run the script

./DeepBlue.ps1 -log security
./DeepBlue.ps1 -log system

# if the script is not running, then we need to bypass the execution policy
Set-ExecutionPolicy Bypass -Scope CurrentUser
```
Threathive -  TheHive is an open-source Security Incident Response Platform (SIRP) specifically designed to facilitate the management and investigation of cybersecurity events and incidents. This tool offers a centralized platform for managing and tracking tasks, cases, observables, and alerts.

You can find the GitHub repo for TheHive at the following link: https://github.com/TheHive-Project/TheHive


### Registry Forensics
```

Here's the updated and formatted version including the USB device forensics section:

System Info and Accounts

OS Version:

SOFTWARE\Microsoft\Windows NT\CurrentVersion
Current Control Set:

HKLM\SYSTEM\CurrentControlSet
SYSTEM\Select\Current
SYSTEM\Select\LastKnownGood
Computer Name:

SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName
Time Zone Information:

SYSTEM\CurrentControlSet\Control\TimeZoneInformation
Network Interfaces and Past Networks:

SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces
Autostart Programs (Autoruns):

NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Run
NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\RunOnce
SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce
SOFTWARE\Microsoft\Windows\CurrentVersion\policies\Explorer\Run
SOFTWARE\Microsoft\Windows\CurrentVersion\Run
SAM Hive and User Information:

SAM\Domains\Account\Users
Recent Files:

NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs
Office Recent Files:

NTUSER.DAT\Software\Microsoft\Office\VERSION
NTUSER.DAT\Software\Microsoft\Office\VERSION\UserMRU\LiveID_####\FileMRU
ShellBags:

USRCLASS.DAT\Local Settings\Software\Microsoft\Windows\Shell\Bags
USRCLASS.DAT\Local Settings\Software\Microsoft\Windows\Shell\BagMRU
NTUSER.DAT\Software\Microsoft\Windows\Shell\BagMRU
NTUSER.DAT\Software\Microsoft\Windows\Shell\Bags
Open/Save and LastVisited Dialog MRUs:

NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\OpenSavePIDlMRU
NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\LastVisitedPidlMRU
Windows Explorer Address/Search Bars:

NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths
NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery
File/Folder Usage or Knowledge

UserAssist:

NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist\{GUID}\Count
ShimCache:

SYSTEM\CurrentControlSet\Control\Session Manager\AppCompatCache
AmCache:

Amcache.hve\Root\File\{Volume GUID}\
BAM/DAM:

SYSTEM\CurrentControlSet\Services\bam\UserSettings\{SID}
SYSTEM\CurrentControlSet\Services\dam\UserSettings\{SID}
USB Device Forensics

Device Identification:

SYSTEM\CurrentControlSet\Enum\USBSTOR
SYSTEM\CurrentControlSet\Enum\USB
First/Last Times:

SYSTEM\CurrentControlSet\Enum\USBSTOR\Ven_Prod_Version\USBSerial#\Properties\{83da6326-97a6-4088-9453-a19231573b29}\####
0064 = First connection
0066 = Last connection
0067 = Last removal
USB Device Volume Name:

SOFTWARE\Microsoft\Windows Portable Devices\Devices
```

