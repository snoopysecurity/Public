<?php
require __DIR__ . '/vendor/autoload.php';
use splitbrain\PHPArchive\Zip;

$tar = new Zip();
$tar->open('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip');
$tar->extract('/home/snoopy/zipslip/uploads');