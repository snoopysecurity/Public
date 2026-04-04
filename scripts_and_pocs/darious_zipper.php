<?php
require __DIR__ . '/vendor/autoload.php';
$zipper = new \DariusIII\Zipper\Zipper;

$zipper->make('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip')->extractTo('/home/snoopy/zipslip/uploads');
$zipper->close();