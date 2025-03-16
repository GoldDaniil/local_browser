DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

--хэшированный пароль для "adminpassword"
INSERT INTO users (username, password, email)
VALUES ('admin', '$2b$12$Cl0spheDYKnk6iRpV2Et7e4ne/AM8ufnN/7nWCAtsLCquYHM.YDyq', 'admin@example.com')
ON CONFLICT DO NOTHING;
