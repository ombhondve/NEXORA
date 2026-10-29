const fs = require('fs');
const path = require('path');
const { PDFDocument, StandardFonts, rgb } = require('pdf-lib');

async function createFixtures() {
  const fixturesDir = path.resolve(__dirname, '../fixtures');
  if (!fs.existsSync(fixturesDir)) {
    fs.mkdirSync(fixturesDir, { recursive: true });
  }

  // 1. Short text PDF
  {
    const doc = await PDFDocument.create();
    const font = await doc.embedFont(StandardFonts.Helvetica);
    const page = doc.addPage([600, 400]);
    page.drawText(
      'MEMORANDUM OF UNDERSTANDING\n\n' +
      'Date: October 12, 2024\n' +
      'Parties: Fictional Dynamics Inc. ("Buyer") and Sample Logistics Corp. ("Provider")\n\n' +
      '1. Scope of Services: Provider agrees to maintain automated backup systems for Buyer.\n' +
      '2. Consideration: Buyer shall pay a fixed fee of $45,000 upon delivery.\n' +
      '3. Confidentiality: Both parties shall preserve confidentiality for three (3) years.\n',
      { x: 50, y: 350, size: 11, font, lineHeight: 15 }
    );
    const bytes = await doc.save();
    fs.writeFileSync(path.join(fixturesDir, 'short_text.pdf'), bytes);
    console.log('Created short_text.pdf');
  }

  // 2. Contradictory statements PDF
  {
    const doc = await PDFDocument.create();
    const font = await doc.embedFont(StandardFonts.Helvetica);

    const page1 = doc.addPage([600, 450]);
    page1.drawText(
      'COMMERCIAL LEASE AGREEMENT\n\n' +
      'Page 1:\n' +
      'This lease is executed on January 15, 2024 by Landlord Alpha Real Estate LLC and Tenant Beta Innovations Corp.\n' +
      'Section 2.1: The Commencement Date shall be March 1, 2024.\n' +
      'Section 3.1: The Base Monthly Rent is agreed at $12,500 payable on the first day of each month.\n' +
      'Section 4.1: Security deposit of $25,000 was received in full on January 10, 2024.\n',
      { x: 50, y: 380, size: 11, font, lineHeight: 16 }
    );

    const page2 = doc.addPage([600, 450]);
    page2.drawText(
      'Page 2:\n' +
      'Section 6.4: Alterations and Tenant Improvements.\n' +
      'Tenant shall receive an improvement allowance of $60,000 from Landlord prior to occupancy.\n' +
      'Section 7.2: Landlord warranty states that HVAC systems are brand new and installed in December 2023.\n',
      { x: 50, y: 380, size: 11, font, lineHeight: 16 }
    );

    const page3 = doc.addPage([600, 450]);
    page3.drawText(
      'Page 3:\n' +
      'Section 11.1: Default & Late Penalties.\n' +
      'Late fee of 10% applies if the monthly rent of $15,000 is not received by the 5th.\n' +
      'Section 12.3: Security Deposit Status.\n' +
      'Tenant acknowledges that the security deposit of $25,000 remains unpaid as of the date hereof.\n' +
      'Section 14.1: The Commencement Date is mutually amended to April 1, 2024.\n',
      { x: 50, y: 380, size: 11, font, lineHeight: 16 }
    );

    const bytes = await doc.save();
    fs.writeFileSync(path.join(fixturesDir, 'contradictory_statements.pdf'), bytes);
    console.log('Created contradictory_statements.pdf');
  }

  // 3. Multi-page deposition
  {
    const doc = await PDFDocument.create();
    const font = await doc.embedFont(StandardFonts.Helvetica);

    for (let i = 1; i <= 5; i++) {
      const page = doc.addPage([600, 450]);
      page.drawText(
        `DEPOSITION OF WITNESS ARTHUR PENDLETON - PAGE ${i}\n\n` +
        `Q: Mr. Pendleton, where were you on the evening of August 14, 2023?\n` +
        `A: I was attending the quarterly board meeting at the downtown office until approximately 9:30 PM.\n` +
        `Q: Did you review the audit report before signing off?\n` +
        `A: On page ${i}, I confirm that I observed email exchanges from the Chief Financial Officer discussing wire transfers.\n` +
        `Q: Were any exhibits attached to that email?\n` +
        `A: No, the attachment referenced as Schedule 4 was omitted.\n`,
        { x: 50, y: 380, size: 11, font, lineHeight: 16 }
      );
    }
    const bytes = await doc.save();
    fs.writeFileSync(path.join(fixturesDir, 'multipage_deposition.pdf'), bytes);
    console.log('Created multipage_deposition.pdf');
  }

  // 4. Scanned image-only (no extractable text)
  {
    const doc = await PDFDocument.create();
    doc.addPage([600, 400]); // Blank page
    const bytes = await doc.save();
    fs.writeFileSync(path.join(fixturesDir, 'scanned_image_only.pdf'), bytes);
    console.log('Created scanned_image_only.pdf');
  }

  console.log('All fixtures created successfully.');
}

createFixtures().catch(console.error);

