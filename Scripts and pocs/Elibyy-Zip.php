<?php
require 'vendor/autoload.php';

use Elibyy\Reader;
use Elibyy\Creator;


$reader = new Reader('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip');
$reader->unzip('/home/snoopy/zipslip/uploads');


//https://mega.nz/#F!Qo9hgASA!HaOtbRwm18QhgApGfu6tqQ