USE auth;

CREATE TABLE IF NOT EXISTS token (
    id SERIAL PRIMARY KEY,
    token VARCHAR(64) UNIQUE NOT NULL
);

INSERT into token (token) VALUES ('b226c02dc3539324ed52e6d8cd16ab26d6067c6400b51d7d7f4ecacb318cca77')
INSERT into token (token) VALUES ('c7f016d77bd48c99b611d4e381223a8641c177975dc21a5f181539a21c10d14d')