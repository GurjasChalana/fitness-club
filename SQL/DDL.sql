CREATE TABLE members (
    member_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name  VARCHAR(50) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    date_of_birth DATE,
    gender VARCHAR(20),
    phone VARCHAR(30)
);

CREATE TABLE trainers (
    trainer_id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name  VARCHAR(50) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    certification VARCHAR(100)
);

CREATE TABLE rooms (
    room_id SERIAL PRIMARY KEY,
    room_name VARCHAR(50) UNIQUE NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0)
);

CREATE TABLE fitness_goals (
    goal_id SERIAL PRIMARY KEY,
    member_id INT REFERENCES members(member_id) ON DELETE CASCADE,
    goal_type VARCHAR(50) NOT NULL,
    target_value NUMERIC(6,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE health_metrics (
    metric_id SERIAL PRIMARY KEY,
    member_id INT REFERENCES members(member_id) ON DELETE CASCADE,
    weight NUMERIC(5,2),
    heart_rate INT,
    body_fat NUMERIC(5,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE trainer_availability (
    availability_id SERIAL PRIMARY KEY,
    trainer_id INT REFERENCES trainers(trainer_id) ON DELETE CASCADE,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    CHECK (start_time < end_time)
);

CREATE TABLE personal_training_sessions (
    session_id SERIAL PRIMARY KEY,
    member_id INT REFERENCES members(member_id),
    trainer_id INT REFERENCES trainers(trainer_id),
    room_id INT REFERENCES rooms(room_id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    CHECK (start_time < end_time)
);

CREATE TABLE group_classes (
    class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(100) NOT NULL,
    trainer_id INT REFERENCES trainers(trainer_id),
    room_id INT REFERENCES rooms(room_id),
    class_time TIMESTAMP NOT NULL,
    capacity INT NOT NULL CHECK (capacity > 0)
);

CREATE TABLE class_registrations (
    member_id INT REFERENCES members(member_id) ON DELETE CASCADE,
    class_id INT REFERENCES group_classes(class_id) ON DELETE CASCADE,
    PRIMARY KEY (member_id, class_id)
);

CREATE TABLE equipment (
    equipment_id SERIAL PRIMARY KEY,
    room_id INT REFERENCES rooms(room_id),
    equipment_name VARCHAR(100) NOT NULL,
    status VARCHAR(30) DEFAULT 'OPERATIONAL'
);

CREATE TABLE maintenance_logs (
    log_id SERIAL PRIMARY KEY,
    equipment_id INT REFERENCES equipment(equipment_id),
    issue_description TEXT,
    status VARCHAR(30) DEFAULT 'OPEN'
);

CREATE TABLE invoices (
    invoice_id SERIAL PRIMARY KEY,
    member_id INT REFERENCES members(member_id),
    total_amount NUMERIC(8,2) NOT NULL,
    status VARCHAR(30) DEFAULT 'UNPAID'
);

CREATE TABLE invoice_items (
    item_id SERIAL PRIMARY KEY,
    invoice_id INT REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    description TEXT,
    amount NUMERIC(8,2) NOT NULL
);

CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    invoice_id INT REFERENCES invoices(invoice_id),
    payment_method VARCHAR(30),
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
