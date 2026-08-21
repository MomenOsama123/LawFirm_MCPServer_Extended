INSERT INTO staff (staff_id, full_name, role, email, active) VALUES
('staff-001', 'Mona Adel', 'receptionist', 'mona@lawfirm.eg', 1),
('staff-002', 'Nourhan Samir', 'senior_associate', 'nourhan@lawfirm.eg', 1),
('staff-003', 'Karim El-Sayed', 'partner', 'karim@lawfirm.eg', 1),
('staff-004', 'Laila Mostafa', 'admin', 'laila@lawfirm.eg', 1);

INSERT INTO case_type_policy
(policy_id, case_type, min_seniority_required, required_documents, auto_reject_if_conflict)
VALUES
('policy-civil', 'civil', 1, '["national_id","claim_summary"]', 0),
('policy-criminal', 'criminal', 3, '["national_id","police_report"]', 1),
('policy-corporate', 'corporate', 2, '["national_id","company_registration"]', 0),
('policy-ip', 'IP', 2, '["national_id","trademark_filing"]', 0);

INSERT INTO party
(party_id, full_name, party_type, national_id_or_reg_no, email, phone)
VALUES
('party-001', 'Ahmed Reda', 'client', '29001011234567', 'ahmed@example.com', '01011111111'),
('party-002', 'Sara Tarek', 'client', '29202021234567', 'sara@example.com', '01022222222'),
('party-003', 'Mahmoud Adel Hussein', 'opposing_party', '28808081234567', NULL, NULL),
('party-004', 'Mahmoud A. Hussein', 'client', '28808081234567', 'mahmoud@example.com', '01033333333');

INSERT INTO lawyer
(lawyer_id, full_name, bar_number, specialization, seniority_level, current_caseload, max_caseload, status)
VALUES
('lawyer-001', 'Dina Farouk', 'BAR-1001', 'civil', 'junior', 2, 8, 'active'),
('lawyer-002', 'Omar Khaled', 'BAR-1002', 'criminal', 'senior', 3, 6, 'active'),
('lawyer-003', 'Sara Nabil', 'BAR-1003', 'corporate', 'partner', 6, 6, 'active'),
('lawyer-004', 'Rania Adel', 'BAR-1004', 'IP', 'senior', 1, 6, 'active');

INSERT INTO batch_job
(job_id, triggered_by, job_type, total_items, processed_items, status)
VALUES
('batch-001', 'staff-003', 'bulk_conflict_check', 20, 20, 'completed');

INSERT INTO "case"
(case_id, client_party_id, policy_id, description, status, estimated_value, jurisdiction, decision_reason, decided_by)
VALUES

('case-001',
'party-001',
'policy-civil',
'Residential lease dispute.',
'accepted',
50000,
'Giza',
'Requirements satisfied.',
'staff-002'),

('case-002',
'party-002',
'policy-corporate',
'Supply contract dispute.',
'under_review',
250000,
'Cairo',
NULL,
NULL),

('case-003',
'party-004',
'policy-criminal',
'Financial fraud investigation.',
'conflict_flagged',
900000,
'Alexandria',
NULL,
NULL),

('case-004',
'party-001',
'policy-ip',
'Trademark infringement.',
'assigned',
150000,
'Cairo',
'Approved.',
'staff-002');

INSERT INTO document
(document_id, case_id, file_name, file_type, storage_path, upload_status)
VALUES
('doc-001', 'case-001', 'lease.pdf', 'pdf', '/storage/case1/lease.pdf', 'verified'),
('doc-002', 'case-002', 'contract.pdf', 'pdf', '/storage/case2/contract.pdf', 'verified'),
('doc-003', 'case-003', 'police_report.pdf', 'pdf', '/storage/case3/police.pdf', 'missing'),
('doc-004', 'case-004', 'trademark.pdf', 'pdf', '/storage/case4/trademark.pdf', 'verified');


INSERT INTO conflict_check
(check_id, case_id, batch_job_id, matched_party_id, match_type, confidence_score, resolution)
VALUES
('check-001',
'case-003',
'batch-001',
'party-003',
'fuzzy_name_match',
0.87,
'unresolved');

INSERT INTO case_assignment
(assignment_id, case_id, lawyer_id, assigned_by, role_on_case)
VALUES
('assign-001',
'case-004',
'lawyer-001',
'staff-002',
'lead');

INSERT INTO audit_log
(log_id, actor_staff_id, action, entity_type, entity_id, outcome)
VALUES
('audit-001',
'staff-002',
'accept_case',
'case',
'case-001',
'success'),

('audit-002',
'staff-002',
'assign_lawyer',
'case',
'case-004',
'success');
