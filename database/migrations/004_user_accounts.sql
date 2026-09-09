-- 冶金平台用户账号表
CREATE SCHEMA IF NOT EXISTS "User";

CREATE TABLE IF NOT EXISTS "User".accounts (
    id              BIGSERIAL PRIMARY KEY,
    username        VARCHAR(20) NOT NULL UNIQUE,
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    real_name       VARCHAR(100),
    organization    VARCHAR(255),
    role            VARCHAR(32) NOT NULL DEFAULT 'user',
    account_type    VARCHAR(32) NOT NULL DEFAULT 'user',
    account_status  VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ,
    CONSTRAINT chk_accounts_role
        CHECK (role IN ('user', 'admin')),
    CONSTRAINT chk_accounts_type
        CHECK (account_type IN ('user', 'admin')),
    CONSTRAINT chk_accounts_status
        CHECK (account_status IN ('active', 'disabled', 'locked'))
);

CREATE INDEX IF NOT EXISTS idx_accounts_email
    ON "User".accounts(LOWER(email));

CREATE INDEX IF NOT EXISTS idx_accounts_status
    ON "User".accounts(account_status);

COMMENT ON TABLE "User".accounts IS
    '平台登录账号：密码仅保存 bcrypt 哈希，不保存明文密码';
