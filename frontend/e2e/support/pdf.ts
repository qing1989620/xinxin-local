export function syntheticPdf(pages = 2) {
  const text =
    "Learning example: the derivative of x squared is twice x. Compute the derivative at x=3 and explain the tangent slope. ";
  const stream = `BT /F1 12 Tf 25 740 Td (${text}) Tj 0 -30 Td (${text}) Tj ET`;
  const fontId = 3 + pages * 2;
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    `<< /Type /Pages /Kids [${Array.from({ length: pages }, (_, index) => `${3 + index * 2} 0 R`).join(" ")}] /Count ${pages} >>`,
  ];
  for (let index = 0; index < pages; index++)
    objects.push(
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 800] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${4 + index * 2} 0 R >>`,
      `<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}\nendstream`,
    );
  objects.push("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
  let content = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets.push(Buffer.byteLength(content));
    content += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });
  const xref = Buffer.byteLength(content);
  content += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  content += offsets
    .slice(1)
    .map((offset) => `${String(offset).padStart(10, "0")} 00000 n \n`)
    .join("");
  content += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(content);
}
