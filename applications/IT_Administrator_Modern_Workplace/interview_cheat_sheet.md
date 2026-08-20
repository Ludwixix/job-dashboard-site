# Interview Cheat Sheet: IT Administrator (Modern Workplace & Hybrid Systems)

## 🎯 Your Value Proposition (30-second elevator pitch)

> "I've spent the last 5+ years managing hybrid M365 environments at enterprise scale — including the largest SharePoint farm in the Southern Hemisphere (660K+ users). I specialise in the exact transition you're doing: managing hybrid AD/M365 environments, automating identity and endpoint operations, and keeping the business running while you modernise. I don't just configure tools — I build the automation that makes them manageable."

---

## 🔥 Likely Questions & Killer Answers

### 1. "Tell us about your experience with hybrid AD / Entra ID migration."

**Strategy:** Lead with scale and automation. Don't just say you've done it — show how.

**Answer:**
"I've managed hybrid AD environments connecting on-premises Active Directory to Entra ID using Azure AD Connect, with 660,000+ identities in scope. I handled identity conflict resolution between AD, Entra ID, and Google Workspace, managed user synchronization workflows, and built PowerShell automation for bulk provisioning and tenant configuration. The key lesson I learned is that the migration strategy is only as good as your data quality — so I always start with a deep identity audit before touching any sync rules."

**Key things to mention:**
- Azure AD Connect / Entra ID Connect sync configuration
- Password hash sync vs Pass-through Auth vs Federation
- UPN suffix mapping and domain verification
- Group scope filtering and OU-based sync

---

### 2. "How would you approach the planned migration to Entra ID for this organisation?"

**Strategy:** Show structured thinking. Walk through a phased approach.

**Answer:**
"I'd break it into four phases:

1. **Discovery & Audit** — Map current AD structure, identify stale accounts, document group nesting, verify UPN alignment, and audit sync scope. I'd do this via PowerShell before touching anything.

2. **Pilot** — Select a non-critical OU group, configure Entra ID Connect in staging mode first, validate sync, test authentication, and verify group memberships land correctly.

3. **Rollout** — Migrate in waves by business unit, using my automation scripts to handle bulk attribute mapping and verify each wave before proceeding.

4. **Cutover & Decommission** — Once all workloads are verified in Entra ID, I'd establish a schedule for legacy AD dependency removal, with a documented rollback plan for each service."

---

### 3. "What experience do you have with Intune and Autopilot?"

**Strategy:** Show hands-on depth. Talk about compliance policies, device enrolment, and the deployment pipeline.

**Answer:**
"I've configured Intune compliance policies, device configuration profiles, and Autopilot deployment profiles across enterprise environments. At Australia Post, I managed device lifecycle including Autopilot enrolment, OS re-imaging, and provisioning. At St John of God Health Care, I led the Windows 11 migration for 100+ clinical endpoints using Intune and Autopilot policies. My approach is 'zero-touch wherever possible' — if a laptop can arrive at a user's desk and be fully configured with nothing more than a Wi-Fi connection and their credentials, that's the goal."

**Key talking points:**
- Autopilot vs traditional imaging — why Autopilot wins
- ESP configuration (timeout settings, critical app blocking)
- Company Portal vs fully automated app deployment
- Device compliance policies tied to Conditional Access
- Windows Update rings and patch management

---

### 4. "Tell me about your networking experience — VPN, DNS, DHCP."

**Strategy:** Be honest about depth but demonstrate solid fundamentals. Sam has networking from his infrastructure work.

**Answer:**
"I've worked extensively with networking in the context of hybrid cloud deployments. I've configured DHCP and DNS for on-premises environments, managed VPN connectivity for remote access, and troubleshot FortiGate VPN routing issues. Full-tunnel configurations are something I understand well — it's about making sure the routing table doesn't leak traffic and that split tunnelling (or the absence of it) aligns with security requirements. While I'm not a dedicated network engineer, I'm very comfortable managing and troubleshooting the networking layer that supports a modern workplace environment."

**Be ready for:**
- "Walk me through how a DHCP request works end-to-end"
- "Explain the difference between a VPN full-tunnel and split-tunnel"
- "How would you troubleshoot a user who can't connect to the VPN?"
- "What's the difference between DNS A and CNAME records?"

---

### 5. "How would you manage HubSpot and Aircall administration?"

**Strategy:** Show you're a quick learner with SaaS platform experience. Honesty about specifics, confidence about capability.

**Answer:**
"While I haven't been a dedicated HubSpot or Aircall admin, I've been the technical owner for multiple SaaS platforms including the full M365 stack and ServiceNow, where I managed integrations, user provisioning, and configuration. My approach to a new platform is systematic: I start with the knowledge base and admin docs, map out the integration points, audit the current configuration, and then identify quick wins. I'd expect to be self-sufficient on HubSpot administration within two weeks, including user provisioning, pipeline configuration, and integrating it with the M365 stack."

---

### 6. "Walk me through a complex technical problem you solved."

**Strategy:** Use STAR method. Pick something impressive from Capgemini.

**Answer (STAR):**

- **Situation:** At Knosys, we had significant manual overhead in recurring administrative tasks for the intranet platform, consuming hours of engineering time each week for repetitive processing.
- **Task:** I needed to eliminate the manual steps to free up engineering capacity for higher-value work.
- **Action:** I built a PowerShell automation framework that handled user provisioning, content management, and platform maintenance in a single pipeline, integrated with Azure DevOps for scheduled execution.
- **Result:** Processing time was reduced by up to 87% across recurring tasks, and ongoing maintenance effort dropped by 20% through automated patching scripts.

---

### 7. "How do you stay current with Microsoft 365 changes?"

**Answer:**
"I follow the Microsoft 365 Roadmap via the admin centre and subscribe to the monthly Message Center digest. I hold an Azure Administrator Associate certification which requires staying current with platform changes. Beyond that, the PowerShell community and Microsoft Tech Community are solid signal sources for what's actually working in production, not just what's been announced."

---

### 8. "Where do you see yourself in five years?"

**Strategy:** Show ambition that aligns with the role — growing within the company, not using it as a stepping stone.

**Answer:**
"I want to be the person who's built and owns this company's modern workplace environment end-to-end. In five years, I see myself in a senior infrastructure or IT management role — probably at the same company — where I've driven the full digital transformation from hybrid legacy to cloud-native. I'm not looking for short stints. I want to build something and see it through."

---

### 9. "Why do you want to leave Capgemini / your current role?"

**Strategy:** Frame positively. Focus on wanting ownership and impact, not escaping a bad situation. **Do NOT mention the Fair Work case.**

**Answer (prepared):**
"Consulting is great for breadth of experience, but I've reached a point where I want deeper ownership. I want to manage a single environment end-to-end — see the impact of my decisions, build relationships with the team, and drive transformation rather than just being brought in for a project phase. This role offers exactly that."

**Backup (if they push):**
"The project requirements changed, and the trajectory of the work shifted away from the hands-on infrastructure ownership I enjoy most. It was a mutual recognition that my strengths are better applied in an environment like this one."

---

### 10. "Tell me about a time you had to support a legacy system while modernising."

**Answer:**
"This is essentially what I did at Capgemini across the SharePoint migration. The environment had hundreds of legacy SharePoint 2010/2013 sites running alongside SharePoint Online. We couldn't just flip a switch — business-critical workflows depended on those legacy sites. My approach was to maintain strict operational monitoring for the legacy platform while running parallel migration streams, giving business owners clear timetables for cutover. I documented every dependency before touching anything, and built rollback scripts for each migration wave so we could pull the cord if needed."

---

## 💡 Questions YOU Should Ask Them

| Question | Why Ask |
|---|---|
| "What does the current AD-to-Entra ID migration roadmap look like — what phase are you in?" | Shows you're thinking about the work, not just getting a job |
| "What's the current Intune/Autopilot maturity level — fully deployed, pilot, or greenfield?" | Positions you as someone who can assess and drive |
| "How mature is the HubSpot instance? Is there a dedicated CRM person or is IT owning it?" | Shows you're thinking about the SaaS management scope |
| "What does success look like for this role in 90 days? In 12 months?" | Shows you're strategic and want to align |
| "Who else is on the tech team? Is this a solo role or is there a team?" | Practical — you need to know the support structure |
| "What's the current state of the on-prem SQL server — is the modernisation project scoped yet?" | Shows you read the JD carefully and understand the legacy work |

---

## 🚩 Topics to AVOID

- **Fair Work case** (C2026/6670) — Never. Not their business. If they ask directly about termination, use the "mutual recognition" framing above.
- **Capgemini exposé / MSP Playbook** — Keep personal and professional brands completely separate.
- **Negative talk about Capgemini** — Even if justified, it's a red flag to hiring managers. Focus on what you want to build, not what you're leaving behind.
- **Salary in first interview** — Let them bring it up. If pressed, "I'm looking for market rate for a role of this scope — what's the budgeted range?"

---

## 📋 Before the Interview

- [ ] Review this cheat sheet and practise answers out loud
- [ ] Prepare 2-3 questions from the list above
- [ ] Know the company (industry, size, recent news) — research if you have the name
- [ ] Have your personal site (samludwig.au) and LinkedIn up to date
- [ ] Test your internet/camera/audio if it's a video interview
- [ ] Dress one notch above what you think is necessary

---

## 📌 Key Messages to Weave In

1. **Scale** — 660K users, largest SharePoint farm in Southern Hemisphere
2. **Automation** — 87% processing reduction, PowerShell-first approach
3. **Hybrid depth** — AD/Entra ID management, identity sync, endpoint lifecycle
4. **Ownership mentality** — You want the whole environment, not a ticket queue
5. **Breadth of experience** — Enterprise M365, healthcare endpoint migration, logistics IT, SaaS platform support

**Remember:** You're not just qualified for this role. You're overqualified in the areas that matter and honest about the areas you'll grow into. Confidence, competence, no bullshit.
