import { readdirSync } from 'fs';
import { join, basename } from 'path';

export default async (request) => {
  const url = new URL(request.url);
  const job = url.searchParams.get('job');

  if (!job) {
    return new Response(JSON.stringify({ error: 'Missing ?job= query parameter' }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Sanitize the job stem to prevent path traversal
  const safeName = basename(job).replace(/[^a-zA-Z0-9_\-]/g, '_');

  // In Netlify serverless, we can't access local files directly.
  // Instead, fetch PDFs from the public CDN URL.
  const siteUrl = `https://${url.hostname}`;

  // Find matching files by listing the applications directory via CDN
  // We'll try common patterns for resume and cover letter PDFs
  const possibleResumeNames = [
    `${safeName}_resume.pdf`,
    // Also try with date prefix variations
  ];
  const possibleCoverNames = [
    `${safeName}_cover_letter.pdf`,
  ];

  async function fetchPdf(filename) {
    const pdfUrl = `${siteUrl}/applications/${filename}`;
    try {
      const resp = await fetch(pdfUrl);
      if (resp.ok) {
        const arrayBuffer = await resp.arrayBuffer();
        return Buffer.from(arrayBuffer);
      }
    } catch (e) {
      // File not found, continue
    }
    return null;
  }

  // Try to fetch resume and cover letter
  let resumeData = null;
  let coverData = null;
  let resumeName = null;
  let coverName = null;

  for (const name of possibleResumeNames) {
    resumeData = await fetchPdf(name);
    if (resumeData) {
      resumeName = name;
      break;
    }
  }

  for (const name of possibleCoverNames) {
    coverData = await fetchPdf(name);
    if (coverData) {
      coverName = name;
      break;
    }
  }

  if (!resumeData && !coverData) {
    return new Response(JSON.stringify({ error: `No documents found for job stem: ${safeName}` }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  // Build a ZIP file in memory
  const files = [];
  if (resumeData) files.push({ name: resumeName, data: resumeData });
  if (coverData) files.push({ name: coverName, data: coverData });

  // Simple ZIP construction (no external dependencies needed)
  const zipParts = [];
  const localHeaders = [];
  let offset = 0;

  for (const file of files) {
    const data = file.data;
    const nameBytes = new TextEncoder().encode(file.name);

    // Local file header
    const header = new ArrayBuffer(30 + nameBytes.length);
    const hv = new DataView(header);
    hv.setUint32(0, 0x04034b50, true);  // Local file header signature
    hv.setUint16(4, 20, true);           // Version needed
    hv.setUint16(6, 0, true);            // Flags
    hv.setUint16(8, 0, true);            // Compression: stored
    hv.setUint16(10, 0, true);           // Mod time
    hv.setUint16(12, 0, true);           // Mod date
    hv.setUint32(14, crc32(data), true); // CRC-32
    hv.setUint32(18, data.length, true); // Compressed size
    hv.setUint32(22, data.length, true); // Uncompressed size
    hv.setUint16(26, nameBytes.length, true); // Filename length
    hv.setUint16(28, 0, true);           // Extra field length
    new Uint8Array(header).set(nameBytes, 30);

    localHeaders.push({ name: file.name, offset, size: data.length, crc: crc32(data) });
    zipParts.push(Buffer.from(header), Buffer.from(data));
    offset += header.byteLength + data.length;
  }

  // Central directory
  const centralStart = offset;
  for (const h of localHeaders) {
    const nameBytes = new TextEncoder().encode(h.name);
    const entry = new ArrayBuffer(46 + nameBytes.length);
    const ev = new DataView(entry);
    ev.setUint32(0, 0x02014b50, true);  // Central directory signature
    ev.setUint16(4, 20, true);           // Version made by
    ev.setUint16(6, 20, true);           // Version needed
    ev.setUint16(8, 0, true);            // Flags
    ev.setUint16(10, 0, true);           // Compression
    ev.setUint16(12, 0, true);           // Mod time
    ev.setUint16(14, 0, true);           // Mod date
    ev.setUint32(16, h.crc, true);       // CRC-32
    ev.setUint32(20, h.size, true);      // Compressed size
    ev.setUint32(24, h.size, true);      // Uncompressed size
    ev.setUint16(28, nameBytes.length, true); // Filename length
    ev.setUint16(30, 0, true);           // Extra field length
    ev.setUint16(32, 0, true);           // File comment length
    ev.setUint16(34, 0, true);           // Disk number start
    ev.setUint16(36, 0, true);           // Internal file attributes
    ev.setUint32(38, 0, true);           // External file attributes
    ev.setUint32(42, h.offset, true);    // Relative offset of local header
    new Uint8Array(entry).set(nameBytes, 46);
    zipParts.push(Buffer.from(entry));
    offset += entry.byteLength;
  }

  // End of central directory
  const centralSize = offset - centralStart;
  const eocd = new ArrayBuffer(22);
  const ev = new DataView(eocd);
  ev.setUint32(0, 0x06054b50, true);  // End of central directory signature
  ev.setUint16(4, 0, true);           // Disk number
  ev.setUint16(6, 0, true);           // Disk with central directory
  ev.setUint16(8, localHeaders.length, true); // Entries on this disk
  ev.setUint16(10, localHeaders.length, true); // Total entries
  ev.setUint32(12, centralSize, true); // Size of central directory
  ev.setUint32(16, centralStart, true); // Offset of central directory
  ev.setUint16(20, 0, true);          // Comment length
  zipParts.push(Buffer.from(eocd));

  const zipBuffer = Buffer.concat(zipParts);

  return new Response(zipBuffer, {
    status: 200,
    headers: {
      'Content-Type': 'application/zip',
      'Content-Disposition': `attachment; filename="${safeName}_application_pack.zip"`,
      'Content-Length': String(zipBuffer.length),
    },
  });
};

// CRC-32 lookup table
const crcTable = new Uint32Array(256);
for (let i = 0; i < 256; i++) {
  let c = i;
  for (let j = 0; j < 8; j++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
  crcTable[i] = c;
}

function crc32(buf) {
  let crc = 0xFFFFFFFF;
  for (let i = 0; i < buf.length; i++) crc = crcTable[(crc ^ buf[i]) & 0xFF] ^ (crc >>> 8);
  return (crc ^ 0xFFFFFFFF) >>> 0;
}
