<?php
require __DIR__ . '/vendor/autoload.php';
require __DIR__ .'/vendor/codeless/ziparchiveex/src/ZipArchiveEx.php';
#use codeless\ziparchiveex\ZipArchiveEx;
# ZipArchive as usual:
$zip = new ZipArchiveEx();
$zip->open('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/testzip-slip.zip', ZIPARCHIVE::OVERWRITE);
$zip->addDir('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/uploads');
echo $zip;
# Add whole directory including contents:


# Only add the contents of the directory, but
# not the directory-entry of "mydir" itself:

# Close archive (as usual):
$zip->close();