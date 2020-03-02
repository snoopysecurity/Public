<?php
require __DIR__ . '/vendor/autoload.php';
use Symfony\Component\Finder\Finder;
use Mmoreram\Extractor\Filesystem\TemporaryDirectory;
use Mmoreram\Extractor\Resolver\ExtensionResolver;
use Mmoreram\Extractor\Extractor;

$temporaryDirectory = new TemporaryDirectory();
$extensionResolver = new ExtensionResolver;
$extractor = new Extractor(
    $temporaryDirectory,
    $extensionResolver
);



/**
 * @var Finder $files
 */
$files = $extractor->extractFromFile('/home/snoopy/zipslip/payloads/zip-slip-vulnerability/archives/zip-slip.zip');
foreach ($files as $file) {
    echo $file->getRealpath() . PHP_EOL;
    echo $file;
}