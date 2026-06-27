"""
competency_planner.py — Builds a structured competency plan from the CV + role.
This is the brain that decides WHAT to test and in what order.
"""

COMPETENCY_PLANS = {
    "software_tester": [
        "test_fundamentals", "test_case_design", "bug_lifecycle",
        "api_testing", "automation_tools", "scenario_testing",
        "communication_with_devs", "analytical_thinking", "behavioral"
    ],
    "qa_engineer": [
        "test_strategy", "test_planning", "automation_frameworks",
        "performance_testing", "bug_lifecycle", "ci_cd_integration",
        "metrics_reporting", "behavioral"
    ],
    "backend_developer": [
        "api_design", "database_knowledge", "authentication_security",
        "performance_optimization", "system_design", "error_handling",
        "scalability", "debugging", "behavioral"
    ],
    "frontend_developer": [
        "javascript_fundamentals", "framework_knowledge", "state_management",
        "css_responsive_design", "performance_optimization", "browser_apis",
        "testing_frontend", "ux_thinking", "behavioral"
    ],
    "fullstack_developer": [
        "api_design", "frontend_framework", "database_knowledge",
        "authentication", "state_management", "deployment_devops",
        "performance", "system_thinking", "behavioral"
    ],
    "data_scientist": [
        "ml_algorithms", "feature_engineering", "model_evaluation",
        "data_preprocessing", "statistics", "ml_stack_tools",
        "real_world_ml_challenges", "communication_of_insights", "behavioral"
    ],
    "ml_engineer": [
        "mlops_deployment", "model_serving", "training_pipelines",
        "model_optimization", "data_pipelines", "ml_fundamentals",
        "ab_testing", "behavioral"
    ],
    "data_analyst": [
        "sql_proficiency", "data_visualization", "statistical_analysis",
        "business_metrics", "python_r_analysis", "data_cleaning",
        "storytelling_with_data", "behavioral"
    ],
    "devops_engineer": [
        "cicd_pipelines", "containerization", "infrastructure_as_code",
        "cloud_platforms", "monitoring_alerting", "incident_response",
        "security_devops", "behavioral"
    ],
    "cybersecurity_analyst": [
        "threat_detection", "incident_response", "network_security",
        "owasp_vulnerabilities", "penetration_testing", "risk_assessment",
        "security_tools", "behavioral"
    ],
    "mobile_developer": [
        "platform_specifics", "app_architecture", "state_management_mobile",
        "api_integration", "performance_mobile", "offline_handling",
        "app_store_deployment", "behavioral"
    ],
    "product_manager": [
        "product_discovery", "prioritization", "stakeholder_management",
        "metrics_kpis", "roadmap_planning", "cross_functional_collaboration",
        "go_to_market", "behavioral"
    ],
    "hr_recruiter": [
        "sourcing_screening", "interviewing_techniques", "onboarding",
        "conflict_resolution", "hr_metrics", "employment_law_basics",
        "communication", "behavioral"
    ],
    "other": [
        "core_domain_knowledge", "practical_experience",
        "problem_solving", "tools_and_technologies",
        "communication", "teamwork", "adaptability", "behavioral"
    ]
}

def get_competency_plan(role: str, detected_technologies: list = None) -> list:
    """Return an ordered competency plan for the role."""
    plan = None
    # Exact match
    if role in COMPETENCY_PLANS:
        plan = list(COMPETENCY_PLANS[role])
    else:
        # Partial match
        for key in COMPETENCY_PLANS:
            if key in role or role in key:
                plan = list(COMPETENCY_PLANS[key])
                break
    if not plan:
        plan = list(COMPETENCY_PLANS["other"])

    # If specific technologies detected, inject them as competencies
    if detected_technologies:
        for tech in detected_technologies[:3]:
            tech_comp = tech.lower().replace(" ", "_") + "_proficiency"
            if tech_comp not in plan:
                plan.insert(-1, tech_comp)  # before behavioral

    return plan
