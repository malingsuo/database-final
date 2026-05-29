CREATE TABLE IF NOT EXISTS token (
    id          uuid PRIMARY KEY NOT NULL DEFAULT gen_random_uuid(),
    account_id  INTEGER NOT NULL REFERENCES account(id) ON DELETE CASCADE,
    token TEXT NOT NULL UNIQUE
);
