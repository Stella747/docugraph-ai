# DocuGraph compliance report

## 1. breach_notice_hours: High risk

The conflict arises because the Northwind vendor security policy requires notification within 24 hours, while the ACME Cloud MSA requires notification within 72 hours. This inconsistency could lead to legal and reputational risks.

**Recommended action:** Review and harmonize the notification times to ensure compliance with the stricter requirement, which is the 24-hour notification from the Northwind vendor security policy.

**Evidence**
- northwind_vendor_security_policy.pdf, section 5.3, page 3: "Vendors must notify Northwind of any personal data breach within 24 hours of becoming aware of it."
- acme_cloud_msa.pdf, section 9.1, page 2: "Vendor shall notify Customer of any personal data breach within 72 hours of becoming aware of it."

## 2. breach_notice_hours: High risk

The conflict arises because the fictional_data_protection_act_excerpt.pdf mandates reporting within 24 hours, while acme_cloud_msa.pdf requires notification within 72 hours. This discrepancy could lead to non-compliance with either regulation depending on the timing of the breach.

**Recommended action:** Review and harmonize the breach notification timelines to ensure compliance with the stricter requirement, which is the 24-hour reporting as per the fictional_data_protection_act_excerpt.pdf.

**Evidence**
- fictional_data_protection_act_excerpt.pdf, section 12, page 2: "A data controller must report a personal data breach to the Authority within 24 hours of becoming aware of it."
- acme_cloud_msa.pdf, section 9.1, page 2: "Vendor shall notify Customer of any personal data breach within 72 hours of becoming aware of it."

## 3. incident_response_hours: High risk

The conflict arises because the Northwind Vendor Security Policy requires vendors to respond to Critical incidents within 2 hours, while the ACME Cloud MSA specifies a response time of 4 hours. This discrepancy could lead to non-compliance with either policy.

**Recommended action:** Review and harmonize the response time requirements with the more stringent policy, either the Northwind Vendor Security Policy or the ACME Cloud MSA, to ensure compliance.

**Evidence**
- northwind_vendor_security_policy.pdf, section 4.1, page 3: "All vendors must respond to Critical incidents within 2 hours of notification."
- acme_cloud_msa.pdf, section 8.2, page 2: "Vendor shall respond to Critical incidents within 4 hours of notification."

## 4. incident_response_hours: High risk

The conflict arises because the northwind_vendor_security_policy.pdf requires vendors to respond to Critical incidents within 2 hours, which is stricter than the acme_sla_schedule.pdf, which allows a maximum of 8 hours for response to Critical incidents. The recommended action is to align the response time requirement with the acme_sla_schedule.pdf, ensuring that vendors respond to Critical incidents within 8 hours as per the SLA agreement.

**Recommended action:** Align the response time requirement with the acme_sla_schedule.pdf, ensuring that vendors respond to Critical incidents within 8 hours.

**Evidence**
- northwind_vendor_security_policy.pdf, section 4.1, page 3: "All vendors must respond to Critical incidents within 2 hours of notification."
- acme_sla_schedule.pdf, section 1.1, page 1: "Response and resolution targets by incident severity are set out in the table below. | Severity | Response time | Resolution target |
|---|---|---|
| Critical | 8 hours | 24 hours |
| High | 12 hours | 48 hours |
| Medium | 2 business days | 5 business days |"

## 5. incident_response_hours: High risk

The conflict arises because the rule states that the vendor must respond to Critical incidents within 4 hours, but the SLA table specifies that the response time for Critical incidents is 8 hours. This internal inconsistency suggests that the response time requirement in the rule is stricter than the SLA.

**Recommended action:** Review and update the internal response time requirement to align with the SLA, ensuring that the response time for Critical incidents is set to 8 hours as per the SLA.

**Evidence**
- acme_cloud_msa.pdf, section 8.2, page 2: "Vendor shall respond to Critical incidents within 4 hours of notification."
- acme_sla_schedule.pdf, section 1.1, page 1: "Response and resolution targets by incident severity are set out in the table below. | Severity | Response time | Resolution target |
|---|---|---|
| Critical | 8 hours | 24 hours |
| High | 12 hours | 48 hours |
| Medium | 2 business days | 5 business days |"

## 6. cyber_insurance_usd: Medium risk

The conflict arises because the Northwind Vendor Security Policy requires cyber liability insurance of at least USD 5,000,000, while the ACME Cloud MSA requires a minimum of USD 2,000,000. This inconsistency could lead to compliance issues.

**Recommended action:** Review and negotiate a revised cyber liability insurance requirement that aligns with both policies, ensuring it meets or exceeds the higher threshold of USD 5,000,000.

**Evidence**
- northwind_vendor_security_policy.pdf, section 6.2, page 3: "Vendors handling customer data must hold cyber liability insurance of at least USD 5,000,000."
- acme_cloud_msa.pdf, section 12.1, page 2: "Vendor shall maintain cyber liability insurance of not less than USD 2,000,000 throughout the Term."

## 7. cyber_insurance_usd: Medium risk

The conflict arises because the Northwind Vendor Security Policy requires cyber liability insurance of at least USD 5,000,000, while the ACME Insurance Certificate provides coverage of only USD 2,000,000 per claim, which does not meet the requirement. 

**Recommended action:** The vendor should seek cyber liability insurance with a coverage limit of at least USD 5,000,000 to comply with the policy.

**Evidence**
- northwind_vendor_security_policy.pdf, section 6.2, page 3: "Vendors handling customer data must hold cyber liability insurance of at least USD 5,000,000."
- acme_insurance_certificate.pdf, section 1.1, page 1: "Cyber liability coverage limit: USD 2,000,000 per claim."

## 8. insurance_coverage_gap: Medium risk

The conflict arises because the insurance policy period ends on June 30, 2026, while the MSA (Master Service Agreement) is effective from January 1, 2026, and continues for 24 months, ending on December 31, 2027. This creates a coverage gap from July 1, 2026, to December 31, 2026, where the insurance coverage does not align with the MSA's effective period.

**Recommended action:** Renew the insurance policy to ensure continuous coverage until the end of the MSA period.

**Evidence**
- acme_insurance_certificate.pdf, section 2.1, page 1: "Policy period: 1 July 2025 to 30 June 2026. Coverage ends at expiry unless renewed."
- acme_cloud_msa.pdf, section 4.2, page 2: "This Agreement is effective 1 January 2026 and continues for 24 months, ending 31 December 2027."

## 9. payment_terms_days: Low risk

The conflict arises because the payment terms for the invoice are specified as Net 30 in the acme_invoice_0412.pdf, while the MSA (Master Service Agreement) specifies Net 45. This inconsistency could lead to legal disputes if not resolved.

**Recommended action:** Review and negotiate with the customer to determine which payment term to apply, either Net 30 or Net 45, to ensure compliance and avoid potential legal issues.

**Evidence**
- acme_invoice_0412.pdf, section 3, page 1: "Payment is due within 30 days of the invoice date (Net 30)."
- acme_cloud_msa.pdf, section 11.3, page 2: "Customer shall pay undisputed invoices within 45 days of the invoice date (Net 45)."

Finding ID,Subject / Topic,Draft Explanation Direction & Wording,Manual Review Verdict,Notes / Flaws
ISS-001,Cyber Insurance,"Acme holds USD 2,000,000; policy requires USD 5,000,000.",Correct,Clearly states shortfall and direction.
ISS-002,Data Breach Notice,MSA specifies 72 hours; policy requires 24 hours.,Correct,Identifies vendor's looser notice window vs. policy requirement.
ISS-003,Critical Incident SLA,MSA specifies 4 hours; policy requires 2 hours.,Correct,Identifies response target gap accurately.
ISS-004,Payment Terms,MSA specifies Net 45; Invoice 0412 specifies Net 30.,Awkward,"Accurately identifies mismatch, but misattributes direction (refers to invoice as tighter rather than earlier payment pressure)."
ISS-005,Policy Expiry,Insurance policy expires 30 June 2026; contract ends 31 Dec 2027.,Correct,Clearly identifies coverage gap period.
ISS-006,Access Reviews,MSA and policy both specify quarterly access reviews.,Wrong,Surfaced as a violation despite both requiring quarterly reviews (false positive finding).
ISS-007,Data Protection Act,MSA specifies 72 hours; statutory requirement is 24 hours.,Correct,Identifies statutory compliance failure.
ISS-008,SLA Schedule Conflict,Schedule A allows 8-hour response; MSA main body mandates 4 hours.,Correct,Internal document contradiction accurately captured.
ISS-009,SLA Resolution Target,Schedule A specifies 24-hour resolution; no main body target exists.,Awkward,Explanation phrasing is verbose/redundant regarding missing baseline.

7 of 9 explanations judged correct by manual review (7 Correct, 2 Awkward, 1 Wrong / False Positive).