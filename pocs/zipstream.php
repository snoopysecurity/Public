<?php

# Autoload the dependencies
require 'vendor/autoload.php';
# enable output of HTTP headers
use ZipStream\File;
use ZipStream\Option\Archive as ArchiveOptions;
use ZipStream\Option\File as FileOptions;
use ZipStream\Option\Method;
use ZipStream\ZipStream;

$zipArch = new \ZipArchive;;
$res = $zipArch->open('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip');
$zipArch->extractTo('/home/snoopy/zipslip/uploads');
$zipArch->close();