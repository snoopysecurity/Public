<?php
require __DIR__ . '/vendor/autoload.php';
#use Chamilo\PclZip;

$zip = new PclZip('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip');
$zip->extract(PCLZIP_OPT_PATH, '/home/snoopy/zipslip/uploads');