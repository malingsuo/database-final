CREATE TABLE IF NOT EXISTS token (
    id          UUID PRIMARY KEY NOT NULL DEFAULT gen_random_uuid(),
    account_id  UUID NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE
);
