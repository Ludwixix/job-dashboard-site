/**
 * ============================================================================
 * AUTONOMOUS GOOGLE APPS SCRIPT BACKEND & GOOGLE DATABASE ENGINE
 * Candidate: Sam Ludwig (sam.ludwig@gmail.com)
 * Target Drive: "Job Applications - Sam Ludwig"
 * Target Sheet: JobTracker ("Applications Tracker" / "Suggestions")
 * ============================================================================
 */

const GOOGLE_DRIVE_FOLDER_NAME = "Job Applications - Sam Ludwig";
const ADZUNA_APP_ID = "22c1598f";
const ADZUNA_APP_KEY = "80f80879483da4e99f928fce13bf7bfb";

function getOrCreateApplicationsDriveFolder() {
  const folders = DriveApp.getFoldersByName(GOOGLE_DRIVE_FOLDER_NAME);
  if (folders.hasNext()) {
    return folders.next();
  }
  const newFolder = DriveApp.createFolder(GOOGLE_DRIVE_FOLDER_NAME);
  newFolder.setDescription("Centralized storage for all tailored resumes, cover letters, and application packages for Sam Ludwig.");
  return newFolder;
}

function convertMarkdownToHtml(markdown, title) {
  const formattedBody = (markdown || "")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^\*\*(.+)\*\*$/gm, "<strong>$1</strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-•] (.+)$/gm, "<li>$1</li>")
    .replace(/\n{2,}/g, "</p><p>")
    .replace(/\n/g, "<br>");

  return '<!DOCTYPE html><html><head><meta charset="utf-8"><title>' + title + '</title>' +
    '<style>@page { margin: 16mm 14mm; size: A4; } body { font-family: Calibri, Arial, sans-serif; font-size: 10.5pt; color: #111827; line-height: 1.45; max-width: 760px; margin: 0 auto; } h1 { font-size: 19pt; font-weight: 800; color: #0f172a; margin: 0 0 2px; } h2 { font-size: 10.5pt; font-weight: 700; color: #1e1b4b; text-transform: uppercase; border-bottom: 1.5px solid #1e1b4b; margin: 14px 0 6px; padding-bottom: 2px; } h3 { font-size: 10.5pt; font-weight: 700; color: #334155; margin: 8px 0 1px; } li { margin: 1.5px 0 1.5px 14px; } p { margin: 4px 0; } strong { font-weight: 700; color: #0f172a; }</style></head><body><p>' + formattedBody + '</p></body></html>';
}

function saveApplicationDocsToDrive(jobData, resumeMarkdown, coverLetterMarkdown) {
  const rootFolder = getOrCreateApplicationsDriveFolder();
  const companyName = (jobData.company || "General_Applications").replace(/[^a-zA-Z0-9_-]/g, "_");
  const dateStr = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd");

  let companyFolder;
  const subFolders = rootFolder.getFoldersByName(companyName);
  if (subFolders.hasNext()) {
    companyFolder = subFolders.next();
  } else {
    companyFolder = rootFolder.createFolder(companyName);
  }

  const resumeHtml = convertMarkdownToHtml(resumeMarkdown, "Sam Ludwig - Resume - " + (jobData.company || ""));
  const resumePdfBlob = Utilities.newBlob(resumeHtml, "text/html", "Resume_" + companyName + ".html")
                                .getAs("application/pdf")
                                .setName("Sam_Ludwig_" + companyName + "_Resume_" + dateStr + ".pdf");
  const resumeFile = companyFolder.createFile(resumePdfBlob);
  resumeFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

  let clFileUrl = "";
  if (coverLetterMarkdown) {
    const clHtml = convertMarkdownToHtml(coverLetterMarkdown, "Sam Ludwig - Cover Letter - " + (jobData.company || ""));
    const clPdfBlob = Utilities.newBlob(clHtml, "text/html", "CoverLetter_" + companyName + ".html")
                               .getAs("application/pdf")
                               .setName("Sam_Ludwig_" + companyName + "_CoverLetter_" + dateStr + ".pdf");
    const clFile = companyFolder.createFile(clPdfBlob);
    clFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    clFileUrl = clFile.getUrl();
  }

  return {
    success: true,
    folderUrl: companyFolder.getUrl(),
    resumePdfUrl: resumeFile.getUrl(),
    coverLetterPdfUrl: clFileUrl,
    savedAt: new Date().toISOString()
  };
}

function doGet(e) {
  const action = (e && e.parameter && e.parameter.action) || "health";

  if (action === "health") {
    return ContentService.createTextOutput(JSON.stringify({
      status: "online",
      database: "Google Sheets & Google Drive",
      timestamp: new Date().toISOString()
    })).setMimeType(ContentService.MimeType.JSON);
  }

  if (action === "get_jobs") {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = ss.getSheetByName("Applications Tracker") || ss.getSheets()[0];
    const rows = sheet.getDataRange().getValues();
    const headers = rows[0];
    const jobs = [];
    for (let i = 1; i < rows.length; i++) {
      const r = rows[i];
      if (r[1] || r[2]) {
        jobs.push({
          date: r[0],
          company: r[1],
          title: r[2],
          status: r[3],
          source: r[4],
          notes: r[5]
        });
      }
    }
    return ContentService.createTextOutput(JSON.stringify({ success: true, count: jobs.length, jobs: jobs }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  if (action === "scan") {
    const result = runAutonomousCloudScrape();
    return ContentService.createTextOutput(JSON.stringify(result))
      .setMimeType(ContentService.MimeType.JSON);
  }

  return ContentService.createTextOutput(JSON.stringify({ error: "Unknown action" }))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);
    const action = data.action || "update_status";

    if (action === "save_application_pdf") {
      const driveResult = saveApplicationDocsToDrive(data.job || {}, data.resume, data.coverLetter);
      updateSheetRowWithDriveUrls(data.job, driveResult);
      return ContentService.createTextOutput(JSON.stringify(driveResult))
        .setMimeType(ContentService.MimeType.JSON);
    }

    if (action === "update_status") {
      const result = updateSheetStatus(data.company, data.title, data.status, data.notes);
      return ContentService.createTextOutput(JSON.stringify(result))
        .setMimeType(ContentService.MimeType.JSON);
    }

    if (action === "trigger_scan") {
      const scanResult = runAutonomousCloudScrape();
      return ContentService.createTextOutput(JSON.stringify(scanResult))
        .setMimeType(ContentService.MimeType.JSON);
    }

    return ContentService.createTextOutput(JSON.stringify({ success: false, message: "Unhandled action" }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ success: false, error: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function updateSheetRowWithDriveUrls(job, driveResult) {
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = ss.getSheetByName("Applications Tracker") || ss.getSheets()[0];
    const values = sheet.getDataRange().getValues();
    
    const company = String(job.company || "").trim();
    const title = String(job.title || "").trim();

    for (let i = 1; i < values.length; i++) {
      if (String(values[i][1]).toLowerCase() === company.toLowerCase() &&
          String(values[i][2]).toLowerCase() === title.toLowerCase()) {
        
        sheet.getRange(i + 1, 4).setValue("Applied / Confirmation Received");
        const docNotes = "Resume PDF: " + driveResult.resumePdfUrl + 
          (driveResult.coverLetterPdfUrl ? " | Cover Letter: " + driveResult.coverLetterPdfUrl : "") +
          " | Folder: " + driveResult.folderUrl;
        sheet.getRange(i + 1, 6).setValue(docNotes);
        return true;
      }
    }

    const dateStr = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd");
    sheet.appendRow([
      dateStr,
      company,
      title,
      "Applied / Confirmation Received",
      job.source || "Web Dashboard",
      "Resume PDF: " + driveResult.resumePdfUrl + " | Cover Letter: " + (driveResult.coverLetterPdfUrl || "N/A")
    ]);
    return true;
  } catch (e) {
    Logger.log("Error updating sheet with Drive URLs: " + e);
    return false;
  }
}

function updateSheetStatus(company, title, status, notes) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName("Applications Tracker") || ss.getSheets()[0];
  const values = sheet.getDataRange().getValues();

  for (let i = 1; i < values.length; i++) {
    if (String(values[i][1]).toLowerCase() === String(company).toLowerCase() &&
        String(values[i][2]).toLowerCase() === String(title).toLowerCase()) {
      
      if (status) sheet.getRange(i + 1, 4).setValue(status);
      if (notes) sheet.getRange(i + 1, 6).setValue(notes);
      return { success: true, updatedRow: i + 1 };
    }
  }

  return { success: false, message: "Job not found in sheet" };
}

function runAutonomousCloudScrape() {
  const scrapedJobs = [];
  const keywords = ["systems administrator", "IT support", "microsoft 365", "cloud engineer", "cyber security", "network engineer"];
  
  keywords.forEach(kw => {
    try {
      const url = "https://api.adzuna.com/v1/api/jobs/au/search/1?app_id=" + ADZUNA_APP_ID + "&app_key=" + ADZUNA_APP_KEY + "&results_per_page=20&what=" + encodeURIComponent(kw) + "&where=Melbourne&distance=25&max_days_old=14";
      const response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });
      if (response.getResponseCode() === 200) {
        const data = JSON.parse(response.getContentText());
        (data.results || []).forEach(r => {
          scrapedJobs.push({
            title: r.title,
            company: r.company && r.company.display_name ? r.company.display_name : "Unknown Company",
            url: r.redirect_url,
            location: r.location && r.location.display_name ? r.location.display_name : "Melbourne VIC",
            posted: (r.created || "").split("T")[0],
            source: "Adzuna",
            salary: r.salary_min ? "$" + Math.round(r.salary_min) + " - $" + Math.round(r.salary_max || r.salary_min) : null,
            description: r.description
          });
        });
      }
    } catch (e) {
      Logger.log("Adzuna scrape error: " + e);
    }
  });

  try {
    const vicUrl = "https://careers.vic.gov.au/jobs/rss?category=information-technology&location=melbourne";
    const vicRes = UrlFetchApp.fetch(vicUrl, { muteHttpExceptions: true });
    if (vicRes.getResponseCode() === 200) {
      const xml = XmlService.parse(vicRes.getContentText());
      const items = xml.getRootElement().getChild("channel").getChildren("item");
      items.forEach(item => {
        scrapedJobs.push({
          title: item.getChildText("title"),
          company: "Victorian State Government (Careers Vic)",
          url: item.getChildText("link"),
          location: "Melbourne VIC",
          posted: Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd"),
          source: "Careers Vic",
          description: item.getChildText("description")
        });
      });
    }
  } catch (e) {
    Logger.log("Careers Vic notice: " + e);
  }

  syncNewJobsToSuggestionsSheet(scrapedJobs);

  return {
    success: true,
    scrapedCount: scrapedJobs.length,
    timestamp: new Date().toISOString()
  };
}

function syncNewJobsToSuggestionsSheet(jobs) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sugSheet = ss.getSheetByName("Suggestions");
  if (!sugSheet) {
    sugSheet = ss.insertSheet("Suggestions");
    sugSheet.appendRow(["Date", "Company", "Job Title", "Location", "Salary", "Source", "Portal Link", "Notes / Description"]);
  }

  const existingData = sugSheet.getDataRange().getValues();
  const seen = new Set();
  for (let i = 1; i < existingData.length; i++) {
    seen.add(String(existingData[i][1]).toLowerCase() + "_" + String(existingData[i][2]).toLowerCase());
  }

  let added = 0;
  jobs.forEach(j => {
    const key = (j.company || "").toLowerCase() + "_" + (j.title || "").toLowerCase();
    if (!seen.has(key)) {
      sugSheet.appendRow([
        j.posted || Utilities.formatDate(new Date(), Session.getScriptTimeZone(), "yyyy-MM-dd"),
        j.company,
        j.title,
        j.location,
        j.salary || "",
        j.source,
        j.url,
        j.description || ""
      ]);
      seen.add(key);
      added++;
    }
  });

  Logger.log("Added " + added + " new scraped jobs to Suggestions sheet.");
}

function syncGmailToJobTracker() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let mainSheet = ss.getSheetByName("Applications Tracker") || ss.getSheets()[0];

  const searchQuery = 'subject:("Application sent for" OR "Your application for" OR "Application received" OR "Application Confirmation")';
  const threads = GmailApp.search(searchQuery, 0, 50);

  const existingData = mainSheet.getDataRange().getValues();
  const existingKeys = new Set();
  for (let i = 1; i < existingData.length; i++) {
    const comp = String(existingData[i][1] || "").toLowerCase().trim();
    const title = String(existingData[i][2] || "").toLowerCase().trim();
    if (comp && title) {
      existingKeys.add(comp + "_" + title);
    }
  }

  let newRowsCount = 0;

  for (let i = 0; i < threads.length; i++) {
    const messages = threads[i].getMessages();
    const firstMsg = messages[0];
    const subject = firstMsg.getSubject();
    const date = Utilities.formatDate(firstMsg.getDate(), Session.getScriptTimeZone(), "yyyy-MM-dd");

    const match = subject.match(/(?:Application sent for|You applied for|Your application for|Confirmation:)\s+(.*?)\s+(?:at|with|-)\s+(.*)/i);
    
    if (match) {
      const title = match[1].trim();
      const company = match[2].trim();
      const key = company.toLowerCase() + "_" + title.toLowerCase();

      if (!existingKeys.has(key)) {
        mainSheet.appendRow([
          date,
          company,
          title,
          "Applied / Confirmation Received",
          "Gmail Auto-Sync",
          subject
        ]);
        existingKeys.add(key);
        newRowsCount++;
      }
    }
  }

  Logger.log("Successfully auto-synced " + newRowsCount + " new job application receipts from Gmail.");
}

function setupAutomatedTriggers() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => ScriptApp.deleteTrigger(t));

  ScriptApp.newTrigger("syncGmailToJobTracker")
    .timeBased()
    .everyMinutes(15)
    .create();

  ScriptApp.newTrigger("runAutonomousCloudScrape")
    .timeBased()
    .everyHours(6)
    .create();

  Logger.log("Automated 15-minute Gmail sync and 6-hour Cloud Scrape triggers successfully installed.");
}
