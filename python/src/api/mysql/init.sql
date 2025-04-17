CREATE USER IF NOT EXISTS 'auth_user'@'%' IDENTIFIED BY 'Auth123';

GRANT ALL PRIVILEGES ON *.* TO 'auth_user'@'%';
CREATE DATABASE IF NOT EXISTS auth;

USE auth;

CREATE TABLE user (id INT NOT NULL AUTO_INCREMENT PRIMARY KEY, email VARCHAR(255) UNIQUE NOT NULL, password VARCHAR(255) NOT NULL);
INSERT IGNORE INTO user (email, password) VALUES ('vacrecco97@gmail.com', 'valerio');
INSERT IGNORE INTO user (email, password) VALUES ('ludovix9070@gmail.com', 'ludovico');
INSERT IGNORE INTO user (email, password) VALUES ('filesurfer97@gmail.com', 'filesurfer');