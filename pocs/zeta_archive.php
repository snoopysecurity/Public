<?php
require __DIR__ . '/vendor/autoload.php';

#require_once 'tutorial_autoload.php';
#use zetacomponents\archive\ezcArchive;
#require __DIR__ . '/vendor/zetacomponents/archive/src/zip/zip.php';
#require __DIR__ . '/vendor/zetacomponents/archive/src/archive.php';

date_default_timezone_set( "UTC" );
// Open the gzipped TAR archive.


$archive = ezcArchive::open( "/home/snoopy/zipslip/payloads/test3.zip");
$archive->extractCurrent( "/home/snoopy/zipslip/uploads" );

?>