"""
role_guidelines.py — Dynamic role-specific question guidelines.
This is the brain that makes the interview smart per role.
"""

ROLE_GUIDELINES = {
    "software_tester": """Focus heavily on:
- Test case design and boundary conditions
- Bug lifecycle and severity classification
- API testing (REST, Postman, automated)
- Test automation frameworks (Selenium, Cypress, Pytest, etc.)
- Regression, smoke, sanity, exploratory testing
- Defect reporting and developer communication
- CI/CD integration for test pipelines
- Scenario-based: "Given this bug report, how would you reproduce it?"
Include some analytical and soft skill questions about working with dev teams.""",

    "qa_engineer": """Same as software_tester — focus on:
- ISTQB concepts, test planning, test strategies
- Performance and load testing (JMeter, k6)
- Mobile testing if relevant
- Test metrics and coverage reporting""",

    "backend_developer": """Focus heavily on:
- REST/GraphQL API design and best practices
- Database design, indexing, query optimization (SQL + NoSQL)
- Authentication/authorization (JWT, OAuth2, sessions)
- Caching strategies (Redis, Memcached)
- Scalability, load balancing, microservices
- Error handling, logging, monitoring
- System design questions for mid/senior
- Scenario: "Your API is returning 500 errors under load — how do you debug?"
Include architecture trade-off questions for seniors.""",

    "frontend_developer": """Focus on:
- JavaScript fundamentals (closures, event loop, async/await)
- Framework specifics (React/Vue/Angular — whatever's on their CV)
- State management (Redux, Zustand, Pinia, etc.)
- CSS, responsive design, accessibility
- Performance optimization (lazy loading, code splitting, rendering)
- Browser APIs and cross-browser compatibility
- Testing frontend components
- Scenario: "Your React app re-renders too often — how do you fix it?" """,

    "fullstack_developer": """Balance between frontend and backend:
- API design and integration
- Database interactions from the app layer
- Authentication flows end-to-end
- Deployment and DevOps basics
- State management on frontend
- Performance on both ends
- Scenario: "Build a feature that requires real-time updates — what's your approach?" """,

    "data_scientist": """Focus on:
- Machine learning algorithms and when to use each
- Feature engineering and selection
- Model evaluation metrics (precision, recall, F1, AUC-ROC)
- Overfitting, underfitting, bias-variance tradeoff
- Data cleaning and preprocessing pipelines
- Statistics (hypothesis testing, distributions, p-values)
- Python ML stack (scikit-learn, pandas, numpy, PyTorch/TensorFlow)
- Real-world ML challenges: imbalanced data, missing values, drift
- Scenario: "Your model performs great in training but poorly in production — why?" """,

    "ml_engineer": """Focus on:
- MLOps: model serving, versioning, monitoring
- Training pipelines and orchestration
- Model optimization (quantization, distillation, ONNX)
- Deployment (Docker, Kubernetes, cloud ML services)
- Data pipelines and feature stores
- A/B testing for ML models
- Same core ML knowledge as data scientist""",

    "data_analyst": """Focus on:
- SQL proficiency (complex joins, window functions, CTEs)
- Data visualization (Tableau, Power BI, matplotlib)
- Statistical analysis and interpretation
- Business metrics and KPIs
- Excel/Google Sheets advanced features
- Python or R for analysis
- Communicating insights to non-technical stakeholders
- Scenario: "You notice an unexpected drop in a key metric — how do you investigate?" """,

    "devops_engineer": """Focus on:
- CI/CD pipelines (GitHub Actions, Jenkins, GitLab CI)
- Containerization (Docker, Kubernetes)
- Infrastructure as Code (Terraform, Ansible)
- Cloud platforms (AWS/GCP/Azure — whatever's on CV)
- Monitoring and alerting (Prometheus, Grafana, ELK)
- Incident response and post-mortems
- Security in DevOps (DevSecOps)
- Scenario: "Production is down. Walk me through your incident response process." """,

    "sre": """Same focus as devops_engineer, plus:
- SLOs, SLIs, SLAs and error budgets
- Chaos engineering
- Capacity planning
- Toil reduction automation""",

    "cybersecurity_analyst": """Focus on:
- Threat detection and analysis (SIEM tools)
- Incident response playbooks
- Network security concepts (firewalls, IDS/IPS, VPN)
- OWASP Top 10 vulnerabilities
- Penetration testing concepts
- Risk assessment and vulnerability management
- Social engineering awareness
- Scenario-based: "You detect unusual outbound traffic at 3am — what do you do?"
Include real-world attack scenarios.""",

    "mobile_developer": """Focus on:
- Platform specifics (iOS/Swift/SwiftUI or Android/Kotlin or Flutter — from CV)
- App architecture (MVVM, MVC, Clean Architecture)
- State management on mobile
- API integration and offline handling
- Performance optimization (battery, memory)
- App Store/Play Store submission process
- Push notifications, deep linking
- Scenario: "Your app crashes on launch for 10% of users — how do you debug?" """,

    "embedded_systems_engineer": """Focus on:
- C/C++ proficiency, memory management, pointers
- RTOS concepts (FreeRTOS, Zephyr)
- Hardware interfaces (UART, SPI, I2C, CAN)
- Interrupt handling and timing constraints
- Debugging hardware/software interactions
- Power optimization
- Bootloaders and firmware updates
- Scenario: "Your embedded device randomly resets — how do you diagnose it?" """,

    "cloud_architect": """Focus on:
- Cloud service selection and trade-offs (IaaS vs PaaS vs SaaS)
- Multi-region, high availability design
- Cost optimization strategies
- Security architecture (IAM, VPC, encryption)
- Disaster recovery and backup strategies
- Migration strategies (lift-and-shift vs rearchitect)
- Well-Architected Framework principles
- Scenario: "Design a globally distributed API that handles 1M requests/day." """,

    "database_administrator": """Focus on:
- Performance tuning (indexing, query optimization, explain plans)
- Replication and high availability
- Backup and recovery strategies
- Database security (roles, permissions, encryption)
- Capacity planning
- Both SQL and NoSQL if relevant
- Migration strategies
- Scenario: "A query that took 50ms is now taking 10s — how do you investigate?" """,

    "product_manager": """Focus on:
- Product discovery and user research
- Prioritization frameworks (RICE, MoSCoW, ICE)
- Roadmap planning and stakeholder management
- Metrics and success criteria (OKRs, KPIs)
- Working with engineering and design teams
- Feature trade-off decisions
- Go-to-market strategy
- Behavioral: "Tell me about a feature you killed and why." """,

    "ui_ux_designer": """Focus on:
- Design process (research, ideation, prototyping, testing)
- User research methods (interviews, surveys, usability tests)
- Design systems and component libraries
- Accessibility and inclusive design
- Tools (Figma, Sketch, Adobe XD — from CV)
- Collaboration with developers
- Scenario: "How would you redesign the checkout flow for an e-commerce app?" """,

    "hr_recruiter": """Focus more on soft skills and process:
- Candidate sourcing and screening strategies
- Interviewing techniques and bias reduction
- Onboarding and employee experience
- Conflict resolution between teams
- Employment law basics
- HR metrics (time-to-hire, retention, eNPS)
- Behavioral: "Tell me about a difficult hire you closed and how you did it." """,

    "marketing_specialist": """Focus on:
- Digital marketing channels (SEO, SEM, social, email)
- Campaign planning and budget management
- Analytics and attribution (Google Analytics, UTMs)
- Content strategy and copywriting
- A/B testing campaigns
- CRM tools
- Scenario: "Campaign CTR dropped by 40% — how do you investigate and respond?" """,

    "finance_analyst": """Focus on:
- Financial modeling and forecasting
- Variance analysis and budget management
- Financial statements (P&L, balance sheet, cash flow)
- Excel/financial tools proficiency
- Business valuation methods
- Risk analysis
- Behavioral: "Walk me through a financial model you built and the insights it revealed." """,

    "business_analyst": """Focus on:
- Requirements gathering techniques
- Process mapping and gap analysis
- Stakeholder management
- Use case and user story writing
- Data analysis to support decisions
- Working with both business and technical teams
- Scenario: "A stakeholder wants a feature but hasn't defined success — what do you do?" """,

    "other": """Adapt questions dynamically based on the CV:
- Ask about the core skills and technologies listed
- Mix technical depth with scenario-based questions
- Include project-based questions referencing their actual CV
- Balance between domain knowledge and problem-solving
- Use behavioral questions to understand how they work""",
}

def get_role_guidelines(role: str) -> str:
    """Return role-specific question guidelines. Falls back gracefully."""
    # Try exact match
    if role in ROLE_GUIDELINES:
        return ROLE_GUIDELINES[role]
    # Try partial match
    for key in ROLE_GUIDELINES:
        if key in role or role in key:
            return ROLE_GUIDELINES[key]
    return ROLE_GUIDELINES["other"]
