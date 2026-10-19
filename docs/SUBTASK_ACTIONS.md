# Subtask → Action Map (hand-maintained)

**You fill this in by hand.** For every subtask, say what it drives: which field or document you touch, and what should happen when it is marked Done or Issue. Rules in `rules/rules.json` prove some links; only you know the rest. This file is written once by a throwaway script and is **never regenerated** — re-running repo scripts will not overwrite your answers.

## How to answer

Type directly into the blank cells. Leave **Rules today** alone. Use `?` if unsure.

| Column | Meaning |
|---|---|
| Subtask | Subtask name. **Bold** = at least one rule references it. |
| Auto | `Y` = `autoCreate` (created with the task); `N` = added only when a condition is met. |
| Rules today | What existing rules do with it: Done/Issue effects, what adds it, what auto-completes it. |
| Intent | `Manual` (a person does it), `Automated` (a rule/system does it), `Planned` (automation wanted, not built), `N/A`. |
| Field / doc touched | The Encompass field ID or eFolder document the user touches that should complete it. |
| Done should… | Actions that should fire when marked Done (create task, send docs, set field, start timer…). |
| Issue should… | Actions that should fire when marked Issue. |
| Notes | Anything else. |

## Progress

**292 subtasks** across **79 tasks** · **112** with rule links · **180** without · **72** pre-filled (✓).

## Legend

- ✓ = derived from rules; confirm or override.
- ⚠ = rule reference matched only after normalising hyphen/en-dash (the rule's type differs from the XML type).
- — = no rule references this subtask.

---

## File Follow Up (15 Day)

`PipelineMgt_PreApp_FollowUp15` · [file_follow_up_15_day_v1.xml](../tasks/1_origination/pipeline_management/file_follow_up_15_day_v1.xml) · roadmap `task_071` (completed, Origination)

Created by: `Live App Follow Up (15 Days)`, `Pre-App Follow Up (15 Days)`, `PreApp Follow Up 15` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Decision Status** | Y | Issue → create task Processing_Misc_NoticeOfIncomplete (`Task_CreateNOI_15Day`) | Automated ✓ |  |  | create task Processing_Misc_NoticeOfIncomplete ✓ |  |

## File Follow Up (30 Day)

`PipelineMgt_PreApp_FollowUp` · [file_follow_up_30_day_v1.xml](../tasks/1_origination/pipeline_management/file_follow_up_30_day_v1.xml) · roadmap `task_072` (completed, Origination)

Created by: `Live App Follow Up (30 Days)`, `Pre-App Follow Up (30 Days)` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Decision Status** | Y | Issue → create task Processing_Misc_NoticeOfIncomplete (`Task_CreateNOI_30Day`) | Automated ✓ |  |  | create task Processing_Misc_NoticeOfIncomplete ✓ |  |

## Review Credit

`Processing_FileSetup_ReviewCredit` · [review_credit_v1.xml](../tasks/2_processing/credit_review/review_credit_v1.xml) · roadmap `task_001` (completed, Processing)

Created by: `Task_CreditReview` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Name Discrepancy** | Y | Issue → add condition "Red Flag Discrepancy (Name)" (`Condition_CreditReview_Name`) | Automated ✓ |  |  | add condition "Red Flag Discrepancy (Name)" ✓ |  |
| Sub-Task Name | Y | — |  |  |  |  |  |
| **Address Discrepancy** | Y | Issue → add condition "Red Flag Discrepancy (Address)" (`Condition_CreditReview_Address`) | Automated ✓ |  |  | add condition "Red Flag Discrepancy (Address)" ✓ |  |
| **SSN Discrepancy** | Y | Issue → add condition "Social Security Number Verification" (`Condition_CreditReview_SSVN`) | Automated ✓ |  |  | add condition "Social Security Number Verification" ✓ |  |
| **OFAC** | Y | Issue → add condition "Red Flag Discrepancy (OFAC)" (`Condition_CreditReview_OFAC`) | Automated ✓ |  |  | add condition "Red Flag Discrepancy (OFAC)" ✓ |  |
| **Fraud Alerts** | Y | Issue → add condition "Red Flag Discrepancy (Fraud Alert)" (`Condition_CreditReview_Fraud`) | Automated ✓ |  |  | add condition "Red Flag Discrepancy (Fraud Alert)" ✓ |  |
| **Frozen Score** | Y | Issue → add condition "Red Flag Discrepancy (Frozen)" (`Condition_CreditReview_Frozen`) | Automated ✓ |  |  | add condition "Red Flag Discrepancy (Frozen)" ✓ |  |
| **Red Flag Form** | Y | Done → condition "Red Flag Discrepancy (Name)" → Cleared; condition "Red Flag Discrepancy (Fraud Alert)" → Cleared; condition "Red Flag Discrepancy (Address)" → Cleared; condition "Red Flag Discrepancy (Frozen)" → Cleared; condition "Red Flag Discrepancy (OFAC)" → Cleared (`Condition_CreditReview_RedFlagForm`) | Automated ✓ |  | condition "Red Flag Discrepancy (Name)" → Cleared; condition "Red Flag Discrepancy (Fraud Alert)" → Cleared; condition "Red Flag Discrepancy (Address)" → Cleared; condition "Red Flag Discrepancy (Frozen)" → Cleared; condition "Red Flag Discrepancy (OFAC)" → Cleared ✓ |  |  |
| Review Liens | Y | — |  |  |  |  |  |

## Send Disclosures

`Processing_FileSetup_SendDisclosures` · [send_disclosures_v1.xml](../tasks/2_processing/disclosures/send_disclosures_v1.xml) · roadmap `task_002` (completed, Processing)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Index | Y | — |  |  |  |  |  |
| Appraisal Fee Only | Y | — |  |  |  |  |  |
| FACT Act Disclosure – All Scores | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Checkboxes | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Key Factors | Y | — |  |  |  |  |  |
| FACT Act Disclosure – eConsent | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Contact Info | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Ready to Send | Y | — |  |  |  |  |  |
| Home Counseling List | Y | — |  |  |  |  |  |

## Send Disclosures (HELOC)

`Processing_FileSetup_SendDisclosuresHELOC` · [send_disclosures_heloc_v1.xml](../tasks/2_processing/disclosures/send_disclosures_heloc_v1.xml) · roadmap `task_002b` (completed, Processing)

Created by: `Task_HELOCIntiailDocs` · Completed by: `Task_Cancel_AllAdverse` · On create: `Task_HELOCIntiailDocs2`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Program Selection | Y | — |  |  |  |  |  |
| Index | Y | — |  |  |  |  |  |
| Sub-Task Name | Y | — |  |  |  |  |  |
| Appraisal Fee Only | Y | — |  |  |  |  |  |
| 1003 – Demographic HELOC | Y | — |  |  |  |  |  |
| FACT Act Disclosure – All Scores | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Checkboxes | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Key Factors | Y | — |  |  |  |  |  |
| Home Counseling List | Y | — |  |  |  |  |  |
| **Order AVM** | N | Added by: task created: Processing_FileSetup_SendDisclosuresHELOC [[#2] <= 400000] (`Task_HELOCIntiailDocs2`)<br>Auto-done by: task completed: Processing_ServiceOrders_OrderAVM (Issue) → Issue (`Task_AVMFailCompletion`)<br>Auto-done by: task completed: Processing_ServiceOrders_OrderAVM (Complete) → Done (`Task_AVMSuccessCompletion`) | Automated ✓ | task completed ✓ |  |  |  |
| **Flood Cert** | Y | Auto-done by: task completed: Processing_ServiceOrders_FloodCertificateReview → Done (`Task_FloodReviewCompletionInitial`) | Automated ✓ | task completed ✓ |  |  |  |
| FACT Act Disclosure – eConsent | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Contact Info | Y | — |  |  |  |  |  |
| Loan Audit | Y | — |  |  |  |  |  |
| **FACT Act Disclosure – Ready to Send** | Y | Done → set field CX.DISCLOSEDPRODUCT=NEW; create task Processing_Misc_MailingInitialDisclosures; add condition "Initial Disclosures – Signature Required"; notify; send docs [AVM, Appraisal Report Acknowledgement (AVM)]; notify; send disclosure; notify [[1172]="HELOC"; IsEmpty([3983]); [CX.AVMSENDINITI…] (`Disclosures_HELOCInitialDocs`) | Automated ✓ |  | set field CX.DISCLOSEDPRODUCT=NEW; create task Processing_Misc_MailingInitialDisclosures; add condition "Initial Disclosures – Signature Required"; notify; send docs [AVM, Appraisal Report Acknowledgement (AVM)]; notify; send disclosure; notify [[1172]="HELOC"; IsEmpty([3983]); [CX.AVMSENDINITI…] ✓ |  |  |

## Pull Deed

`Processing_FileSetup_PullDeed` · [pull_deed_v1.xml](../tasks/2_processing/pull_deed/pull_deed_v1.xml) · roadmap `task_063` (completed, Processing)

Created by: `Task_HELOCIntiailDocs2` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Pull Deed from Registry | Y | — |  |  |  |  |  |
| Ownership Screen | Y | — |  |  |  |  |  |
| Trust | N | — |  |  |  |  |  |
| Add Non-Borrowing Owner | N | — |  |  |  |  |  |

## Notice of Incomplete

`Processing_Misc_NoticeOfIncomplete` · [Notice of Incomplete.xml](../tasks/2_processing/misc/Notice of Incomplete.xml) · roadmap `task_002c` (completed, Processing)

Created by: `Task_CreateNOI_15Day`, `Task_CreateNOI_30Day`, `TaskComplete_NOIExtension` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Sub-Task Name | Y | — |  |  |  |  |  |
| Sub-Task Name | Y | — |  |  |  |  |  |
| Dates | Y | — |  |  |  |  |  |
| **Sub-Task Name** | Y | Done → start timer "Notice of Incomplete Warning"; send docs [Notice of Incomplete Letter] (`Disclosures_NOI`) | Automated ✓ |  | start timer "Notice of Incomplete Warning"; send docs [Notice of Incomplete Letter] ✓ |  |  |

## Mailing Initial Disclosures

`Processing_Misc_MailingInitialDisclosures` · [mailing_initial_disclosures_v1.xml](../tasks/2_processing/misc/mailing_initial_disclosures_v1.xml) · roadmap `task_002d` (completed, Processing)

Created by: `OR_Disclosures_HELOCInitialDocs`, `Disclosures_HELOCInitialDocs` · Completed by: `Task_Cancel_Mailed Disclosures`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Sub-Task Name | Y | — |  |  |  |  |  |

## Appraisal Invoice

`Processing_Appraisal_Order` · [order_appraisal_v1.xml](../tasks/2_processing/appraisal/order_appraisal_v1.xml) · roadmap `task_003` (completed, Processing)

Created by: `Task_OrderAppraisalEquity`, `Task_OrderAppraisalFirstMtg`, `Task-OrderAppraisalEquity-AVMFail`, `Task_AVMFailCompletion`, `Task_HELOCIntiailDocs2` · Completed by: `Task_Cancel_AllAdverse` · On create: `Subtask_AppraisalQuote`, `SubtTask_OrderAppraisal1`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Obtain Quote** | N | Done → set field CX.APPRAISALQUOTE=Yes (`Subtask_QuoteComplete`)<br>Added by: task created: Processing_Appraisal_Order [[#1821] >= 1000000 OR [15] = "02535" OR [15] = "0…] (`Subtask_AppraisalQuote`)<br>Added by: task created: Processing_Appraisal_Order [[#2] >= 1000000] (`SubtTask_OrderAppraisal1`) | Automated ✓ |  | set field CX.APPRAISALQUOTE=Yes ✓ |  |  |
| Create Invoice | Y | — |  |  |  |  |  |
| **Send Invoice** | N | Done → notify [[@3142] >= #07/01/2024#] (`Appraisal Invoice Notification`)<br>Added by: file attached: Acknowledgement of Intent to Proceed [([1172] <> "HELOC")] (`SubtTask_OrderAppraisal2`)<br>Added by: task created: Processing_Appraisal_Order [[#1821] >= 1000000 OR [15] = "02535" OR [15] = "0…] (`Subtask_AppraisalQuote`)<br>Added by: task created: Processing_Appraisal_Order [([1172] = "HELOC")] (`SubtTask_OrderAppraisal1`) | Automated ✓ |  | notify [[@3142] >= #07/01/2024#] ✓ |  |  |

## Order Title

`Processing_ServiceOrders_OrderTitle` · [order_title_v1.xml](../tasks/2_processing/title/order_title_v1.xml) · roadmap `task_004` (completed, Processing)

Created by: `Task_PostApprovalEquity` · Completed by: `Task_Cancel_AllAdverse` · On create: `SubTask_TitleOrderEquity`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Order Title Ownership Report – Old Republic** | N | Done → set field CX.TITLEORDERED=today(); condition "Title Report" → Requested (`ConditionUpdate_TitleOrderEquity`)<br>Added by: task created: Processing_ServiceOrders_OrderTitle [(([URLA.X140] <> "LandTrust" AND [URLA.X140] <> "…] (`SubTask_TitleOrderEquity`) | Automated ✓ |  | set field CX.TITLEORDERED=today(); condition "Title Report" → Requested ✓ |  |  |
| **Order Title Ownership Report – Equity Attorney (Trust)** | N | Added by: task created: Processing_ServiceOrders_OrderTitle [(([URLA.X140] = "LandTrust" OR [URLA.X140] = "Liv…] (`SubTask_TitleOrderEquity`) |  |  |  |  |  |
| Obtain Quote – New Deed Prep | N | — |  |  |  |  |  |
| Order Title – Bank Attorney | N | — |  |  |  |  |  |

## Order Flood Certificate

`Processing_ServiceOrders_OrderFloodCertificate` · [order_flood_certificate_v1.xml](../tasks/2_processing/flood_certificate/order_flood_certificate_v1.xml) · roadmap `task_005` (completed, Processing)

Created by: `Task_HELOCIntiailDocs2` · Completed by: `Service - Flood Order`, `Task_Cancel_AllAdverse`, `Service - Flood Order Task`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Resubmit with Supporting Documents | N | — |  |  |  |  |  |
| **Submit Order** | Y | Done → complete task Processing_ServiceOrders_OrderFloodCertificate (Complete); order service [[@3142] >= #03/01/2025#] (`Service - Flood Order Task`) | Automated ✓ |  | complete task Processing_ServiceOrders_OrderFloodCertificate (Complete); order service [[@3142] >= #03/01/2025#] ✓ |  |  |

## ARM Disclosure

`Processing_ARM_Disclosure` · [arm_disclosure_v1.xml](../tasks/2_processing/arm_disclosure/arm_disclosure_v1.xml) · roadmap `task_006` (completed, Processing)

Created by: `Amortization Type Change Notice and Task` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Send Adjustable Rate Disclosure | Y | — |  |  |  |  |  |
| Send Consumer Handbook on Adjustable Rate Mortgage | Y | — |  |  |  |  |  |

## Credit Score Disclosure

`Processing_Disclosures_CreditScoreDisclosure` · [credit_score_disclosure_v1.xml](../tasks/2_processing/credit_score_disclosure/credit_score_disclosure_v1.xml) · roadmap `task_016` (completed, Processing)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| FACT Act All Scores | Y | — |  |  |  |  |  |
| FACT Act Checkboxes | Y | — |  |  |  |  |  |
| FACT Act Key Factors | Y | — |  |  |  |  |  |
| eConsent | Y | — |  |  |  |  |  |
| Contact Info | Y | — |  |  |  |  |  |
| Ready to Send | Y | — |  |  |  |  |  |

## Withdraw Loan

`Processing_Misc_WithdrawLoan` · [withdraw_loan_v1.xml](../tasks/2_processing/misc/withdraw_loan_v1.xml) · roadmap `task_036` (completed, Processing)

Created by: `Withdraw_TaskCreation` · On complete: `Task_Post_Withdraw`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Borrower Withdrawal Documented | Y | — |  |  |  |  |  |
| Withdrawal Date Entered | Y | — |  |  |  |  |  |
| **Send Withdrawal Notice** | Y | Done → notify; send docs [1003 - URLA, Notice to Right to Copy of Appraisal, Withdrawn Letter]; notify; send docs [1003 - URLA, Appraisal Report Acknowledgement (AVM), AVM, Credit Score Disclosure, Notice to Right to Copy of Appraisal, Withdrawn Letter]; notify; send docs [1003 - URLA, Credit Score Disclosure, Withdrawn Letter, AVM, Appraisal Report Acknowledgement (AVM)]; notify; send docs [1003 - URLA, Credit Score Disclosure, Withdrawn Letter]; notify; send docs [Withdrawn Letter, Notice to Right to Copy of Appraisal, Credit Score Disclosure, 1003 - URLA]; notify; send docs [Withdrawn Letter] [IsEmpty([Document.DateReceived.AVM]) and IsEmpty(…] (`Disclosures_Withdrawn_Letter`) | Automated ✓ |  | notify; send docs [1003 - URLA, Notice to Right to Copy of Appraisal, Withdrawn Letter]; notify; send docs [1003 - URLA, Appraisal Report Acknowledgement (AVM), AVM, Credit Score Disclosure, Notice to Right to Copy of Appraisal, Withdrawn Letter]; notify; send docs [1003 - URLA, Credit Score Disclosure, Withdrawn Letter, AVM, Appraisal Report Acknowledgement (AVM)]; notify; send docs [1003 - URLA, Credit Score Disclosure, Withdrawn Letter]; notify; send docs [Withdrawn Letter, Notice to Right to Copy of Appraisal, Credit Score Disclosure, 1003 - URLA]; notify; send docs [Withdrawn Letter] [IsEmpty([Document.DateReceived.AVM]) and IsEmpty(…] ✓ |  |  |

## Send Denial

`Processing_Misc_SendDenial` · [send_denial_v1.xml](../tasks/2_processing/misc/send_denial_v1.xml) · roadmap `task_037` (completed, Processing)

Created by: `Denial_SecondReview` · On create: `Subtask_Denial`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **MA Review Board Form** | N | Added by: task created: Processing_Misc_SendDenial [NOT ([1401] = "MassHousing" and [420] = "Second L…] (`Subtask_Denial`) |  |  |  |  |  |
| **ECOA Right to Copy of Appraisal** | N | Added by: task created: Processing_Misc_SendDenial [IsEmpty([Document.DateOrdered.1003 - URLA])] (`Subtask_Denial`) |  |  |  |  |  |
| **Massachusetts MGL Disclosure** | N | Added by: task created: Processing_Misc_SendDenial [IsEmpty([Document.DateOrdered.1003 - URLA])] (`Subtask_Denial`) |  |  |  |  |  |
| **Credit Score Disclosure** | N | Added by: task created: Processing_Misc_SendDenial [IsEmpty([Document.DateOrdered.1003 - URLA])] (`Subtask_Denial`) |  |  |  |  |  |
| **Mail Counteroffer** | N | Added by: task created: Processing_Misc_SendDenial [(NOT ([1401] = "MassHousing" and [420] = "Second …] (`Subtask_Denial`) |  |  |  |  |  |
| **Send Counteroffer Electronically** | N | Done → notify; notify; send docs [1003 - URLA, Credit Score Disclosure, Statement of Denial]; notify; notify; send docs [Statement of Denial]; notify; notify; send docs [1003 - URLA, Credit Score Disclosure, Notice to Right to Copy of Appraisal, Statement of Denial] [IsEmpty([Document.DateOrdered.1003 - URLA]) AND (…] (`Disclosures_Denial`)<br>Added by: task created: Processing_Misc_SendDenial [NOT((NOT ([1401] = "MassHousing" and [420] = "Sec…] (`Subtask_Denial`) | Automated ✓ |  | notify; notify; send docs [1003 - URLA, Credit Score Disclosure, Statement of Denial]; notify; notify; send docs [Statement of Denial]; notify; notify; send docs [1003 - URLA, Credit Score Disclosure, Notice to Right to Copy of Appraisal, Statement of Denial] [IsEmpty([Document.DateOrdered.1003 - URLA]) AND (…] ✓ |  |  |

## File Closure Documents

`Processing_Misc_FileClosureDocuments` · [file_closure_documents_v1.xml](../tasks/2_processing/misc/file_closure_documents_v1.xml) · roadmap `task_052` (completed, Processing)

Created by: `CounterOffer_Verdict`, `Denial_SecondReview`, `TaskComplete_PostNOI`, `Task_Post_Withdraw`, `Task_DocumentReceipt` · On create: `SubTask_FileClosure_InitialDocs`, `SubTask_FileClosure_InitialDocs1003` · On complete: `Task_TransfertoCold_Adverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Conversation Log** | Y | Auto-done by: file attached: Conversation Log → Done (`Subtask_Complete_ConvoPark`) | Automated ✓ | doc Conversation Log ✓ |  |  |  |
| **Disclosure Tracking** | Y | Auto-done by: file attached: Disclosure Tracking Sheet → Done (`Subtask_Complete_DisclosureTrackingPark`) | Automated ✓ | doc Disclosure Tracking Sheet ✓ |  |  |  |
| **eConsent** | Y | Auto-done by: file attached: eConsent → Done (`Subtask_Complete_eConsetPark`) | Automated ✓ | doc eConsent ✓ |  |  |  |
| **Initial Disclosures** | N | Added by: task created: Processing_Misc_FileClosureDocuments [Not IsEmpty([Document.DateOrdered.USA Patriot Act…] (`SubTask_FileClosure_InitialDocs`)<br>Added by: task created: Processing_Misc_FileClosureDocuments [Not IsEmpty([Document.DateOrdered.USA Patriot Act…] (`SubTask_FileClosure_InitialDocs1003`)<br>Auto-done by: file attached: USA Patriot Act Information Disclosure [([1393] = "Loan Originated" OR [1393] = "Applicat…] → Done (`Subtask_Complete_InitialDisclosurePark`) | Automated ✓ | doc USA Patriot Act Information Disclosure ✓ |  |  |  |
| **1003** | N | Added by: task created: Processing_Misc_FileClosureDocuments [IsEmpty([Document.DateReceived.1003 - URLA])] (`SubTask_FileClosure_InitialDocs1003`)<br>Auto-done by: file attached: 1003 - URLA [([1393] = "Loan Originated" OR [1393] = "Applicat…] → Done (`Subtask_Complete_1003Park`) | Automated ✓ | doc 1003 - URLA ✓ |  |  |  |

## Cancel Flood Certificate

`Processing_Misc_CancelFloodCertificate` · [cancel_flood_certificate_v1.xml](../tasks/2_processing/misc/cancel_flood_certificate_v1.xml) · roadmap `task_053` (completed, Processing)

Created by: `CounterOffer_Verdict`, `Denial_SecondReview`, `TaskComplete_PostNOI`, `Task_Post_Withdraw`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Cancel Flood Certificate on Xactus Website** | Y | Done → set field CX.FLOODCANCEL=today() (`Subtask_CancelFlood`) | Automated ✓ |  | set field CX.FLOODCANCEL=today() ✓ |  |  |

## Notice of Incomplete Expiration

`Processing_Misc_NOIExpiration` · [notice_of_incomplete_expiration_v1.xml](../tasks/2_processing/misc/notice_of_incomplete_expiration_v1.xml) · roadmap `task_060` (completed, Processing)

Created by: `NOI_Expiration_Closure` · Completed by: `NOI_DocsRec_Cancel`, `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **NOI Expired** | Y | Done → create task Processing_Misc_CancelTitle; create task Processing_Misc_CancelPAR; create task Processing_Misc_AppraisalRefund; create task Processing_Misc_CancelFloodCertificate; move to folder Adverse Loans; set field 1393=File Closed for incompleteness; create task Processing_Misc_FileClosureDocuments [Not IsEmpty([CX.TITLEORDERED]) AND IsEmpty([Docum…] (`TaskComplete_PostNOI`)<br>Issue → create task Processing_Misc_NoticeOfIncomplete (`TaskComplete_NOIExtension`) | Automated ✓ |  | create task Processing_Misc_CancelTitle; create task Processing_Misc_CancelPAR; create task Processing_Misc_AppraisalRefund; create task Processing_Misc_CancelFloodCertificate; move to folder Adverse Loans; set field 1393=File Closed for incompleteness; create task Processing_Misc_FileClosureDocuments [Not IsEmpty([CX.TITLEORDERED]) AND IsEmpty([Docum…] ✓ | create task Processing_Misc_NoticeOfIncomplete ✓ |  |

## Appraisal Refund

`Processing_Misc_AppraisalRefund` · [appraisal_refund_v1.xml](../tasks/2_processing/misc/appraisal_refund_v1.xml) · roadmap `task_054` (completed, Processing)

Created by: `CounterOffer_Verdict`, `Denial_SecondReview`, `TaskComplete_PostNOI`, `Task_Post_Withdraw` · On create: `Subtask_AppraisalCancel`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Cancel Appraisal** | N | Issue → complete subtask Appraisal Refund – Scan Letter and Check to Loan File (NA); complete subtask Appraisal Refund – Prepare Refund Check and Letter (NA); complete subtask Appraisal Refund – Mail Check (NA); complete subtask Appraisal Refund – Confirm Appraisal Fee Received (NA) (`Task_AppraisaRefundCancel`)<br>Added by: task created: Processing_Misc_AppraisalRefund [[CX.APPRAISALSTATUS] <> "" AND [CX.APPRAISALSTATU…] (`Subtask_AppraisalCancel`) | Automated ✓ |  |  | complete subtask Appraisal Refund – Scan Letter and Check to Loan File (NA); complete subtask Appraisal Refund – Prepare Refund Check and Letter (NA); complete subtask Appraisal Refund – Mail Check (NA); complete subtask Appraisal Refund – Confirm Appraisal Fee Received (NA) ✓ |  |
| **Confirm Appraisal Fee Received** | Y | Auto-done by: subtask completed: Appraisal Refund – Cancel Appraisal Issue → NA (`Task_AppraisaRefundCancel`) | Automated ✓ | subtask completed ✓ |  |  |  |
| **Prepare Refund Check and Letter** | Y | Auto-done by: subtask completed: Appraisal Refund – Cancel Appraisal Issue → NA (`Task_AppraisaRefundCancel`) | Automated ✓ | subtask completed ✓ |  |  |  |
| **Scan Letter and Check to Loan File** | Y | Auto-done by: subtask completed: Appraisal Refund – Cancel Appraisal Issue → NA (`Task_AppraisaRefundCancel`) | Automated ✓ | subtask completed ✓ |  |  |  |
| **Mail Check** | Y | Auto-done by: subtask completed: Appraisal Refund – Cancel Appraisal Issue → NA (`Task_AppraisaRefundCancel`) | Automated ✓ | subtask completed ✓ |  |  |  |

## Order SSA-89

`Processing_ServiceOrders_OrderSSA89` · [order_ssa89_v1.xml](../tasks/2_processing/ssa89/order_ssa89_v1.xml) · roadmap `task_007` (completed, Processing)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|

## Order Tax Transcripts

`Processing_ServiceOrders_OrderTaxTranscripts` · [order_tax_transcripts_v1.xml](../tasks/2_processing/tax_transcripts/order_tax_transcripts_v1.xml) · roadmap `task_008` (completed, Processing)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|

## Order AVM

`Processing_ServiceOrders_OrderAVM` · [order_avm_v1.xml](../tasks/2_processing/avm/order_avm_v1.xml) · roadmap `task_046` (completed, Processing)

Created by: `Task_HELOCIntiailDocs2` · Completed by: `Task_Cancel_AllAdverse`, `SubTask_AVMFailCompletion`, `SubTask_AVMSuccessCompletion` · On complete: `Task_AVMFailCompletion`, `Task_AVMSuccessCompletion`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Order AVM in Xactus | Y | — |  |  |  |  |  |
| **Save AVM to eFolder** | Y | Issue → add condition "Appraisal"; add condition "Appraisal Report Acknowledgement"; add condition "Appraisal Fee"; set field CX.AVMFAIL=Y; notify; complete task Processing_ServiceOrders_OrderAVM (Issue) (`SubTask_AVMFailCompletion`) | Automated ✓ |  |  | add condition "Appraisal"; add condition "Appraisal Report Acknowledgement"; add condition "Appraisal Fee"; set field CX.AVMFAIL=Y; notify; complete task Processing_ServiceOrders_OrderAVM (Issue) ✓ |  |
| Enter AVM Data | Y | — |  |  |  |  |  |
| **Ready to Send** | Y | Done → complete task Processing_ServiceOrders_OrderAVM (Complete); set field CX.AVMSENDINITIALDOCS=Y (`SubTask_AVMSuccessCompletion`) | Automated ✓ |  | complete task Processing_ServiceOrders_OrderAVM (Complete); set field CX.AVMSENDINITIALDOCS=Y ✓ |  |  |
| **Value Sufficient** | Y | Issue → notify; add condition "Appraisal"; add condition "Appraisal Report Acknowledgement"; add condition "Appraisal Fee"; create task Processing_Appraisal_Order (`Task-OrderAppraisalEquity-AVMFail`) | Automated ✓ |  |  | notify; add condition "Appraisal"; add condition "Appraisal Report Acknowledgement"; add condition "Appraisal Fee"; create task Processing_Appraisal_Order ✓ |  |

## Flood Certificate Review

`Processing_ServiceOrders_FloodCertificateReview` · [flood_certificate_review_v1.xml](../tasks/2_processing/flood_certificate/flood_certificate_review_v1.xml) · roadmap `task_047` (completed, Processing)

Created by: `Task_ServiceOrders_FloodCertificateReview` · Completed by: `Task_Cancel_AllAdverse` · On complete: `Task_FloodReviewCompletionInitial`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Address Matches System** | Y | Done → set field CX.FLOODADDRESSCHECK=now() (`FloodCertificateReview_Address`) | Automated ✓ |  | set field CX.FLOODADDRESSCHECK=now() ✓ |  |  |
| Flood Zone Matches System | Y | — |  |  |  |  |  |
| Life of Loan Coverage Obtained | Y | — |  |  |  |  |  |
| Multiple Livable Dwellings | Y | — |  |  |  |  |  |
| **Sub-Task Name** | N | Issue → create task Processing_ServiceOrders_RecheckFloodCertificate; add condition "Flood Zone Certification" (`Task_FloodRecheck`)<br>Added by: field CX.CURRENTADDRESSSTRING changed [[CX.CURRENTADDRESSSTRING] <> [CX.FLOODADDRESS]] (`Task_FloodCertificateReview_AddressMismatch`) | Automated ✓ |  |  | create task Processing_ServiceOrders_RecheckFloodCertificate; add condition "Flood Zone Certification" ✓ |  |

## Order PAR

`Processing_ServiceOrders_OrderPAR` · [order_par_v1.xml](../tasks/2_processing/service_orders/order_par_v1.xml) · roadmap `task_049` (completed, Processing)

Created by: `Task_PostApprovalEquity` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Place PAR Order** | Y | Done → set field CX.PARORDERED=today(); condition "Property Assessment Report" → Requested [[4002]="Firstimer" OR [CX.TASKPILOT] = "Y"] (`Subtask_PARRequest`) | Automated ✓ |  | set field CX.PARORDERED=today(); condition "Property Assessment Report" → Requested [[4002]="Firstimer" OR [CX.TASKPILOT] = "Y"] ✓ |  |  |

## Recheck Flood

`Processing_ServiceOrders_RecheckFloodCertificate` · [recheck_flood_v1.xml](../tasks/2_processing/service_orders/recheck_flood_v1.xml) · roadmap `task_055` (completed, Processing)

Created by: `Task_FloodRecheck` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|

## Pre-Underwriting Checklist

`Processing_PreUnderwriting_PreUWChecklist` · [pre_uw_checklist_v1.xml](../tasks/2_processing/pre_underwriting_checklist/pre_uw_checklist_v1.xml) · roadmap `task_048` (completed, Processing)

Completed by: `Task_Cancel_AllAdverse` · On create: `Subtask_Processing_PreUndewriting`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Organize eFolder | Y | — |  |  |  |  |  |
| **Run AUS** | N | Added by: task created: Processing_PreUnderwriting_PreUWChecklist [NOT [1401].Contains("Equity") OR NOT ([420] = "Se…] (`Subtask_Processing_PreUndewriting`) |  |  |  |  |  |
| Verify Income | Y | — |  |  |  |  |  |
| Verify Insurance | Y | — |  |  |  |  |  |
| **Verify Mortgage Statements** | Y | Added by: task created: Processing_PreUnderwriting_PreUWChecklist [[1401].Contains("Equity")] (`Subtask_Processing_PreUndewriting`) |  |  |  |  |  |
| **Verify Purpose** | N | Added by: task created: Processing_PreUnderwriting_PreUWChecklist [[1401].Contains("Equity")] (`Subtask_Processing_PreUndewriting`) |  |  |  |  |  |
| **Verify Assets** | N | Added by: task created: Processing_PreUnderwriting_PreUWChecklist [NOT [1401].Contains("Equity") OR NOT ([420] = "Se…] (`Subtask_Processing_PreUndewriting`) |  |  |  |  |  |
| Verify Employment | N | — |  |  |  |  |  |
| **Self-Employed Income** | N | Added by: task created: Processing_PreUnderwriting_PreUWChecklist [[FE0115] = "Y" OR [FE0215] = "Y" OR [FE0315] = "Y…] (`Subtask_Processing_PreUndewriting`) |  |  |  |  |  |
| **Non-Traditional Income** | N | Added by: task created: Processing_PreUnderwriting_PreUWChecklist [[#URLA.X44] > 0] (`Subtask_Processing_PreUndewriting`) |  |  |  |  |  |
| **Rental Income** | N | Added by: task created: Processing_PreUnderwriting_PreUWChecklist [[#FM0120] > 0 OR [#FM0220] > 0 OR [#FM0320] > 0 O…] (`Subtask_Processing_PreUndewriting`) |  |  |  |  |  |

## Order HOI

`Underwriting_PostUnderwriting_OrderHOI` · [order_hoi_v1.xml](../tasks/3_underwriting/post_underwriting/order_hoi_v1.xml) · roadmap `task_015` (completed, Processing)

Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Request Insurance Declaration | Y | — |  |  |  |  |  |

## HOI Review

`Underwriting_PostUnderwriting_HOIReview` · [hoi_review_v1.xml](../tasks/3_underwriting/post_underwriting/hoi_review_v1.xml) · roadmap `task_050` (completed, Processing)

Created by: `Task_HOIReview` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Verify Coverage Amounts | Y | — |  |  |  |  |  |
| Verify Named Insured | Y | — |  |  |  |  |  |
| Verify Lender Named as Mortgagee | Y | — |  |  |  |  |  |
| Verify Address | Y | — |  |  |  |  |  |
| Confirm Policy Effective Date | Y | — |  |  |  |  |  |
| Unit Number | Y | — |  |  |  |  |  |
| Review Deductibles | Y | — |  |  |  |  |  |
| Dwelling Coverage | Y | — |  |  |  |  |  |
| Builders Risk | N | — |  |  |  |  |  |
| Replacement Cost Value | Y | — |  |  |  |  |  |
| Effective Date | Y | — |  |  |  |  |  |
| Policy Term | Y | — |  |  |  |  |  |
| Annual Premium | Y | — |  |  |  |  |  |
| Deductible Amount | Y | — |  |  |  |  |  |
| Mortgagee Clause | Y | — |  |  |  |  |  |
| Binder Signature | Y | — |  |  |  |  |  |
| Name of Trust | N | — |  |  |  |  |  |

## Send Commitment Letter

`Processing_PostUnderwriting_SendCommitmentLetter` · [send_commitment_letter_v1.xml](../tasks/3_underwriting/post_underwriting/send_commitment_letter_v1.xml) · roadmap `task_035` (completed, Processing)

Created by: `Task_SendApproval` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Send Commitment Letter** | Y | Done → send docs [Commitment Letter]; notify; send docs [Commitment Letter-HELOC, Commitment Acknowledgment]; set field CX.UW.APPROVALSENTASK=now(); notify; send docs [Commitment Letter - HELOC, Commitment Acknowledgment] [NOT [1401].Contains("Equity"); ([1172] = "HELOC")…] (`Disclosures_Approval_CL`) | Automated ✓ |  | send docs [Commitment Letter]; notify; send docs [Commitment Letter-HELOC, Commitment Acknowledgment]; set field CX.UW.APPROVALSENTASK=now(); notify; send docs [Commitment Letter - HELOC, Commitment Acknowledgment] [NOT [1401].Contains("Equity"); ([1172] = "HELOC")…] ✓ |  |  |
| **Save to eFolder** | Y | Auto-done by: file attached: Commitment Letter-HELOC [[CX.TASKPILOT] = "Y"AND ([1172] = "HELOC")] → Done (`Task_SendApproval_Save`) | Automated ✓ | doc Commitment Letter-HELOC ✓ |  |  |  |

## Order Appraisal

`Processing_Appraisal_Ordering` · [order_appraisal_ordering_v1.xml](../tasks/2_processing/appraisal/order_appraisal_ordering_v1.xml) · roadmap `task_073` (completed, Processing)

Created by: `Task_OrderAppraisal` · Completed by: `Task_Cancel_AllAdverse` · On create: `SubTask_AppraisalOrder`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Automated Order** | N | Done → condition "Appraisal" → Requested; order service (`Service_AppraisalOrder`)<br>Added by: task created: Processing_Appraisal_Ordering [([ULDD.X220] <> "Y") AND ( ( [CX.APPRAISALQUOTE] …] (`SubTask_AppraisalOrder`) | Automated ✓ |  | condition "Appraisal" → Requested; order service ✓ |  |  |
| **Manual Order** | N | Added by: task created: Processing_Appraisal_Ordering [([ULDD.X220] = "Y") OR NOT ( ( [CX.APPRAISALQUOTE…] (`SubTask_AppraisalOrder`) |  |  |  |  |  |
| **Quote Assignment** | N | Added by: task created: Processing_Appraisal_Ordering [([CX.APPRAISALQUOTE] = "Yes")] (`SubTask_AppraisalOrder`) |  |  |  |  |  |
| Payment Recording | N | — |  |  |  |  |  |
| Order 1004 | N | — |  |  |  |  |  |
| Order 1025 | N | — |  |  |  |  |  |
| Order 1073 | N | — |  |  |  |  |  |

## Order FraudX

`Processing_ServiceOrders_FraudX` · [order_fraudx_v1.xml](../tasks/2_processing/service_orders/order_fraudx_v1.xml) · roadmap `task_074` (completed, Processing)

Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Buyer Agent | N | — |  |  |  |  |  |
| Seller Agent | N | — |  |  |  |  |  |
| Sellers | N | — |  |  |  |  |  |
| **Order** | Y | Done → condition "Fraud & OFAC Review" → Requested; order service (`Service_FraudX`) | Automated ✓ |  | condition "Fraud & OFAC Review" → Requested; order service ✓ |  |  |

## Order SSVN

`Processing_ServiceOrders_SSVN` · [order_ssvn_v1.xml](../tasks/2_processing/service_orders/order_ssvn_v1.xml) · roadmap `task_075` (completed, Processing)

Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Submit Order | Y | — |  |  |  |  |  |

## Redisclose HELOC Disclosure

`Processing_Disclosures_HELOCDisclosure` · [redisclose_heloc_disclosure_v1.xml](../tasks/2_processing/disclosures/redisclose_heloc_disclosure_v1.xml) · roadmap `task_076` (completed, Processing)

Created by: `Task_HELOCImportantTermsRedisclosure` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Revised Disclosure Needed** | Y | Done → set field CX.DISCLOSEDPRODUCT=NEW; notify; send docs [HELOC - Important Terms Disclosure] (`Disclosures_HELOCImportantTerms`) | Automated ✓ |  | set field CX.DISCLOSEDPRODUCT=NEW; notify; send docs [HELOC - Important Terms Disclosure] ✓ |  |  |

## Send Disclosures Alert

`Processing_FileSetup_DislosureAlert` · [send_disclosures_alert_v1.xml](../tasks/2_processing/disclosures/send_disclosures_alert_v1.xml) · roadmap `task_077` (completed, Processing)

Created by: `Task_IntiailDocsAlert` · Completed by: `Task_Cancel_AllAdverse`, `Task_HELOCIntiailDocs`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|

## Send Disclosures Closed End

`Processing_FileSetup_SendDisclosuresClosedEnd` · [send_disclosures_closed_end_v1.xml](../tasks/2_processing/disclosures/send_disclosures_closed_end_v1.xml) · roadmap `task_002e` (completed, Processing)

Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Program Selection | Y | — |  |  |  |  |  |
| Index | N | — |  |  |  |  |  |
| Plan Code | Y | — |  |  |  |  |  |
| Fee Review | Y | — |  |  |  |  |  |
| 1003 – Demographic | Y | — |  |  |  |  |  |
| FACT Act Disclosure – All Scores | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Checkboxes | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Key Factors | Y | — |  |  |  |  |  |
| Home Counseling List | Y | — |  |  |  |  |  |
| Flood Cert | Y | — |  |  |  |  |  |
| FACT Act Disclosure – eConsent | Y | — |  |  |  |  |  |
| FACT Act Disclosure – Contact Info | Y | — |  |  |  |  |  |
| Loan Audit | Y | — |  |  |  |  |  |
| **FACT Act Disclosure – Ready to Send** | Y | Done → send docs [AVM, Appraisal Report Acknowledgement (AVM)]; notify; notify; send disclosure [[CX.AVMSENDINITIALDOCS] = "Y"] (`Disclosures_ClosedEnd`) | Automated ✓ |  | send docs [AVM, Appraisal Report Acknowledgement (AVM)]; notify; notify; send disclosure [[CX.AVMSENDINITIALDOCS] = "Y"] ✓ |  |  |

## Cancel PAR

`Processing_Misc_CancelPAR` · [cancel_par_v1.xml](../tasks/2_processing/misc/cancel_par_v1.xml) · roadmap `task_086` (completed, Processing)

Created by: `CounterOffer_Verdict`, `TaskComplete_PostNOI`, `Task_Post_Withdraw`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Cancel PAR in AppraisalX | Y | — |  |  |  |  |  |

## Cancel Title

`Processing_Misc_CancelTitle` · [cancel_title_v1.xml](../tasks/2_processing/misc/cancel_title_v1.xml) · roadmap `task_087` (completed, Processing)

Created by: `CounterOffer_Verdict`, `TaskComplete_PostNOI`, `Task_Post_Withdraw`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Cancel Title Order with Title Provider | Y | — |  |  |  |  |  |

## Pull Property Field Card

`Processing_FileSetup_PullPropertyFieldCard` · [pull_property_field_card_v1.xml](../tasks/2_processing/pull_property_field_card/pull_property_field_card_v1.xml) · roadmap `task_088` (completed, Processing)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Locate Property Field Card | Y | — |  |  |  |  |  |
| Verify Property Address | Y | — |  |  |  |  |  |

## Underwrite

`Underwriting_Submittal_Underwrite` · [underwrite_v1.xml](../tasks/3_underwriting/submittal/underwrite_v1.xml) · roadmap `task_017` (completed, Underwriting)

Created by: `CounterOffer_Verdict`, `Processing_DenialReviewRequest`, `Task_ExtendApproval_ClosingDate`, `Task_Underwrite_Conditions`, `Task_Underwrite_Expired` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Approve** | Y | Auto-done by: field CX.ADVERSESIGNER1 NOT_EQUAL_TO   [[CX.COUNTEROFFER] = "Y"] → NA (`CounterOffer_FirstReview`)<br>Auto-done by: field CX.ADVERSESIGNER1 NOT_EQUAL_TO   [[CX.COUNTEROFFER] <> "Y"] → NA (`Denial_FirstReview`)<br>Auto-done by: field CX.UW.APPROVAL.LATEST.NAME NOT_EQUAL_TO   [[CX.TASKPILOT] = "Y"AND ([1172] = "HELOC")] → Done (`Task_SendApproval`)<br>Auto-done by: field CX.UW.APPROVAL.LATEST.NAME NOT_EQUAL_TO   [[CX.TASKPILOT] = "Y"] → Done (`Task_UnderwriteCompletion`) | Automated ✓ | field CX.ADVERSESIGNER1; field CX.UW.APPROVAL.LATEST.NAME ✓ |  |  |  |
| **Deny** | Y | Auto-done by: field CX.ADVERSESIGNER1 NOT_EQUAL_TO   [[CX.COUNTEROFFER] = "Y"] → NA (`CounterOffer_FirstReview`)<br>Auto-done by: field CX.ADVERSESIGNER1 NOT_EQUAL_TO   [[CX.COUNTEROFFER] <> "Y"] → Done (`Denial_FirstReview`)<br>Auto-done by: field CX.UW.APPROVAL.LATEST.NAME NOT_EQUAL_TO   [[CX.TASKPILOT] = "Y"AND ([1172] = "HELOC")] → NA (`Task_SendApproval`)<br>Auto-done by: field CX.UW.APPROVAL.LATEST.NAME NOT_EQUAL_TO   [[CX.TASKPILOT] = "Y"] → NA (`Task_UnderwriteCompletion`) | Automated ✓ | field CX.ADVERSESIGNER1; field CX.UW.APPROVAL.LATEST.NAME ✓ |  |  |  |
| **CounterOffer** | Y | Auto-done by: field CX.ADVERSESIGNER1 NOT_EQUAL_TO   [[CX.COUNTEROFFER] = "Y"] → Done (`CounterOffer_FirstReview`)<br>Auto-done by: field CX.ADVERSESIGNER1 NOT_EQUAL_TO   [[CX.COUNTEROFFER] <> "Y"] → NA (`Denial_FirstReview`)<br>Auto-done by: field CX.UW.APPROVAL.LATEST.NAME NOT_EQUAL_TO   [[CX.TASKPILOT] = "Y"AND ([1172] = "HELOC")] → NA (`Task_SendApproval`)<br>Auto-done by: field CX.UW.APPROVAL.LATEST.NAME NOT_EQUAL_TO   [[CX.TASKPILOT] = "Y"] → NA (`Task_UnderwriteCompletion`) | Automated ✓ | field CX.ADVERSESIGNER1; field CX.UW.APPROVAL.LATEST.NAME ✓ |  |  |  |
| **Return to Processor** | Y | Auto-done by: field CX.ADVERSESIGNER1 NOT_EQUAL_TO   [[CX.COUNTEROFFER] = "Y"] → NA (`CounterOffer_FirstReview`)<br>Auto-done by: field CX.ADVERSESIGNER1 NOT_EQUAL_TO   [[CX.COUNTEROFFER] <> "Y"] → NA (`Denial_FirstReview`)<br>Auto-done by: field CX.UW.APPROVAL.LATEST.NAME NOT_EQUAL_TO   [[CX.TASKPILOT] = "Y"AND ([1172] = "HELOC")] → NA (`Task_SendApproval`)<br>Auto-done by: field CX.UW.APPROVAL.LATEST.NAME NOT_EQUAL_TO   [[CX.TASKPILOT] = "Y"] → NA (`Task_UnderwriteCompletion`) | Automated ✓ | field CX.ADVERSESIGNER1; field CX.UW.APPROVAL.LATEST.NAME ✓ |  |  |  |

## Title (Ownership Report)

`Underwriting_Resubmittal_TitleOwnershipReport` · [title_ownership_report_v1.xml](../tasks/3_underwriting/resubmittal/title_ownership_report_v1.xml) · roadmap `task_018` (completed, Underwriting)

Created by: `Title Review` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Customer Name & Property Address | Y | — |  |  |  |  |  |
| Vesting / Ownership | Y | — |  |  |  |  |  |
| Deed Review | Y | — |  |  |  |  |  |
| Mortgages / Liens | Y | — |  |  |  |  |  |
| Judgments | Y | — |  |  |  |  |  |
| Legal Description | Y | — |  |  |  |  |  |

## Review Appraisal

`Underwriting_Resubmittal_ReviewAppraisal` · [review_appraisal_v1.xml](../tasks/3_underwriting/resubmittal/review_appraisal_v1.xml) · roadmap `task_019` (completed, Underwriting)

Created by: `Task_AppraisalReview`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Transfer Appraisal from Value Link** | Y | Auto-done by: file attached: Appraisal → Done (`SubTask_AppraisalTransfer_Complete`) | Automated ✓ | doc Appraisal ✓ |  |  |  |
| **External Review** | Y | Auto-done by: field CUST39FV NOT_EQUAL_TO   [NOT [CUST36FV].Contains("External") AND NOT [617]…] → NA (`SubTask_AppraisalExternal_Complete`)<br>Auto-done by: field CUST39FV NOT_EQUAL_TO   [[CUST36FV].Contains("External") AND NOT [617].Con…] → Done (`SubTask_AppraisalExternal_Complete`) | Automated ✓ | field CUST39FV ✓ |  |  |  |
| **Second Review** | N | Added by: field CUST39FV NOT_EQUAL_TO   [[CUST36FV].Contains("External") AND NOT [617].Con…] (`SubTask_AppraisalExternal_Complete`)<br>Auto-done by: field CUST40FV NOT_EQUAL_TO   [NOT [617].Contains("PAR"); [CUST36FV].Contains("E…] → Done (`Task_AppraisalReview_Complete`) | Automated ✓ | field CUST40FV ✓ |  |  |  |
| **Attach Appraisal Review Form** | N | Added by: field CUST39FV NOT_EQUAL_TO   [[CUST36FV].Contains("External") AND NOT [617].Con…] (`SubTask_AppraisalExternal_Complete`)<br>Auto-done by: file attached: Appraisal Review Form → Done (`SubTask_AppraisalReviewForm_Complete`) | Automated ✓ | doc Appraisal Review Form ✓ |  |  |  |

## Send Appraisal

`Underwriting_Resubmittal_SendAppraisal` · [send_appraisal_v1.xml](../tasks/3_underwriting/resubmittal/send_appraisal_v1.xml) · roadmap `task_057` (completed, Underwriting)

Created by: `Task_AppraisalReview_Complete`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Send Appraisal** | Y | Done → set field 3857=today(); condition "Appraisal Report Acknowledgement" → Requested; send docs [Appraisal, Appraisal Report Acknowledgement (AVM)]; set field 3624=today(); notify; send docs [Appraisal Report Acknowledgement, Appraisal] [Not IsEmpty([3624]) AND [CX.VALUATONTYPE] = "Appr…] (`Disclosures_AppraisalDelivery`) | Automated ✓ |  | set field 3857=today(); condition "Appraisal Report Acknowledgement" → Requested; send docs [Appraisal, Appraisal Report Acknowledgement (AVM)]; set field 3624=today(); notify; send docs [Appraisal Report Acknowledgement, Appraisal] [Not IsEmpty([3624]) AND [CX.VALUATONTYPE] = "Appr…] ✓ |  |  |

## Send AVM

`Underwriting_Resubmittal_SendAVM` · [send_avm_v1.xml](../tasks/3_underwriting/resubmittal/send_avm_v1.xml) · roadmap `task_070` (completed, Underwriting)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Send AVM** | Y | Done → set field 3858=today(); send docs [AVM, Appraisal Report Acknowledgement (AVM)] (`Disclosures_AVM Delivery`) | Automated ✓ |  | set field 3858=today(); send docs [AVM, Appraisal Report Acknowledgement (AVM)] ✓ |  |  |

## Review Appraisal – Second Review

`Underwriting_Resubmittal_ReviewAppraisalSecondReview` · [review_appraisal_second_review_v1.xml](../tasks/3_underwriting/resubmittal/review_appraisal_second_review_v1.xml) · roadmap `task_058` (completed, Underwriting)

Created by: `SubTask_AppraisalExternal_Complete`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Document Second Review** | Y | Auto-done by: field CUST40FV NOT_EQUAL_TO   [NOT [617].Contains("PAR"); NOT [CUST36FV].Contain…] → Done (`Task_AppraisalReview_Complete`) | Automated ✓ | field CUST40FV ✓ |  |  |  |
| Attach Appraisal Review Form | N | — |  |  |  |  |  |

## Review PAR (1st Review)

`Underwriting_Resubmittal_ReviewPAR` · [review_par_v1.xml](../tasks/3_underwriting/resubmittal/review_par_v1.xml) · roadmap `task_051` (completed, Underwriting)

Created by: `Task_PARReview` · Completed by: `Task_Cancel_AllAdverse`, `Task_PARReview2`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Address Verification | Y | — |  |  |  |  |  |
| Visible Deferred Maintenance | Y | — |  |  |  |  |  |
| Occupancy Confirmation | Y | — |  |  |  |  |  |
| Repair Costs | Y | — |  |  |  |  |  |

## Master Property Insurance Review

`Underwriting_PostUnderwriting_CondoMasterReview` · [master_property_insurance_review_v1.xml](../tasks/3_underwriting/post_underwriting/master_property_insurance_review_v1.xml) · roadmap `task_056` (completed, Underwriting)

Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Project Insured Confirmation | Y | — |  |  |  |  |  |
| Unit Within Project Confirmation | Y | — |  |  |  |  |  |
| Policy Effective Before Closing | Y | — |  |  |  |  |  |
| Policy Active at Closing | Y | — |  |  |  |  |  |
| Replacement Cost Coverage Sufficiency | Y | — |  |  |  |  |  |
| Coverage Documentation Present | Y | — |  |  |  |  |  |
| Replacement Cost Loss Settlement | Y | — |  |  |  |  |  |
| Roof Coverage Confirmation | Y | — |  |  |  |  |  |
| ACV Language Review | Y | — |  |  |  |  |  |
| Master Policy Deductible Review | Y | — |  |  |  |  |  |
| Per-Unit Deductible Exists | Y | — |  |  |  |  |  |
| Per-Unit Deductible Amount Review | N | — |  |  |  |  |  |
| Interior Coverage Gap | Y | — |  |  |  |  |  |
| Mortgagee Clause Review | N | — |  |  |  |  |  |

## Send Counteroffer

`Underwriting_Misc_SendCounteroffer` · [send_counteroffer_v1.xml](../tasks/3_underwriting/uw_misc/send_counteroffer_v1.xml) · roadmap `task_034` (completed, Underwriting)

Created by: `CounterOffer_SecondReview` · On create: `Subtask_Counter`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **MA Review Form Board Required** | N | Added by: task created: Underwriting_Misc_SendCounteroffer [[CX.COUNTEROFFER] = "Y"; NOT ([1401] = "MassHousi…] (`Subtask_Counter`) |  |  |  |  |  |
| **Send Counteroffer Electronically** | N | Done → start timer "Counteroffer Closure"; notify; send docs [Counter Offer]; start timer "Counteroffer Warning" (`Disclosures_Counter`)<br>Added by: task created: Underwriting_Misc_SendCounteroffer [[CX.COUNTEROFFER] = "Y"; NOT(NOT ([1401] = "MassH…] (`Subtask_Counter`) | Automated ✓ |  | start timer "Counteroffer Closure"; notify; send docs [Counter Offer]; start timer "Counteroffer Warning" ✓ |  |  |
| **Mail Counteroffer** | N | Added by: task created: Underwriting_Misc_SendCounteroffer [[CX.COUNTEROFFER] = "Y"; NOT ([1401] = "MassHousi…] (`Subtask_Counter`) |  |  |  |  |  |

## Review PAR (2nd Review)

`Underwriting_Resubmittal_ReviewPAR2` · [review_par_second_review_v1.xml](../tasks/3_underwriting/resubmittal/review_par_second_review_v1.xml) · roadmap `task_078` (completed, Underwriting)

Created by: `Task_PARReview2` · Completed by: `Task_Cancel_AllAdverse`, `Task_PARReview3`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Address Verification | Y | — |  |  |  |  |  |
| Visible Deferred Maintenance | Y | — |  |  |  |  |  |
| Occupancy Confirmation | Y | — |  |  |  |  |  |
| Repair Costs | Y | — |  |  |  |  |  |

## Appraisal - Ready in ValueLink Follow Up

`Underwriting_Resubmittal_AppraisalReviewFollow` · [appraisal_ready_in_valuelink_follow_up_v1.xml](../tasks/3_underwriting/resubmittal/appraisal_ready_in_valuelink_follow_up_v1.xml) · roadmap `task_079` (completed, Underwriting)

Created by: `Task_SSRAvailableFollowUp`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|

## Counteroffer Second Review

`Underwriting_Counter_Second` · [counteroffer_second_review_v1.xml](../tasks/3_underwriting/uw_misc/counteroffer_second_review_v1.xml) · roadmap `task_080` (completed, Underwriting)

Created by: `CounterOffer_FirstReview`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Second Look** | Y | Auto-done by: field CX.UW.ADVERSE.SIGNER2.1, CX.UW.ADVERSE.SIGNER2.2, CX.UW.ADVERSE.SIGNER2.3, CX.UW.ADVERSE.SIGNER2.4 changed [[CX.COUNTEROFFER] = "Y"] → Done (`CounterOffer_SecondReview`) | Automated ✓ | field CX.UW.ADVERSE.SIGNER2.1; field CX.UW.ADVERSE.SIGNER2.2; field C… ✓ |  |  |  |

## Denial – Second Look

`Underwriting_Denial_Second` · [denial_second_look_v1.xml](../tasks/3_underwriting/uw_misc/denial_second_look_v1.xml) · roadmap `task_081` (completed, Underwriting)

Created by: `Denial_FirstReview`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Second Look** | Y | Auto-done by: field CX.UW.ADVERSE.SIGNER2.1, CX.UW.ADVERSE.SIGNER2.2, CX.UW.ADVERSE.SIGNER2.3, CX.UW.ADVERSE.SIGNER2.4 changed [[CX.COUNTEROFFER] <> "Y"; [CX.COUNTEROFFER] <> "Y"] → Done (`Denial_SecondReview`) | Automated ✓ | field CX.UW.ADVERSE.SIGNER2.1; field CX.UW.ADVERSE.SIGNER2.2; field C… ✓ |  |  |  |

## Counteroffer Closure

`Underwriting_Misc_CounterofferClosure` · [counteroffer_closure_v1.xml](../tasks/3_underwriting/uw_misc/counteroffer_closure_v1.xml) · roadmap `task_085` (completed, Underwriting)

Created by: `Counteroffer_Expiration_Task`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Counteroffer Declined** | Y | Done → set field 4458=Declined; complete subtask Send Counteroffer – Extension Request (NA); complete subtask Send Counteroffer – Counteroffer Accepted (NA) (`CounterOffer_ClosuerTask_Declined`)<br>Auto-done by: subtask completed: Send Counteroffer – Counteroffer Accepted Done → NA (`CounterOffer_ClosuerTask_Accepted`)<br>Auto-done by: subtask completed: Send Counteroffer – Extension Request Done → NA (`CounterOffer_ClosuerTask_Extend`) | Automated ✓ | subtask completed ✓ | set field 4458=Declined; complete subtask Send Counteroffer – Extension Request (NA); complete subtask Send Counteroffer – Counteroffer Accepted (NA) ✓ |  |  |
| **Counteroffer Accepted** | Y | Done → complete subtask Send Counteroffer – Counteroffer Declined (NA); complete subtask Send Counteroffer – Extension Request (NA); set field 4458=Accepted (`CounterOffer_ClosuerTask_Accepted`)<br>Auto-done by: subtask completed: Send Counteroffer – Counteroffer Declined Done → NA (`CounterOffer_ClosuerTask_Declined`)<br>Auto-done by: subtask completed: Send Counteroffer – Extension Request Done → NA (`CounterOffer_ClosuerTask_Extend`) | Automated ✓ | subtask completed ✓ | complete subtask Send Counteroffer – Counteroffer Declined (NA); complete subtask Send Counteroffer – Extension Request (NA); set field 4458=Accepted ✓ |  |  |
| **Extension Request** | Y | Done → start timer "Counteroffer Closure"; complete subtask Send Counteroffer – Counteroffer Accepted (NA); complete subtask Send Counteroffer – Counteroffer Declined (NA); start timer "Counteroffer Warning" (`CounterOffer_ClosuerTask_Extend`)<br>Auto-done by: subtask completed: Send Counteroffer – Counteroffer Accepted Done → NA (`CounterOffer_ClosuerTask_Accepted`)<br>Auto-done by: subtask completed: Send Counteroffer – Counteroffer Declined Done → NA (`CounterOffer_ClosuerTask_Declined`) | Automated ✓ | subtask completed ✓ | start timer "Counteroffer Closure"; complete subtask Send Counteroffer – Counteroffer Accepted (NA); complete subtask Send Counteroffer – Counteroffer Declined (NA); start timer "Counteroffer Warning" ✓ |  |  |

## Confirm Scheduling

`Closing_PreClosing_Scheduling` · [scheduling_v1.xml](../tasks/4_closing/pre_closing/scheduling_v1.xml) · roadmap `task_022` (completed, Closing)

Created by: `BranchScheduling_CTC` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Obtain Closing Date and Time from Branch** | Y | Auto-done by: field 748 changed [([1172] = "HELOC")] → Done (`BranchScheduling_Complete`) | Automated ✓ | field 748 ✓ |  |  |  |

## Request Closing Disclosure

`Closing_PreClosing_RequestClosingDisclosure` · [request_closing_disclosure_v1.xml](../tasks/4_closing/pre_closing/request_closing_disclosure_v1.xml) · roadmap `task_064` (completed, Closing)

Created by: `Task_ICD_CreateRequest` · On create: `Task_Complete_CD_Request_Equity`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Request CD** | Y | Done → notify; create task Closing_PreClosing_SendInitialClosingDisclosure; set field CX.ICDREQUEST=Y (`Task_ICD_Requested`)<br>Auto-done by: field CUST40FV NOT_EQUAL_TO   [NOT [617].Contains("PAR"); NOT [CUST36FV].Contain…] → Done (`Task_AppraisalReview_Complete`)<br>Auto-done by: field 3977 NOT_EQUAL_TO   [[CX.ICDREQUEST] <> "Y"] → NA (`Task_ICDSentNA`)<br>Auto-done by: task created: Closing_PreClosing_RequestClosingDisclosure [[CX.AVMACCEPTANCE] = "PASS, Sufficient" AND [1401…] → Done (`Task_Complete_CD_Request_Equity`) | Automated ✓ | field CUST40FV; field 3977; task created ✓ | notify; create task Closing_PreClosing_SendInitialClosingDisclosure; set field CX.ICDREQUEST=Y ✓ |  |  |

## Send Initial Closing Disclosure

`Closing_PreClosing_SendInitialClosingDisclosure` · [send_initial_closing_disclosure_v1.xml](../tasks/4_closing/pre_closing/send_initial_closing_disclosure_v1.xml) · roadmap `task_023` (completed, Closing)

Created by: `Task_ICD_Requested` · Completed by: `Task_Cancel_AllAdverse` · On create: `Task_ICD_RequestedSubtasks`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Enter Plan Code** | N | Added by: task created: Closing_PreClosing_SendInitialClosingDisclosure (`Task_ICD_RequestedSubtasks`) |  |  |  |  |  |
| **Reconcile Appraisal Fee** | N | Added by: task created: Closing_PreClosing_SendInitialClosingDisclosure (`Task_ICD_RequestedSubtasks`) |  |  |  |  |  |
| **Enter Closing Date** | N | Added by: task created: Closing_PreClosing_SendInitialClosingDisclosure (`Task_ICD_RequestedSubtasks`) |  |  |  |  |  |
| **Enter CD Issue Date** | N | Added by: task created: Closing_PreClosing_SendInitialClosingDisclosure (`Task_ICD_RequestedSubtasks`) |  |  |  |  |  |
| **Send Initial CD** | Y | Issue → send docs [Closing Disclosure (Alternate), Closing Identification Requirements Form, Closing Employment Certification]; send docs [Closing Disclosure, Closing Employment Certification, Closing Identification Requirements Form] [[LE2.X28] = "Y"; [LE2.X28] = "N"] (`Disclosures_Early_CD`)<br>Auto-done by: field 3977 NOT_EQUAL_TO   → Done (`Task_ICD_Sent`) | Automated ✓ | field 3977 ✓ |  | send docs [Closing Disclosure (Alternate), Closing Identification Requirements Form, Closing Employment Certification]; send docs [Closing Disclosure, Closing Employment Certification, Closing Identification Requirements Form] [[LE2.X28] = "Y"; [LE2.X28] = "N"] ✓ |  |

## Create Closing Package

`Closing_DocPrep_CreateClosingPackage` · [create_closing_package_v1.xml](../tasks/4_closing/doc_prep/create_closing_package_v1.xml) · roadmap `task_025` (completed, Closing)

Created by: `Task_ClosingPackage` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Create Closing Package | Y | — |  |  |  |  |  |

## Closing Setup

`Closing_ClosingSetup_ClosingSetup` · [closing_setup_v1.xml](../tasks/4_closing/closing_setup/closing_setup_v1.xml) · roadmap `task_061` (completed, Closing)

Created by: `BranchScheduling_Complete` · Completed by: `Task_Cancel_AllAdverse` · On complete: `Service_FraudX_Automated`, `Task_ClosingPackage`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Adjust Names | Y | — |  |  |  |  |  |
| Build Vesting | Y | — |  |  |  |  |  |
| Reconcile Fees | Y | — |  |  |  |  |  |
| Enter Plan Code | Y | — |  |  |  |  |  |

## Prepare Payoff Letters

`Closing_ClosingSetup_PreparePayoffLetters` · [prepare_payoff_letters_v1.xml](../tasks/4_closing/closing_setup/prepare_payoff_letters_v1.xml) · roadmap `task_062` (completed, Closing)

Created by: `BranchScheduling_Complete` · Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Reconcile Payoff Letters | Y | — |  |  |  |  |  |
| Save Payoff Letters to eFolder | Y | — |  |  |  |  |  |
| Prepare Envelopes | Y | — |  |  |  |  |  |

## Confirm Funding

`Funding_Funding_ConfirmFunding` · [confirm_funding_v1.xml](../tasks/5_funding/funding/confirm_funding_v1.xml) · roadmap `task_026` (completed, Funding)

Created by: `BranchScheduling_Complete` · Completed by: `Task_Cancel_AllAdverse` · On create: `SubTask_ConfirmFunding_Disbursement`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Add Funding Worksheet to eFolder** | Y | Auto-done by: file attached: Funding/Boarding Documents → Done (`Subtask_FundingGLSheet`) | Automated ✓ | doc Funding/Boarding Documents ✓ |  |  |  |
| **Confirm Funding Amount** | Y | Auto-done by: field CX.FUNDINGCONFIRMED NOT_EQUAL_TO   → Done (`Task_Funding_Funding_Request`) | Automated ✓ | field CX.FUNDINGCONFIRMED ✓ |  |  |  |

## Approve Wire

`Funding_Wire_Approval` · [approve_wire_v1.xml](../tasks/5_funding/funding/approve_wire_v1.xml) · roadmap `task_059` (completed, Funding)

Created by: `Task_Funding_Wire_Request` · Completed by: `Task_Cancel_AllAdverse`, `Task_Funding_Wire_Approval`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|

## Approve Funding

`Funding_Funding_Approval` · [approve_funding_v1.xml](../tasks/5_funding/funding/approve_funding_v1.xml) · roadmap `task_027` (completed, Funding)

Created by: `Task_Funding_Funding_Request` · Completed by: `Task_Cancel_AllAdverse`, `Task_Funding_Funding_Approval`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| FraudX Review | Y | — |  |  |  |  |  |
| Funding Sign Off | Y | — |  |  |  |  |  |

## Fund Loan

`Funding_FundLoan` · [fund_loan_v1.xml](../tasks/5_funding/funding/fund_loan_v1.xml) · roadmap `task_028` (completed, Funding)

Created by: `Task_Funding_Fund_Loan` · Completed by: `Task_Cancel_AllAdverse`, `Task_Funding_Fund_Complete`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|

## Board Loan

`Funding_Boarding_BoardLoan` · [board_loan_v1.xml](../tasks/5_funding/boarding/board_loan_v1.xml) · roadmap `task_029` (completed, Funding)

Created by: `Task_Funding_Fund_Loan`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Board Loan via eLink** | Y | Auto-done by: field CX.EI.UPLOAD.STATUS NOT_EQUAL_TO   [[CX.EI.UPLOAD.STATUS].Contains("Complete")] → Done (`SubTask_CompleteBoarding`) | Automated ✓ | field CX.EI.UPLOAD.STATUS ✓ |  |  |  |

## Credit Refresh

`FundingQC_Credit_Refresh` · [credit-refresh_v1.xml](../tasks/6_pre-closing-qc/funding-qc/credit-refresh_v1.xml) · roadmap `task_009` (completed, Pre-Closing QC)

Completed by: `Task_Cancel_AllAdverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Sub-Task Name | Y | — |  |  |  |  |  |
| Sub-Task Name | Y | — |  |  |  |  |  |

## Fraud X Report

`FundingQC_Fraud_X_Report` · [fraudx_v1.xml](../tasks/6_pre-closing-qc/funding-qc/fraudx_v1.xml) · roadmap `task_010` (completed, Pre-Closing QC)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Appraiser License | N | — |  |  |  |  |  |
| Red Flags | Y | — |  |  |  |  |  |
| All Borrowers | Y | — |  |  |  |  |  |
| Non-Borrowing Owners | N | — |  |  |  |  |  |
| Buyer Agent | N | — |  |  |  |  |  |
| Seller Agent | N | — |  |  |  |  |  |

## Deliver Note

`PostClosingQC_DocumentProcessing_DeliverNote` · [deliver_note_v1.xml](../tasks/7_post-closing-qc/document_processing/deliver_note_v1.xml) · roadmap `task_038` (completed, Post-Closing QC)

Created by: `Task_DeliverNoteMtg`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Deliver to Secondary** | N | Done → set field CX.NOTESENT=Secondary (`Subtask_NoteDelivery_LocationSecondary`) | Automated ✓ |  | set field CX.NOTESENT=Secondary ✓ |  |  |
| Add Loan Number to First Page | N | — |  |  |  |  |  |
| Upload to Identifi | N | — |  |  |  |  |  |
| **Send to Operations** | N | Done → set field CX.NOTESENT=Operations (`Subtask_NoteDelivery_LocationOperations`) | Automated ✓ |  | set field CX.NOTESENT=Operations ✓ |  |  |

## Record Mortgage

`PostClosingQC_DocumentProcessing_RecordMortgage` · [record_mortgage_v1.xml](../tasks/7_post-closing-qc/document_processing/record_mortgage_v1.xml) · roadmap `task_039` (completed, Post-Closing QC)

Created by: `Task_DeliverNoteMtg` · On create: `SubTask_RecordMortgage`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **HELOC Rider** | N | Added by: task created: PostClosingQC_DocumentProcessing_RecordMortgage [([1172] = "HELOC"); ([1172] = "HELOC")] (`SubTask_RecordMortgage`) |  |  |  |  |  |
| **Condo Rider** | N | Added by: task created: PostClosingQC_DocumentProcessing_RecordMortgage [([1172] = "HELOC"); ([1041] = "Condominium" OR [1…] (`SubTask_RecordMortgage`) |  |  |  |  |  |
| **1-to-4 Family Rider** | N | Added by: task created: PostClosingQC_DocumentProcessing_RecordMortgage [([1172] = "HELOC"); [#16] > 1] (`SubTask_RecordMortgage`) |  |  |  |  |  |
| **PUD Rider** | N | Added by: task created: PostClosingQC_DocumentProcessing_RecordMortgage [([1172] = "HELOC"); [1041] = "PUD"] (`SubTask_RecordMortgage`) |  |  |  |  |  |
| **Second Home Rider** | N | Added by: task created: PostClosingQC_DocumentProcessing_RecordMortgage [([1172] = "HELOC"); ([1811] = "SecondHome")] (`SubTask_RecordMortgage`) |  |  |  |  |  |
| Save Exhibit A | Y | — |  |  |  |  |  |
| Scan & Email Package | Y | — |  |  |  |  |  |
| FedEx Package | Y | — |  |  |  |  |  |

## Deliver Mortgage

`PostClosingQC_DocumentProcessing_DeliverMortgage` · [deliver_mortgage_v1.xml](../tasks/7_post-closing-qc/document_processing/deliver_mortgage_v1.xml) · roadmap `task_040` (completed, Post-Closing QC)

Created by: `Task_DeliverNoteMtg`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Deliver to Secondary | N | — |  |  |  |  |  |
| Add Loan Number to First Page | N | — |  |  |  |  |  |
| Upload to Identifi | N | — |  |  |  |  |  |
| Send to Operations | N | — |  |  |  |  |  |

## Transfer to Cold Storage

`PostClosingQC_DocumentProcessing_TransferToColdStorage` · [transfer_to_cold_storage_v1.xml](../tasks/7_post-closing-qc/document_processing/transfer_to_cold_storage_v1.xml) · roadmap `task_043` (completed, Post-Closing QC)

Created by: `Task_ColdStorage_Boarding`, `Task_ColdStorage_PostBoarding`, `Task_TransfertoCold_Adverse`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Transfer to Cold Storage** | Y | Done → set field CX.QC.COMPLETION.DATE=today() (`Subtask_ColdStorage`) | Automated ✓ |  | set field CX.QC.COMPLETION.DATE=today() ✓ |  |  |

## Initial Document Quality Assurance

`QualityAssurance_InitialDocReview` · [initial_document_quality_assurance_v1.xml](../tasks/7_post-closing-qc/initial_doc_qc/initial_document_quality_assurance_v1.xml) · roadmap `task_045` (completed, Post-Closing QC)

Created by: `Task_InitialDocsRec` · Completed by: `Task_Cancel_AllAdverse` · On create: `Task_QualityAssurance_InitialDocReview_1`, `Task_QualityAssurance_InitialDocReview_2`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| eConsent – Completed Prior to Electronic Send | Y | — |  |  |  |  |  |
| eConsent – Docs Mailed if No eConsent | N | — |  |  |  |  |  |
| 1003 – Declarations Complete | Y | — |  |  |  |  |  |
| **1003 – Demographic Info Addendum** | N | Added by: task created: QualityAssurance_InitialDocReview [NOT [1401].Contains("Land") AND [1172]<>"HELOC"] (`Task_QualityAssurance_InitialDocReview_1`)<br>Added by: task created: QualityAssurance_InitialDocReview [NOT [1401].Contains("Land") AND [1172]<>"HELOC"] (`Task_QualityAssurance_InitialDocReview_2`) |  |  |  |  |  |
| **1003 – Demographic Info Addendum Signed** | N | Added by: task created: QualityAssurance_InitialDocReview [[1401].Contains("Land")] (`Task_QualityAssurance_InitialDocReview_1`)<br>Added by: task created: QualityAssurance_InitialDocReview [[1401].Contains("Land")] (`Task_QualityAssurance_InitialDocReview_2`) |  |  |  |  |  |
| **Sub-Task Name** | N | Added by: task created: QualityAssurance_InitialDocReview [[1172]="HELOC"] (`Task_QualityAssurance_InitialDocReview_1`) |  |  |  |  |  |
| ROV Sent with Initial Disclosures | Y | — |  |  |  |  |  |
| Supplemental Consumer Information Form | Y | — |  |  |  |  |  |
| **HELOC Important Terms Disclosure** | N | Added by: task created: QualityAssurance_InitialDocReview [[1172]="HELOC"] (`Task_QualityAssurance_InitialDocReview_1`) |  |  |  |  |  |
| **Your Home Loan Toolkit** | N | Added by: task created: QualityAssurance_InitialDocReview [[1172]<>"HELOC"] (`Task_QualityAssurance_InitialDocReview_2`) |  |  |  |  |  |
| **2015 Settlement Service List** | N | Added by: task created: QualityAssurance_InitialDocReview [NOT [1401].Contains("Equity") AND [14]="RI"] (`Task_QualityAssurance_InitialDocReview_1`)<br>Added by: task created: QualityAssurance_InitialDocReview [NOT [1401].Contains("Equity") AND [14]="RI"] (`Task_QualityAssurance_InitialDocReview_2`) |  |  |  |  |  |
| **Acknowledgement of Intent to Proceed** | N | Added by: task created: QualityAssurance_InitialDocReview [NOT [1401].Contains("Equity")] (`Task_QualityAssurance_InitialDocReview_2`) |  |  |  |  |  |
| CHARM Booklet | N | — |  |  |  |  |  |
| ARM Disclosure | N | — |  |  |  |  |  |
| Credit Score Disclosure Completed | Y | — |  |  |  |  |  |
| Homeowner Counseling List and Acknowledgement | Y | — |  |  |  |  |  |
| Notice of Right to Copy of Appraisal (ECOA) | N | — |  |  |  |  |  |
| Privacy Notice Received | Y | — |  |  |  |  |  |
| Privacy Policy – Opt Out Signed | N | — |  |  |  |  |  |
| **RI Appraisal Fee Notice** | N | Added by: task created: QualityAssurance_InitialDocReview [[2]="RI"] (`Task_QualityAssurance_InitialDocReview_1`) |  |  |  |  |  |
| **RI Right to Copy of Appraisal** | N | Added by: task created: QualityAssurance_InitialDocReview [[2]="RI"] (`Task_QualityAssurance_InitialDocReview_1`) |  |  |  |  |  |
| **RI Notice of Non-Refundability** | N | Added by: task created: QualityAssurance_InitialDocReview [[2]="RI"] (`Task_QualityAssurance_InitialDocReview_1`) |  |  |  |  |  |
| **RI Form 1** | N | Added by: task created: QualityAssurance_InitialDocReview [[2]="RI"] (`Task_QualityAssurance_InitialDocReview_1`) |  |  |  |  |  |
| **RI Form 2** | N | Added by: task created: QualityAssurance_InitialDocReview [[2]="RI"] (`Task_QualityAssurance_InitialDocReview_1`) |  |  |  |  |  |
| **RI Choice of Insurance** | N | Added by: task created: QualityAssurance_InitialDocReview [[2]="RI"] (`Task_QualityAssurance_InitialDocReview_1`) |  |  |  |  |  |
| **RI Title Insurance Disclosure** | N | Added by: task created: QualityAssurance_InitialDocReview [[2]="RI"] (`Task_QualityAssurance_InitialDocReview_1`) |  |  |  |  |  |
| USA Patriot Act Info Disclosure | Y | — |  |  |  |  |  |
| HELOC Booklet | N | — |  |  |  |  |  |

## Document Receipt

`PostClosingQC_DocumentProcessing_DocumentReceipt` · [document_receipt_v1.xml](../tasks/7_post-closing-qc/document_processing/document_receipt_v1.xml) · roadmap `task_065` (completed, Post-Closing QC)

Created by: `Task_DocumentReceipt` · On complete: `Task_ClosingDocumentQA`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **E-Sign Documents** | Y | Auto-done by: file attached: Equal Credit Opportunity Act Notice → Done (`SubTask_DocReceipt_eSignBack`) | Automated ✓ | doc Equal Credit Opportunity Act Notice ✓ |  |  |  |
| **Wet Sign Documents** | Y | Auto-done by: file attached: Home Equity Line of Credit Agreement → Done (`SubTask_DocReceipt_WetSignBack`) | Automated ✓ | doc Home Equity Line of Credit Agreement ✓ |  |  |  |

## Physical Package Receipt

`PostClosingQC_DocumentProcessing_PhysicalPackageReceipt` · [physical_package_receipt_v1.xml](../tasks/7_post-closing-qc/document_processing/physical_package_receipt_v1.xml) · roadmap `task_066` (completed, Post-Closing QC)

Created by: `Task_DocumentReceipt`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| **Receipt of Physical Package** | Y | Done → create task PostClosingQC_DocumentProcessing_RecordMortgage; create task PostClosingQC_DocumentProcessing_DeliverNote; create task PostClosingQC_DocumentProcessing_DeliverMortgage (`Task_DeliverNoteMtg`) | Automated ✓ |  | create task PostClosingQC_DocumentProcessing_RecordMortgage; create task PostClosingQC_DocumentProcessing_DeliverNote; create task PostClosingQC_DocumentProcessing_DeliverMortgage ✓ |  |  |

## Recording Confirmation

`PostClosingQC_DocumentProcessing_RecordingConfirmation` · [recording_confirmation_v1.xml](../tasks/7_post-closing-qc/document_processing/recording_confirmation_v1.xml) · roadmap `task_067` (completed, Post-Closing QC)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Confirm Recording Completed | Y | — |  |  |  |  |  |

## Closing Document Quality Assurance

`PostClosingQC_QualityAssurance_ClosingDocReview` · [closing_document_quality_assurance_v1.xml](../tasks/7_post-closing-qc/quality_assurance/closing_document_quality_assurance_v1.xml) · roadmap `task_068` (completed, Post-Closing QC)

Created by: `Task_ClosingDocumentQA` · On complete: `Task_ColdStorage_PostBoarding`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Check Notary Sections | Y | — |  |  |  |  |  |
| Verify Signatures | Y | — |  |  |  |  |  |
| Confirm Addendums Witnessed | Y | — |  |  |  |  |  |
| Ensure CIP Complete | Y | — |  |  |  |  |  |

## Pre-Closing Document Quality Assurance

`PostClosingQC_QualityAssurance_PreClosingDocReview` · [pre_closing_document_quality_assurance_v1.xml](../tasks/7_post-closing-qc/quality_assurance/pre_closing_document_quality_assurance_v1.xml) · roadmap `task_069` (completed, Post-Closing QC)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Commitment Letters | Y | — |  |  |  |  |  |
| RI HLPA 3 Form | N | — |  |  |  |  |  |
| Counteroffer | N | — |  |  |  |  |  |

## Order HELOC Checks

`PostClosingQC_DocumentProcessing_OrderHELOCChecks` · [order_heloc_checks_v1.xml](../tasks/7_post-closing-qc/document_processing/order_heloc_checks_v1.xml) · roadmap `task_082` (completed, Post-Closing QC)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Order Checks | Y | — |  |  |  |  |  |

## Disbursement Check Receipt

`PostClosingQC_DocumentProcessing_DisbursementCheckReceipt` · [disbursement_check_receipt_v1.xml](../tasks/7_post-closing-qc/document_processing/disbursement_check_receipt_v1.xml) · roadmap `task_083` (completed, Post-Closing QC)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Disbursement Check Received | Y | — |  |  |  |  |  |

## Fill in CIP

`PostClosingQC_DocumentProcessing_FillInCIP` · [fill_in_cip_v1.xml](../tasks/7_post-closing-qc/document_processing/fill_in_cip_v1.xml) · roadmap `task_084` (completed, Post-Closing QC)

Created by: `Task_ClosingDocumentQA`

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| CIP Form | Y | — |  |  |  |  |  |

# Not in roadmap

## Notice of Incomplete

`Processing_Disclosures_NoticeOfIncomplete` · [notice_of_incomplete_v1.xml](../tasks/2_processing/disclosures/notice_of_incomplete_v1.xml)

No rules reference this task.

| Subtask | Auto | Rules today | Intent | Field / doc touched | Done should… | Issue should… | Notes |
|---|---|---|---|---|---|---|---|
| Add Conditions | Y | — |  |  |  |  |  |
| Send Notice of Incomplete | Y | — |  |  |  |  |  |
