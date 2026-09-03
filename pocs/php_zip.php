<?php
require __DIR__ . '/vendor/autoload.php';


$zipFile = new \PhpZip\ZipFile();


$zipFile->openFile('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip');
$zipFile->extractTo('/home/snoopy/zipslip/uploads');
$zipFile->close();