-- Drop if exists
DROP DATABASE IF EXISTS airline;
CREATE DATABASE airline DEFAULT CHARACTER SET utf8mb4;
USE airline;

-- --------------------------
-- AIRPORTS
-- --------------------------
CREATE TABLE airports (
  id INT AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(8) NOT NULL UNIQUE,   -- e.g. DEL, BOM
  name VARCHAR(120) NOT NULL,
  city VARCHAR(80) NOT NULL,
  country VARCHAR(80) NOT NULL
);

-- --------------------------
-- FLIGHTS
-- --------------------------
CREATE TABLE flights (
  id INT AUTO_INCREMENT PRIMARY KEY,
  flight_no VARCHAR(16) NOT NULL UNIQUE,   -- e.g. AI-101
  origin_airport_id INT NOT NULL,
  destination_airport_id INT NOT NULL,
  departure_time DATETIME NOT NULL,
  arrival_time DATETIME NOT NULL,
  capacity INT NOT NULL DEFAULT 180,
  price DECIMAL(10,2) NOT NULL DEFAULT 0,
  FOREIGN KEY (origin_airport_id) REFERENCES airports(id) ON DELETE RESTRICT,
  FOREIGN KEY (destination_airport_id) REFERENCES airports(id) ON DELETE RESTRICT,
  CHECK (arrival_time > departure_time),
  CHECK (capacity > 0)
);

-- --------------------------
-- PASSENGERS
-- --------------------------
CREATE TABLE passengers (
  id INT AUTO_INCREMENT PRIMARY KEY,
  first_name VARCHAR(60) NOT NULL,
  last_name VARCHAR(60) NOT NULL,
  email VARCHAR(120) NOT NULL,
  phone VARCHAR(30) NOT NULL
);

-- --------------------------
-- BOOKINGS
-- --------------------------
CREATE TABLE bookings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  flight_id INT NOT NULL,
  passenger_id INT NOT NULL,
  seat_no VARCHAR(8),
  status ENUM('CONFIRMED','CANCELLED') NOT NULL DEFAULT 'CONFIRMED',
  booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (flight_id) REFERENCES flights(id) ON DELETE CASCADE,
  FOREIGN KEY (passenger_id) REFERENCES passengers(id) ON DELETE CASCADE
);

-- --------------------------
-- USERS (Admin / Staff)
-- --------------------------
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('ADMIN','STAFF') NOT NULL DEFAULT 'STAFF',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- --------------------------
-- SEED DATA
-- --------------------------
INSERT INTO airports (code, name, city, country) VALUES
('DEL','Indira Gandhi International Airport','Delhi','India'),
('BOM','Chhatrapati Shivaji Maharaj International Airport','Mumbai','India'),
('BLR','Kempegowda International Airport','Bengaluru','India');

INSERT INTO flights (flight_no, origin_airport_id, destination_airport_id, departure_time, arrival_time, capacity, price)
VALUES
('AI-101', 1, 2, '2025-09-10 08:00:00', '2025-09-10 10:30:00', 180, 5500.00),
('AI-202', 2, 3, '2025-09-11 09:00:00', '2025-09-11 11:45:00', 150, 4500.00),
('AI-303', 3, 1, '2025-09-12 07:15:00', '2025-09-12 09:45:00', 200, 6000.00);
