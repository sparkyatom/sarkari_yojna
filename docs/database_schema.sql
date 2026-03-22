-- ═══════════════════════════════════════════════════════════════
-- SarkariYojana — Complete MySQL Database Schema
-- Run this ONCE to set up the database before Django migrations.
--
-- IMPORTANT: After running this file, run Django migrations:
--   python manage.py migrate
-- Django will create its own auth/session/JWT tables automatically.
-- ═══════════════════════════════════════════════════════════════

-- ── MUST BE FIRST: disable strict mode before anything else ──
-- MySQL 8.0 strict mode blocks TEXT/BLOB columns from having DEFAULT values.
-- Setting this at the very top (before USE or CREATE) ensures it applies
-- to the entire session including all table creation statements below.
SET GLOBAL sql_mode = 'NO_ENGINE_SUBSTITUTION';
SET SESSION sql_mode = 'NO_ENGINE_SUBSTITUTION';

-- 1. Create database
CREATE DATABASE IF NOT EXISTS sarkari_yojana_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- 2. Create user and grant privileges
CREATE USER IF NOT EXISTS 'syuser'@'localhost' IDENTIFIED BY 'SY@pass2024';
GRANT ALL PRIVILEGES ON sarkari_yojana_db.* TO 'syuser'@'localhost';
FLUSH PRIVILEGES;

USE sarkari_yojana_db;

-- Re-apply after USE (belt and suspenders)
SET SESSION sql_mode = 'NO_ENGINE_SUBSTITUTION';

-- ═══════════════════════════════════════════════════════════════
-- TABLE: user_profiles
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS user_profiles (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(80)  NOT NULL UNIQUE,
    password        VARCHAR(128) NOT NULL,
    email           VARCHAR(254) NULL,
    mobile          VARCHAR(15)  NULL,

    full_name       VARCHAR(200) NOT NULL,
    date_of_birth   DATE         NULL,
    profile_pic     VARCHAR(255) NULL,
    gender          ENUM('male','female','other') NULL,

    category        ENUM('general','sc','st','obc') NOT NULL DEFAULT 'general',
    marital_status  ENUM('single','married','divorced','widowed') NULL,
    aadhaar         VARCHAR(12)  NULL,
    income_range    VARCHAR(30)  NULL,
    occupation      ENUM('farmer','labour','self_employed','business',
                         'teacher','student','govt_employee',
                         'private_employee','other') NULL,
    state           VARCHAR(30)  NULL,
    has_land        ENUM('no','yes_less_2ha','yes_more_2ha') DEFAULT 'no',

    father_name     VARCHAR(200) NULL,
    mother_name     VARCHAR(200) NULL,
    family_size     SMALLINT UNSIGNED DEFAULT 1,

    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    is_staff        TINYINT(1)   NOT NULL DEFAULT 0,
    is_superuser    TINYINT(1)   NOT NULL DEFAULT 0,
    is_admin        TINYINT(1)   NOT NULL DEFAULT 0,
    last_login      DATETIME     NULL,
    date_joined     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_category  (category),
    INDEX idx_state     (state),
    INDEX idx_occupation(occupation)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ═══════════════════════════════════════════════════════════════
-- TABLE: schemes
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS schemes (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,

    name                VARCHAR(300) NOT NULL,
    ministry            VARCHAR(300) NOT NULL,
    category            ENUM('agriculture','education','housing','health',
                             'women','employment','social','finance') NOT NULL,
    description         TEXT         NOT NULL,
    official_url        VARCHAR(500) NULL,
    icon                VARCHAR(10)  NOT NULL DEFAULT '📋',

    eligible_category   ENUM('all','sc','st','obc','sc_st','sc_st_obc','general')
                            NOT NULL DEFAULT 'all',
    eligible_occupation ENUM('all','farmer','labour','student','self_employed',
                             'business','teacher','other') NOT NULL DEFAULT 'all',
    eligible_gender     ENUM('all','male','female') NOT NULL DEFAULT 'all',
    eligible_state      VARCHAR(50)  NOT NULL DEFAULT 'all',
    min_income          INT UNSIGNED NOT NULL DEFAULT 0,
    max_income          INT UNSIGNED NULL,

    benefit_amount      INT UNSIGNED NOT NULL,
    benefit_period      ENUM('per_year','per_month','one_time','per_installment')
                            NOT NULL DEFAULT 'per_year',

    required_documents  TEXT         NOT NULL,

    last_date           DATE         NOT NULL,
    created_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                            ON UPDATE CURRENT_TIMESTAMP,

    status              ENUM('active','draft','expired') NOT NULL DEFAULT 'active',

    INDEX idx_cat        (category),
    INDEX idx_status     (status),
    INDEX idx_last_date  (last_date),
    INDEX idx_elig_cat   (eligible_category),
    FULLTEXT INDEX ft_search (name, description)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ═══════════════════════════════════════════════════════════════
-- TABLE: upload_history
-- ═══════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS upload_history (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    filename         VARCHAR(255) NOT NULL,
    file_type        ENUM('excel','csv','json') NOT NULL,
    schemes_created  INT UNSIGNED DEFAULT 0,
    schemes_skipped  INT UNSIGNED DEFAULT 0,
    uploaded_by_id   BIGINT NULL,
    uploaded_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    success          TINYINT(1) NOT NULL DEFAULT 1,
    error_log        TEXT,

    FOREIGN KEY (uploaded_by_id) REFERENCES user_profiles(id) ON DELETE SET NULL,
    INDEX idx_uploaded_at (uploaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ═══════════════════════════════════════════════════════════════
-- SEED DATA — 10 real government schemes
-- ═══════════════════════════════════════════════════════════════
INSERT INTO schemes
  (name, ministry, category, description, official_url, icon,
   eligible_category, eligible_occupation, eligible_gender, eligible_state,
   min_income, max_income, benefit_amount, benefit_period,
   required_documents, last_date, status)
VALUES
(
  'PM Kisan Samman Nidhi',
  'Ministry of Agriculture & Farmers Welfare',
  'agriculture',
  'Direct income support of Rs.6,000 per year in 3 equal instalments of Rs.2,000 each to all landholding farmer families across India, credited directly to their bank accounts.',
  'https://pmkisan.gov.in', '🌾',
  'all', 'farmer', 'all', 'all', 0, 250000, 6000, 'per_year',
  'Aadhaar Card\nLand Record (Khatoni / Patta)\nBank Passbook with IFSC\nMobile Number linked to Aadhaar',
  '2026-05-31', 'active'
),
(
  'National Scholarship Portal - SC/ST Post-Matric',
  'Ministry of Social Justice & Empowerment',
  'education',
  'Post-matric scholarship for SC/ST students pursuing higher education. Covers tuition fees, maintenance allowance and book grant to reduce dropout rates.',
  'https://scholarships.gov.in', '🎓',
  'sc_st', 'student', 'all', 'all', 0, 500000, 48000, 'per_year',
  'Aadhaar Card\nCaste Certificate\nIncome Certificate\nBonafide Letter from Institution\nBank Passbook\nPrevious Year Marksheet',
  '2026-04-15', 'active'
),
(
  'Pradhan Mantri Awas Yojana - Gramin',
  'Ministry of Rural Development',
  'housing',
  'Financial assistance for construction of a pucca house. Rs.1.2 lakh in plains and Rs.1.3 lakh in hilly/NE areas. Includes MGNREGS labour support.',
  'https://pmayg.nic.in', '🏠',
  'all', 'all', 'all', 'all', 0, 300000, 120000, 'one_time',
  'Aadhaar Card\nBPL/SECC list inclusion proof\nLand ownership document\nBank Account (Jan Dhan preferred)\nGeotagged photo of plot',
  '2026-06-30', 'active'
),
(
  'Ayushman Bharat - PM-JAY',
  'Ministry of Health & Family Welfare',
  'health',
  'Health cover of Rs.5 lakh per family per year for secondary and tertiary hospitalization at over 10,000 empanelled hospitals across India.',
  'https://pmjay.gov.in', '🏥',
  'all', 'all', 'all', 'all', 0, 500000, 500000, 'per_year',
  'Aadhaar Card\nRation Card\nSECC/BPL list inclusion\nFamily Photo',
  '2026-04-08', 'active'
),
(
  'Kanya Sumangala Yojana',
  'Department of Women & Child Development, UP',
  'women',
  'Financial support in 6 stages from birth to graduation for girl children in Uttar Pradesh to promote education and health.',
  'https://mksy.up.gov.in', '👧',
  'all', 'all', 'female', 'uttar_pradesh', 0, 300000, 15000, 'per_installment',
  'Aadhaar Card\nBirth Certificate (for girl)\nIncome Certificate\nBank Account (mother or girl)\nSchool Enrollment Proof (for later stages)',
  '2026-07-31', 'active'
),
(
  'PM SVANidhi - Street Vendor Working Capital Loan',
  'Ministry of Housing & Urban Affairs',
  'finance',
  'Collateral-free working capital loan for street vendors: Rs.10,000 (1st), Rs.20,000 (2nd), Rs.50,000 (3rd time). Subsidised interest with digital transaction incentives.',
  'https://pmsvanidhi.mohua.gov.in', '🛒',
  'all', 'self_employed', 'all', 'all', 0, 200000, 10000, 'one_time',
  'Aadhaar Card\nVending Certificate or ULB Letter\nBank Account\nVendor Photograph',
  '2026-12-31', 'active'
),
(
  'National Rural Livelihood Mission (DAY-NRLM)',
  'Ministry of Rural Development',
  'employment',
  'Support for rural poor women to form Self Help Groups (SHGs) and access subsidised credit, skill training and market linkages to build sustainable livelihoods.',
  'https://aajeevika.gov.in', '💼',
  'all', 'labour', 'female', 'all', 0, 200000, 15000, 'one_time',
  'Aadhaar Card\nBank Account in SHG name\nSHG Registration Certificate\nIncome Certificate',
  '2026-09-30', 'active'
),
(
  'Pradhan Mantri Ujjwala Yojana 2.0',
  'Ministry of Petroleum & Natural Gas',
  'social',
  'Free LPG connection with first refill and stove to BPL households. Aims to replace indoor air pollution from biomass cooking with clean cooking fuel.',
  'https://pmuy.gov.in', '🔥',
  'all', 'all', 'female', 'all', 0, 200000, 1600, 'one_time',
  'Aadhaar Card\nRation Card (BPL)\nBank Account\nAddress Proof',
  '2026-08-15', 'active'
),
(
  'Post Matric Scholarship for OBC Students',
  'Ministry of Social Justice & Empowerment',
  'education',
  'Financial assistance to OBC students pursuing post-matric education in any government-recognised institution, covering fees and maintenance.',
  'https://scholarships.gov.in', '📚',
  'obc', 'student', 'all', 'all', 0, 300000, 25000, 'per_year',
  'Aadhaar Card\nOBC Certificate (non-creamy layer)\nIncome Certificate (family)\nBonafide from College\nBank Passbook\nMarksheet',
  '2026-05-01', 'active'
),
(
  'Pradhan Mantri Mudra Yojana - Shishu Loan',
  'Ministry of Finance / MUDRA',
  'finance',
  'Collateral-free business loans up to Rs.50,000 (Shishu), Rs.5 lakh (Kishore), Rs.10 lakh (Tarun) for non-farm micro-enterprises and small businesses.',
  'https://mudra.org.in', '💰',
  'all', 'business', 'all', 'all', 0, NULL, 50000, 'one_time',
  'Aadhaar Card\nBusiness Proof or Plan\nBank Account Statement (6 months)\nPAN Card\nCaste Certificate (if applicable)',
  '2026-12-31', 'active'
);

-- ═══════════════════════════════════════════════════════════════
-- VERIFY
-- ═══════════════════════════════════════════════════════════════
SELECT CONCAT('SUCCESS: ', COUNT(*), ' schemes loaded') AS result FROM schemes;
