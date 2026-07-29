def missing_case_information(case_id, case_type, description):

    missing = []

    if not case_id:
        missing.append("case_id")

    if not case_type:
        missing.append("case_type")

    if not description:
        missing.append("description")

    return missing

