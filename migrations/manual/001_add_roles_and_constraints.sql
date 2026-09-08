BEGIN;

ALTER TABLE "user"
    ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';

DELETE FROM token_block_list older
USING token_block_list newer
WHERE older.jti = newer.jti AND older.id > newer.id;

CREATE UNIQUE INDEX IF NOT EXISTS uq_user_username ON "user" (username);
CREATE UNIQUE INDEX IF NOT EXISTS uq_token_block_list_jti ON token_block_list (jti);

COMMIT;
