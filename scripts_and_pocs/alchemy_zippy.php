<?php

use Alchemy\Zippy\Zippy;

// Require Composer's autoloader
require __DIR__ . '/vendor/autoload.php';
$zippy = Zippy::load();
// Open an archive
$archive = $zippy->open('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip');

// Extract archive contents to `/tmp`
$archive->extract('/home/snoopy/zipslip/uploads');
