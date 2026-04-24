CREATE DATABASE IF NOT EXISTS bike_pooling_2;
USE bike_pooling_2;

-- =====================================
-- USERS TABLE
-- =====================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone VARCHAR(15),
    has_bike BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================
-- RIDES TABLE (CORE SYSTEM)
-- =====================================
CREATE TABLE rides (
    ride_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,

    start_location VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,

    start_lat DOUBLE,
    start_lng DOUBLE,
    dest_lat DOUBLE,
    dest_lng DOUBLE,

    ride_time DATETIME NOT NULL,

    seats INT DEFAULT 1,

    status ENUM(
        'searching',
        'matched',
        'ongoing',
        'completed',
        'cancelled'
    ) DEFAULT 'searching',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- =====================================
-- RIDE REQUESTS TABLE
-- =====================================
CREATE TABLE ride_requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ride_id INT NOT NULL,

    status ENUM('pending','accepted','rejected') DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (ride_id) REFERENCES rides(ride_id) ON DELETE CASCADE
);

-- =====================================
-- BOOKINGS TABLE (FINAL MATCH ENGINE)
-- =====================================
CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,

    driver_id INT NOT NULL,
    passenger_id INT NOT NULL,
    ride_id INT NOT NULL,

    fare DECIMAL(10,2) DEFAULT 0,

    status ENUM(
        'matched',
        'accepted',
        'ongoing',
        'completed',
        'cancelled'
    ) DEFAULT 'matched',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (driver_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (passenger_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (ride_id) REFERENCES rides(ride_id) ON DELETE CASCADE
);