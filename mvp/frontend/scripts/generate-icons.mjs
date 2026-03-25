/**
 * Generate PWA icons from the SVG source.
 *
 * Usage:
 *   node scripts/generate-icons.mjs
 *
 * Requires: sharp (npm install --save-dev sharp)
 * If sharp is not available, the script creates minimal valid PNG placeholders
 * so the manifest always resolves, and you can regenerate proper icons later.
 */

import { writeFileSync, readFileSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ICONS_DIR = join(__dirname, '..', 'public', 'icons');
const SVG_PATH = join(ICONS_DIR, 'icon.svg');

const SIZES = [72, 96, 128, 144, 152, 192, 384, 512];

/**
 * Create a minimal valid 1x1 PNG buffer and scale description.
 * This is a valid PNG that browsers will accept as a placeholder.
 */
function createMinimalPng() {
  // Minimal valid PNG: 1x1 blue pixel
  // PNG signature + IHDR + IDAT + IEND
  return Buffer.from([
    0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, // PNG signature
    0x00, 0x00, 0x00, 0x0d, 0x49, 0x48, 0x44, 0x52, // IHDR chunk
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, // 1x1
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53, // 8-bit RGB
    0xde, 0x00, 0x00, 0x00, 0x0c, 0x49, 0x44, 0x41, // IDAT chunk
    0x54, 0x08, 0xd7, 0x63, 0xa8, 0xa6, 0x64, 0x00, // compressed blue pixel
    0x00, 0x00, 0x06, 0x00, 0x03, 0x7e, 0x8f, 0xb1, //
    0x47, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4e, // IEND chunk
    0x44, 0xae, 0x42, 0x60, 0x82,
  ]);
}

async function generateWithSharp() {
  const sharp = (await import('sharp')).default;
  const svgBuffer = readFileSync(SVG_PATH);

  for (const size of SIZES) {
    const outputPath = join(ICONS_DIR, `icon-${size}x${size}.png`);
    await sharp(svgBuffer)
      .resize(size, size)
      .png()
      .toFile(outputPath);
    console.log(`  Generated: icon-${size}x${size}.png`);
  }
}

function generatePlaceholders() {
  const placeholderPng = createMinimalPng();

  for (const size of SIZES) {
    const outputPath = join(ICONS_DIR, `icon-${size}x${size}.png`);
    if (!existsSync(outputPath)) {
      writeFileSync(outputPath, placeholderPng);
      console.log(`  Placeholder: icon-${size}x${size}.png (replace with proper icon later)`);
    } else {
      console.log(`  Exists: icon-${size}x${size}.png (skipped)`);
    }
  }
}

async function main() {
  console.log('Generating PWA icons...\n');

  try {
    await generateWithSharp();
    console.log('\nAll icons generated with sharp from SVG source.');
  } catch {
    console.log('sharp not available, creating placeholder PNGs...\n');
    generatePlaceholders();
    console.log('\nPlaceholder icons created. Install sharp and re-run for proper icons:');
    console.log('  npm install --save-dev sharp');
    console.log('  node scripts/generate-icons.mjs');
  }
}

main();
