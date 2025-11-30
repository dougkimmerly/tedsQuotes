# TBG Enterprises Quote Builder

A simple Mac app for creating professional home renovation quotes and exporting them to QuickBooks.

![TBG Enterprises](https://via.placeholder.com/200x60/C41E3A/FFFFFF?text=TBG+Enterprises)

## Features

- ✅ Easy-to-use graphical interface
- ✅ Professional PDF quote generation (red/black/white branding)
- ✅ **Attach plans, photos, and PDFs** to quotes
- ✅ Export to QuickBooks Online (CSV)
- ✅ Export to QuickBooks Desktop (IIF)
- ✅ Automatic payment schedule calculation (20% deposit + weekly payments)
- ✅ Pre-configured categories for home renovation work

## Quick Start (5 minutes)

### Step 1: Download Python (if you don't have it)

1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Click "Download Python 3.x.x" (the big yellow button)
3. Run the installer, click through the prompts

### Step 2: Set Up the Quote Builder

1. Download this folder to your Mac (e.g., to your Desktop)
2. Open **Terminal** (search for it in Spotlight with Cmd+Space)
3. Type: `cd ` (with a space after cd)
4. Drag the `tbg-quote-builder` folder into Terminal - it will fill in the path
5. Press Enter
6. Type: `chmod +x install.command && ./install.command`
7. Press Enter and wait for it to finish

### Step 3: Run the App

- **Double-click** `run_quote_builder.command` to start the app

That's it! 🎉

---

## How to Use

### Creating a Quote

1. **Double-click** `run_quote_builder.command` to open the app
2. Fill in customer information (name, address, phone, email)
3. Add a project description
4. Enter your line items:
   - Select a category from the dropdown
   - Type a description
   - Enter quantity, unit, and rate
   - Click "+ Add Line Item" for more rows
5. Set the estimated project duration in weeks
6. **Add attachments** (optional):
   - Click "+ Add Images/PDFs" to attach floor plans, photos, or PDF drawings
   - Attachments will be included at the end of the quote PDF
7. Click **Generate PDF Quote** to create the customer-facing document

### Exporting to QuickBooks

**For QuickBooks Online:**
1. Click **Export for QuickBooks Online (CSV)**
2. Save the file
3. In QuickBooks Online:
   - Go to Settings (gear icon) → Import Data
   - Choose "Estimates"
   - Upload the CSV file

**For QuickBooks Desktop:**
1. Click **Export for QuickBooks Desktop (IIF)**
2. Save the file
3. In QuickBooks Desktop:
   - Go to File → Utilities → Import → IIF Files
   - Select the file

---

## Payment Schedule

The app automatically calculates:
- **20% deposit** due upon acceptance
- **Remaining balance** split evenly over the estimated project weeks

Example for a $10,000 job over 4 weeks:
- Deposit: $2,000
- Week 1-4: $2,000/week

---

## Categories

Pre-configured for home renovation:
- Demo
- Framing
- Electrical
- Plumbing
- HVAC
- Drywall
- Painting
- Flooring
- Tile
- Showers
- Cabinets
- Countertops
- Fixtures
- Trim/Finish
- Cleanup
- Materials
- Other

---

## Using ChatGPT to Help

See **ChatGPT_Prompt_Guide.md** for prompts you can copy/paste into free ChatGPT to help you:
- Break down projects into line items
- Estimate labor hours
- Write professional project descriptions
- Double-check you haven't forgotten anything

---

## Troubleshooting

### "Python not found"
Download Python from [python.org/downloads](https://www.python.org/downloads/)

### App won't open when double-clicking
1. Right-click the file → Open
2. Click "Open" in the security dialog
3. (You only need to do this once)

### "Permission denied"
Open Terminal and run:
```bash
chmod +x run_quote_builder.command
chmod +x install.command
```

### Quotes not importing to QuickBooks
- Make sure customer names in QuickBooks match exactly
- For QBO: Check that you're importing as "Estimates", not "Invoices"
- For Desktop: Make sure you have an "Accounts Receivable" and "Services" account

---

## Files in This Folder

- `tbg_quote_builder.py` - The main application
- `run_quote_builder.command` - Double-click to run the app
- `install.command` - Run once to set up
- `ChatGPT_Prompt_Guide.md` - Prompts for using ChatGPT to help
- `README.md` - This file

---

## Support

This app was custom-built for TBG Enterprises. For questions or modifications, contact the developer.
