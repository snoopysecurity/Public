

<?php
require __DIR__ . '/vendor/autoload.php';
use ZanySoft\Zip\Zip;


$zip = Zip::open('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip');
$zip->extract('/home/snoopy/zipslip/uploads');