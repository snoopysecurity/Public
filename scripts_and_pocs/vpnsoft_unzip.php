
<?php
require __DIR__ . '/vendor/autoload.php';
use VIPSoft\Unzip\Unzip;


$unzipper  = new Unzip();
$filenames = $unzipper->extract('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip', '/home/snoopy/zipslip/uploads');