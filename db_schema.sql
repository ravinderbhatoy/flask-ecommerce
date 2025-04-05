CREATE DATABASE ecommerce
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ecommerce;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,  -- Added for admin functionality
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email)  -- Added for better query performance
) ENGINE=InnoDB;

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    image_url VARCHAR(255),
    stock INT DEFAULT 0,
    category VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category (category)  -- Added for better query performance
) ENGINE=InnoDB;

CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Create admin user (remember to change the password in production)
INSERT INTO users (username, email, password_hash, is_admin) VALUES
('admin', 'admin@example.com', 'admin', TRUE);

-- Make user with ID 1 an admin
UPDATE users SET is_admin = TRUE WHERE id = 1;

-- Sample products
INSERT INTO products (name, description, price, image_url, stock, category) VALUES
('T-shirt', '100% cotton t-shirt', 9.99, 'products/tshirt.webp', 100, 'Clothing'),
('Laptop Bag', 'Waterproof bag for laptops', 39.99, 'products/laptop-bag.webp', 50, 'Accessories'),
('Sneakers', 'Comfortable running shoes', 49.99, 'products/sneakers.webp', 75, 'Footwear');
