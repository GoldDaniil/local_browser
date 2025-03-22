DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_username VARCHAR(50) NOT NULL,
    receiver_username VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN DEFAULT FALSE
);


--хэшированный пароль для "adminpassword"
INSERT INTO users (username, password, email)
VALUES ('admin', '$2b$12$Cl0spheDYKnk6iRpV2Et7e4ne/AM8ufnN/7nWCAtsLCquYHM.YDyq', 'admin@example.com')
ON CONFLICT DO NOTHING;
