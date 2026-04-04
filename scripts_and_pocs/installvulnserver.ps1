# install vulnserver
$down = New-Object System.Net.WebClient
$url  = 'https://github.com/stephenbradshaw/vulnserver/raw/master/vulnserver.exe';
$url2  = 'https://github.com/stephenbradshaw/vulnserver/raw/master/essfunc.dll';
$file = 'vulnserver.exe';
$file2 = 'essfunc.dll';
$down.DownloadFile($url,$file);
$down.DownloadFile($url2,$file2);
$exec = New-Object -com shell.application
$exec.shellexecute($file);
