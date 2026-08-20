# Study Guide: IT Administrator (Modern Workplace & Hybrid Systems)

## 🎯 Purpose

This study guide covers the specific technologies and concepts mentioned in the job description. Brush up on these areas to confidently discuss them in depth during the interview. **Focus 80% of your prep time on the topics marked 🔴.**

---

## 🔴 HIGH PRIORITY — Core JD Requirements

### 1. 🔴 Active Directory → Entra ID Migration

**You already know:** AD Connect, sync scoping, UPN mapping (from your Capgemini AD/Entra ID/Google Workspace sync management).

**Review:** [https://learn.microsoft.com/en-us/entra/identity/hybrid/](https://learn.microsoft.com/en-us/entra/identity/hybrid/)

**Key concepts to articulate confidently:**
- Azure AD Connect vs Entra ID Connect (what changed?)
- Staging mode — what it is and why it's essential
- Password Hash Sync vs Pass-Through Authentication vs Federation (AD FS)
- Seamless SSO — how it works
- Group writeback vs device writeback
- Entra ID Cloud Sync — when to use it instead of Connect
- Sourcing authority — how to avoid sync conflicts
- Filtering: OU-based, domain-based, attribute-based

**PowerShell commands to know:**
```powershell
# Check AD sync status
Get-ADSyncScheduler
Set-ADSyncScheduler -SyncCycleEnabled $true
Start-ADSyncSyncCycle -PolicyType Delta

# Check Entra ID directory sync status
Get-MgOrganization | Select-Object OnPremisesSyncEnabled
```

---

### 2. 🔴 Microsoft Intune & Windows Autopilot

**You already know:** Compliance policies, device enrolment (from Australia Post and St John of God Health Care deployments).

**Review:** [https://learn.microsoft.com/en-us/mem/autopilot/](https://learn.microsoft.com/en-us/mem/autopilot/)

**Key concepts to articulate:**
- Autopilot deployment modes: User-driven vs Self-deploying vs White Glove (pre-provisioning)
- Registration methods: OEM, CSP, manually importing hardware hashes (PKID), or using Autopilot profile
- ESP (Enrolment Status Page) — what happens when it times out
- Device compliance policies linked to Conditional Access (the "health" chain)
- Company Portal vs assigned apps vs available apps
- Windows Update rings — deferral policies, servicing channel
- Configuration profiles vs Compliance policies vs Feature updates
- Endpoint Analytics — what it measures

**Intune troubleshooting:**
```powershell
# Get Intune managed device info
Get-MgDeviceManagementManagedDevice -Filter "operatingSystem eq 'Windows'" | Select-Object DeviceName, ComplianceState, LastSyncDateTime

# Trigger sync
Sync-MgDeviceManagementManagedDevice -ManagedDeviceId $deviceId
```

---

### 3. 🔴 FortiGate VPN & Networking Fundamentals

**You probably know this already but may need to refresh terminology.**

**Study:**
- FortiGate VPN types: SSL VPN vs IPsec VPN
- Full tunnel vs split tunnel — routing implications for each
- FortiClient EMS integration for remote access
- FortiGate firewall policies and security profiles

**Core networking you WILL be asked:**
```text
- OSI Model layers 1-4 (practical implications, not memorisation)
- DHCP: DORA process (Discover → Offer → Request → Acknowledge)
- DNS resolution flow (local cache → hosts file → DNS server → recursion)
- Ports: 443 (HTTPS), 3389 (RDP), 8443 (VPN portals), 389/636 (LDAP/LDAPS)
- What happens when a user can't connect to VPN: check layers in order
- Difference between static and dynamic routing
- NAT — what it is and why it matters for VPN
- Subnetting — how to identify if two IPs are on the same subnet
```

**Be ready for this question:**
> *"A remote user can connect to the VPN but can't access internal resources on 10.0.1.x. Walk me through your troubleshooting."*

Answer framework:
1. Verify VPN client shows connected → confirms Phase 1/Phase 2 are up
2. Check routing table on client → is the 10.0.1.x route present and correct?
3. Check FortiGate routing table → is 10.0.1.x route pointing to correct interface?
4. Check firewall policy → is VPN traffic allowed to 10.0.1.x network?
5. Check if the target server's firewall is permitting the traffic
6. Test connectivity: ping (ICMP), then specific port (telnet/Test-NetConnection)

---

### 4. 🔴 PowerShell Automation (Your Superpower)

**You already know:** PnP PowerShell, Graph API, Exchange Online.

**Spend 30 mins reviewing:**
- Microsoft Graph PowerShell SDK (MgGraph modules, not just the old AzureAD module)
- Graph API authentication: delegated vs application permissions
- Consent framework — admin consent workflow
- Graph API batch requests for bulk operations

**Scripts to have ready to talk about:**
- Your M365 tenant configuration automation framework (the 2hr→15min one)
- MFA compliance auditing script
- Entra ID migration automation

```powershell
# Modern Graph approach (have this ready to demonstrate)
Connect-MgGraph -Scopes "User.Read.All", "Organization.Read.All"

# Bulk user creation/modification
Import-Csv "users.csv" | ForEach-Object {
    New-MgUser -DisplayName $_.DisplayName -UserPrincipalName $_.UUPN `
        -MailNickname $_.Alias -PasswordProfile @{
            Password = $_.TempPassword
            ForceChangePasswordNextSignIn = $true
        } -AccountEnabled $true
}
```

---

### 5. 🔴 SaaS Platforms (HubSpot, Aircall, CodeTwo)

**HubSpot — what to know (they said "bonus" but aim to impress):**

| Feature | What to Know |
|---|---|
| HubSpot CRM Hub | Contacts, Companies, Deals, Pipelines, Activities |
| HubSpot Marketing Hub | Email campaigns, landing pages, automation workflows |
| HubSpot Service Hub | Ticketing, knowledge base, customer feedback |
| User Management | Roles, permissions, teams, SSO (Entra ID integration) |
| Integrations | M365 (calendar, email sync), Aircall, Slack |
| Migration | Import/export, custom properties, GDPR compliance |

**Aircall — what to know:**
- Cloud-based phone system, integrates with HubSpot
- User provisioning, call routing, IVR, call analytics
- Number porting process

**CodeTwo — what to know:**
- Email signature management for Exchange Online
- How CodeTwo integrates with M365 (service principal, mail flow rules)
- Signature templates, banner management, GDPR consent signatures

---

## 🟡 MEDIUM PRIORITY — Should Know Cold

### 6. Legacy SQL Server Operational Support

**What they'll ask:** *"How would you maintain an on-prem SQL Server while it's being migrated?"*

**Key points:**
- Basic SQL Server administration: backups, index maintenance, log management
- Monitoring: disk space, CPU, memory for SQL
- SQL Agent jobs — what to look for
- Migration paths: SQL Server → Azure SQL Database → SQL Managed Instance
- Ensure business continuity: transaction log backup frequency, HA (always on availability groups)
- "I would establish monitoring and backup baselines, document dependencies, and let the migration team focus on modernisation while I keep the lights on for SQL"

---

### 7. Device Lifecycle Management

**They will ask about this — it's a listed responsibility.**

**Have a framework ready:**
1. **Procurement** — Standard device spec, supplier relationship, budget tracking
2. **Enrolment** — Autopilot registration, device hash import, initial config
3. **Configuration** — Intune profiles, LOB apps, security baselines, BitLocker
4. **Ongoing Management** — Patch cycles, compliance monitoring, health alerts
5. **Retirement** — Data wipe, device de-registration, asset disposal

---

### 8. Identity & Access Governance

**Key topics:**
- PIM (Privileged Identity Management) — Just-In-Time access, approval workflows
- Entra ID Identity Governance — access reviews, entitlement management
- RBAC — Azure vs Entra ID vs application roles
- Guest user management (B2B collaboration)
- MFA — Conditional Access policies vs Security defaults

---

## 🟢 LOW PRIORITY — Skim Once

### 9. ServiceNow Integration

You already know this well. Just have a 30-second story ready:
> *"I built a ServiceNow-M365 integration using presence data and an algorithmic workload engine that routed 1,000+ tickets per month based on real-time engineer availability."*

**Bolt-on insight:** Talk about the Graph API webhook mechanism that enabled real-time status sync.

---

### 10. General IT Procurement & Vendor Management

- Hardware procurement cycles
- Asset tagging, auditing, inventory management
- Peripheral management (monitors, docks, headsets)

---

## 🧪 PRACTICE EXERCISES

### Exercise 1: Design an Intune Autopilot deployment (5 mins)
Talk through the steps for deploying 50 new laptops:
1. Get hardware hashes from OEM
2. Import hashes into Intune
3. Create Autopilot deployment profile (User-driven)
4. Create device configuration profile (BitLocker + security baseline)
5. Assign apps via Intune (required vs available)
6. Configure ESP to block until Office 365 is installed
7. Create compliance policy
8. Create Conditional Access policy (device must be compliant)
9. Ship laptops to users with sign-in instructions
10. Done. Zero IT touch.

### Exercise 2: Troubleshoot a user who can't access SharePoint Online (2 mins)
1. Check network connectivity (general internet access)
2. Check AAD sign-in logs (successful? MFA challenge pass?)
3. Check SharePoint admin centre (site exists, user has permissions?)
4. Check browser (modern auth enabled? AAD conditional access block?)
5. Check Conditional Access policies (access policy blocking?)
6. Check SharePoint Access Policy (location-based? device compliance?)

### Exercise 3: Explain the AD-to-Entra ID migration process (3 mins)
Walk through the four-phase approach from the cheat sheet. Practise it until it's fluid.

---

## 📚 QUICK STUDY RESOURCES

| Topic | URL |
|---|---|
| Entra ID Hybrid Identity | [https://learn.microsoft.com/en-us/entra/identity/hybrid/](https://learn.microsoft.com/en-us/entra/identity/hybrid/) |
| Intune Autopilot | [https://learn.microsoft.com/en-us/mem/autopilot/](https://learn.microsoft.com/en-us/mem/autopilot/) |
| FortiGate VPN Admin | [https://docs.fortinet.com/product/fortigate/7.4](https://docs.fortinet.com/product/fortigate/7.4) |
| HubSpot Admin Guide | [https://knowledge.hubspot.com/account](https://knowledge.hubspot.com/account) |
| PowerShell Graph SDK | [https://learn.microsoft.com/en-us/powershell/microsoftgraph/](https://learn.microsoft.com/en-us/powershell/microsoftgraph/) |
| Aircall Admin | [https://help.aircall.io/en/](https://help.aircall.io/en/) |
| CodeTwo Exchange Signatures | [https://www.codetwo.com/administrator-guide/](https://www.codetwo.com/administrator-guide/) |

---

## ⏱ 48-HOUR PREP PLAN

| Day | Focus | Time |
|---|---|---|
| **Day 1** | AD→Entra ID migration (🔴) + Intune/Autopilot (🔴) + PowerShell review (🔴) | 3 hrs |
| **Day 2** | FortiGate VPN (🔴) + Networking fundamentals + HubSpot (🟡) + Practise cheat sheet answers out loud | 2 hrs |
| **30 mins before** | Skim this study guide + cheat sheet. Practise your elevator pitch once. | 30 mins |

---

**You've got this.** You're a stronger candidate than most people who'll apply — you have the enterprise scale, the automation depth, and the consulting polish. The prep is just about making sure you articulate it clearly and handle anything they throw at you on the specific tech stack.
