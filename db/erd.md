
erDiagram
    PARTY ||--o{ CASE : "files (as client)"
    PARTY ||--o{ CONFLICT_CHECK : "matched_against"
    CASE ||--o{ CONFLICT_CHECK : "undergoes"
    CASE ||--o{ CASE_ASSIGNMENT : "results_in"
    CASE ||--o{ DOCUMENT : "has"
    LAWYER ||--o{ CASE_ASSIGNMENT : "assigned_to"
    STAFF ||--o{ CONFLICT_CHECK : "resolves"
    STAFF ||--o{ CASE_ASSIGNMENT : "assigns"
    STAFF ||--o{ CASE : "reviews"
    STAFF ||--o{ AUDIT_LOG : "generates"
    STAFF ||--o{ BATCH_JOB : "triggers"
    CASE_TYPE_POLICY ||--o{ CASE : "governs"
    CASE ||--o{ AUDIT_LOG : "referenced_in"
    LAWYER ||--o{ AUDIT_LOG : "referenced_in"
    BATCH_JOB ||--o{ CONFLICT_CHECK : "produces"

    PARTY {
        uuid party_id PK
        string full_name
        string party_type "client | opposing_party"
        string national_id_or_reg_no
        string email
        string phone
        datetime created_at
    }

    CASE_TYPE_POLICY {
        uuid policy_id PK
        string case_type "civil | criminal | corporate | family | IP"
        int min_seniority_required
        json required_documents
        bool auto_reject_if_conflict
    }

    CASE {
        uuid case_id PK
        uuid client_party_id FK
        uuid policy_id FK
        string description
        string status "submitted | conflict_check_pending | conflict_clear | conflict_flagged | under_review | accepted | rejected | assigned"
        decimal estimated_value
        string jurisdiction
        string decision_reason
        uuid decided_by FK
        datetime decision_at
        datetime submitted_at
        datetime updated_at
    }

    DOCUMENT {
        uuid document_id PK
        uuid case_id FK
        string file_name
        string file_type
        string storage_path
        string upload_status "pending | verified | missing"
        datetime uploaded_at
    }

    CONFLICT_CHECK {
        uuid check_id PK
        uuid case_id FK
        uuid batch_job_id FK
        uuid matched_party_id FK
        string match_type "exact_match | fuzzy_name_match | related_party"
        decimal confidence_score
        string resolution "unresolved | confirmed_conflict | false_positive"
        uuid resolved_by FK
        datetime checked_at
    }

    BATCH_JOB {
        uuid job_id PK
        uuid triggered_by FK
        string job_type "bulk_conflict_check | other"
        int total_items
        int processed_items
        string status "running | completed | failed"
        datetime started_at
        datetime completed_at
    }

    LAWYER {
        uuid lawyer_id PK
        string full_name
        string bar_number
        string specialization
        string seniority_level "junior | associate | senior | partner"
        int current_caseload
        int max_caseload
        string status "active | on_leave | inactive"
    }

    CASE_ASSIGNMENT {
        uuid assignment_id PK
        uuid case_id FK
        uuid lawyer_id FK
        uuid assigned_by FK
        string role_on_case "lead | support"
        datetime assigned_at
    }

    STAFF {
        uuid staff_id PK
        string full_name
        string role "receptionist | senior_associate | partner | admin"
        string email
        bool active
    }

    AUDIT_LOG {
        uuid log_id PK
        uuid actor_staff_id FK
        string action
        string entity_type
        uuid entity_id
        string outcome "success | denied | error"
        datetime timestamp
    }
