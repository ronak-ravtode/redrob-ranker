# Coarse Filter Recall Audit

- Normal coarse survivors: 906
- Wider-filter survivors: 23927
- Additional candidates under wider filter: 23021

## Findings
- The normal filter retains relevant titles and explicit career-history evidence, and ignores skill-only candidates.
- The wider lexical audit found additional candidates with broader relevance language, but these were not permanently admitted because runtime and top-200 quality need manual review before widening.
- No candidate-ID-specific fixes were applied.

## Sample rejected by normal filter but caught by wider terms
| candidate_id | title | evidence preview |
| --- | --- | --- |
| CAND_0000002 | Operations Manager | operations manager customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering  |
| CAND_0000005 | Accountant | accountant business analyst at a consulting firm, working primarily with retail and cpg clients. conducted business diagnostics, process re-engineering work, and digital transforma |
| CAND_0000007 | Civil Engineer | civil engineer brand design and creative direction at a consumer-products company. owned brand identity (logo, visual system, typography), packaging design, and digital creative ac |
| CAND_0000010 | Data Engineer | data engineer mixed data science and analytics-engineering role at a marketing-analytics startup. spent maybe 30% of my time on lightweight ml (clustering, classification, churn pr |
| CAND_0000013 | Civil Engineer | civil engineer customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and  |
| CAND_0000016 | Accountant | accountant enterprise sales of cloud software solutions into the mid-market segment. carried a $1.8m arr quota and consistently delivered against it across the last three years. ow |
| CAND_0000017 | Accountant | accountant customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and the  |
| CAND_0000021 | Project Manager | project manager brand design and creative direction at a consumer-products company. owned brand identity (logo, visual system, typography), packaging design, and digital creative a |
| CAND_0000026 | Graphic Designer | graphic designer customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering an |
| CAND_0000029 | Business Analyst | business analyst marketing leadership role at a b2b saas company. owned the demand-generation function — content marketing, paid acquisition, seo, email nurture. built and managed  |
| CAND_0000041 | Operations Manager | operations manager customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering  |
| CAND_0000045 | Project Manager | project manager enterprise sales of cloud software solutions into the mid-market segment. carried a $1.8m arr quota and consistently delivered against it across the last three year |
| CAND_0000046 | Mechanical Engineer | mechanical engineer customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering |
| CAND_0000053 | Graphic Designer | graphic designer customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering an |
| CAND_0000064 | Accountant | accountant business analyst at a consulting firm, working primarily with retail and cpg clients. conducted business diagnostics, process re-engineering work, and digital transforma |
| CAND_0000065 | Project Manager | project manager business analyst at a consulting firm, working primarily with retail and cpg clients. conducted business diagnostics, process re-engineering work, and digital trans |
| CAND_0000066 | Content Writer | content writer customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering and  |
| CAND_0000069 | Business Analyst | business analyst enterprise sales of cloud software solutions into the mid-market segment. carried a $1.8m arr quota and consistently delivered against it across the last three yea |
| CAND_0000073 | Project Manager | project manager business analyst at a consulting firm, working primarily with retail and cpg clients. conducted business diagnostics, process re-engineering work, and digital trans |
| CAND_0000076 | Project Manager | project manager senior accounting role at a mid-sized company — month-end close, financial reporting, statutory compliance (gaap / ind-as), and tax filings. owned the gl, fixed-ass |
| CAND_0000082 | Data Analyst | data analyst implemented streaming data pipelines on kafka and spark streaming for a real-time user-activity processing platform. designed the schema-registry integration, the wate |
| CAND_0000083 | Graphic Designer | graphic designer enterprise sales of cloud software solutions into the mid-market segment. carried a $1.8m arr quota and consistently delivered against it across the last three yea |
| CAND_0000084 | Marketing Manager | marketing manager senior accounting role at a mid-sized company — month-end close, financial reporting, statutory compliance (gaap / ind-as), and tax filings. owned the gl, fixed-a |
| CAND_0000098 | Business Analyst | business analyst customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering an |
| CAND_0000102 | Operations Manager | operations manager customer support team lead at a saas product. managed a team of 8 support agents handling tier-1 and tier-2 tickets; owned the escalation process to engineering  |
