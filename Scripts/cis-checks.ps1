function enumeration
{
  # List OS Version
  systeminfo | findstr /B /C:"OS Name" /C:"OS Version"  
  # Hostname of the System
  hostname  
  # List all services
  Get-WmiObject -Class win32_service
  # List all users
  net users
  # Available Network Interfaces and route
  ipconfig /all
  route print
  arp -A
  # Active network connections
  netstat -ano
  netsh firewall show state
  netsh firewall show config
  # Show all scheduled tasks
  schtasks /query /fo LIST /v
  # Show services and process IDs
  tasklist /SVC
  netstart
  # Show 3rd Party Drivers
  DRIVERQUERY
}

function patches
{
  get-hotfix | select Caption,Description,HotFixID,InstalledOn
  
}

function cis-checks
{

"----------------------------------------"
"Password Policy checks, "
"----------------------------------------"
"net accounts"
net accounts
"REG QUERY HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\policies\Network" 
REG QUERY HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\policies\Network 
"REG QUERY HKLM\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters"
REG QUERY HKLM\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters 
"Passwords Should Be Stored Securely"
"REG QUERY HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Lsa\LmCompatibilityLevel"
REG QUERY HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Lsa\LmCompatibilityLevel
"Checking if Account Lockout Registry is set"
"REG QUERY HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\RemoteAccess\Parameters\AccountLockout"
REG QUERY HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\RemoteAccess\Parameters\AccountLockout

"----------------------------------------"
"Account auditing"
"----------------------------------------"
"User Logons and Logoffs Audited"
auditpol /get /subcategory:"Logoff"
auditpol /get /subcategory:"Logon"
"Appropiate Events Audited"
auditpol /get /category:*
"Failsafe if Security Events Unable To Be Audited"
reg query HKLM\System\CurrentControlSet\Control\Lsa /v crashonauditfail



"----------------------------------------"
"System Logging"
"----------------------------------------"

"Checking if EventLog is configured...but check GPO First"
HKLM\Software\Policies\Microsoft\Windows\EventLog\Application\MaxSize
HKLM\Software\Policies\Microsoft\Windows\EventLog\Security\MaxSize
HKLM\Software\Policies\Microsoft\Windows\EventLog\System\MaxSize


"Checking if locally configured value is used"
REG QUERY HKLM\SYSTEM\CurrentControlSet\services\eventlog\Application\MaxSize


"These policy settings are backed up by the following registry values:"
REG QUERY HKLM\Software\Policies\Microsoft\Windows\EventLog\Application\Retention
REG QUERY HKLM\Software\Policies\Microsoft\Windows\EventLog\Security\Retention
REG QUERY HKLM\Software\Policies\Microsoft\Windows\EventLog\System\Retention

"If there is no group policy then the following registry values take precedence"
REG QUERY HKLM\SYSTEM\CurrentControlSet\services\eventlog\Security\Retention
REG QUERY HKLM\SYSTEM\CurrentControlSet\services\eventlog\System\Retention
REG QUERY HKLM\SYSTEM\CurrentControlSet\services\eventlog\Application\Retention



"----------------------------------------"
"Firewall State"

"----------------------------------------"
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\DomainProfile /v EnableFirewall
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PrivateProfile /v EnableFirewall
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PublicProfile /v EnableFirewall
netsh advfirewall show allprofiles


"Firewall Notifications: They should all be 0, meaning notifications are enabled."
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\DomainProfile /v DisableNotifications
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PrivateProfile /v DisableNotifications
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PublicProfile /v DisableNotifications

"Windows Server 2012: These settings control whether local administrators are allowed to create connection security rules that apply together with connection security rules configured by Group Policy."

reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PublicProfile /v AllowLocalIPsecPolicyMerge
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PrivateProfile /v AllowLocalIPsecPolicyMerge
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\DomainProfile /v AllowLocalIPsecPolicyMerge

"These determine whether locally set firewall rules will be permitted. Otherwise, only those that are set by Group Policy will be permitted."

reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PublicProfile /v AllowLocalPolicyMerge
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PrivateProfile /v AllowLocalPolicyMerge
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\DomainProfile /v AllowLocalPolicyMerge

"Firewall Rules: review manually"
netsh advfirewall firewall show rule name=all
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PublicProfile /v DefaultOutboundAction
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PrivateProfile /v DefaultOutboundAction
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\DomainProfile /v DefaultOutboundAction

"Inbound Connections"
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PublicProfile /v DefaultInboundAction
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\PrivateProfile /v DefaultInboundAction
reg query HKLM\Software\Policies\Microsoft\WindowsFirewall\DomainProfile /v DefaultInboundAction









"----------------------------------------"
"Screensaver Security, Default is not found"

"----------------------------------------"



"Interactive logon: Machine inactivity limit. Default is disabled"
REG QUERY HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System /v InactivityTimeoutSecs


"Checking screensaver, probs not configued"
REG QUERY HKCU\Software\Policies\Microsoft\Windows\Control Panel\Desktop\ScreenSaveActive


"See if screensaver executable is present"
REG QUERY HKCU\Software\Policies\Microsoft\Windows\Control Panel\Desktop\SCRNSAVE.EXE 
"Screensaver timeout"
REG QUERY HKCU\Software\Policies\Microsoft\Windows\Control Panel\Desktop\ScreenSaveTimeOut 

"Password protect the screen saver"
REG QUERY HKCU\Software\Policies\Microsoft\Windows\Control Panel\Desktop\ScreenSaverIsSecure 


"RDP Security"
"Check if password security is disabled"
REG QUERY "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\DisablePasswordSaving"
REG QUERY "HKLM\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services\fPromptForPassword"


"----------------------------------------"
"Remote Desktop Encryption"
"----------------------------------------"

REG QUERY "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" /v MinEncryptionLevel
REG QUERY "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" /v SecurityLayer

"----------------------------------------"
"UAC"
"----------------------------------------"
reg query HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System /v FilterAdministratorToken
reg query HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System /v ConsentPromptBehaviorAdmin

"----------------------------------------"
"wsus"
"----------------------------------------"
reg query HKLM\Software\Policies\Microsoft\Windows\WindowsUpdate\ /v WUServer




"----------------------------------------"
"Insecure Interactive Logon Settings"

"----------------------------------------"
reg query HKLM\SYSTEM\CurrentControlSet\Control\Lsa /v crashonauditfail
reg query "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" /v ForceUnlockLogon
reg query "HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon" /v CachedLogonsCount
reg query HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System\ /v LegalNoticeText
reg query HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System\ /v LegalNoticeCaption


"----------------------------------------"
"Insecure Network Access Controls And Configuration"
"----------------------------------------"
reg query HKLM\System\CurrentControlSet\Control\Lsa /v RestrictAnonymous
reg query HKLM\System\CurrentControlSet\Control\Lsa /v DisableDomainCreds
reg query HKLM\System\CurrentControlSet\Control\Lsa\MSV1_0 /v NtlmMinClientSec
reg query HKLM\System\CurrentControlSet\Control\Lsa\MSV1_0 /v NtlmMinServerSec


"----------------------------------------"
"Insecure Startup Settings, Registry should not be set"
"----------------------------------------"

reg query HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer /v DisableLocalMachineRun
reg query HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer /v DisableLocalMachineRunOnce


"----------------------------------------"
"Insecure SMB Settings"
"----------------------------------------"
reg query HKLM\System\CurrentControlSet\Services\LanmanWorkstation\Parameters /v RequireSecuritySignature
reg query HKLM\System\CurrentControlSet\Services\LanmanServer\Parameters /v EnableSecuritySignature
reg query HKLM\System\CurrentControlSet\Services\LanmanServer\Parameters /v RequireSecuritySignature








"----------------------------------------"
"Checking for Null Sessions"
"----------------------------------------"
REG QUERY HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters /v restrictnullsessaccess


}
