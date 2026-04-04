<?php
require 'vendor/autoload.php';

$zipper = new \Madnest\Madzipper\Madzipper;

$zipper->make('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip')->extractTo('/home/snoopy/zipslip/uploads');
$zipper->close();