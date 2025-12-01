INSERT INTO members VALUES
(1,'Alice','Brown','alice@mail.com','1998-05-05','Female','111-111'),
(2,'Bob','Smith','bob@mail.com','1995-02-12','Male','222-222'),
(3,'Carol','Jones','carol@mail.com','2000-08-19','Female','333-333');

INSERT INTO trainers VALUES
(1,'Tom','Hill','tom@fit.com','NASM'),
(2,'Lisa','Ray','lisa@fit.com','ACE'),
(3,'Mark','Lee','mark@fit.com','ISSA');

INSERT INTO rooms VALUES
(1,'Studio A',20),
(2,'Studio B',10),
(3,'Studio C',15);

INSERT INTO fitness_goals VALUES
(1,1,'Weight Loss',65,true),
(2,2,'Muscle Gain',80,true),
(3,3,'Endurance',30,true);

INSERT INTO health_metrics VALUES
(1,1,72.5,70,18.2,'2025-10-01'),
(2,1,71.0,68,17.9,'2025-10-15'),
(3,2,85.0,75,22.0,'2025-10-10'),
(4,3,60.0,72,19.5,'2025-10-12');

INSERT INTO trainer_availability VALUES
(1,1,'2025-11-01 09:00','2025-11-01 12:00'),
(2,1,'2025-11-02 13:00','2025-11-02 17:00'),
(3,2,'2025-11-01 10:00','2025-11-01 14:00');

INSERT INTO personal_training_sessions VALUES
(1,1,1,1,'2025-11-01 09:30','2025-11-01 10:30'),
(2,2,2,2,'2025-11-02 13:30','2025-11-02 14:30'),
(3,3,3,3,'2025-11-03 15:00','2025-11-03 16:00');

INSERT INTO group_classes VALUES
(1,'Yoga',2,1,'2025-11-05 10:00',15),
(2,'HIIT',1,2,'2025-11-06 18:00',10),
(3,'Spin',3,3,'2025-11-07 09:00',12);

INSERT INTO class_registrations VALUES
(1,1),
(2,1),
(3,2);

INSERT INTO equipment VALUES
(1,1,'Treadmill','OPERATIONAL'),
(2,1,'Exercise Bike','OPERATIONAL'),
(3,2,'Bench Press','UNDER_REPAIR');

INSERT INTO maintenance_logs VALUES
(1,3,'Loose bolts','OPEN'),
(2,2,'Pedal noise','RESOLVED'),
(3,1,'Screen issue','OPEN');

INSERT INTO invoices VALUES
(1,1,120.00,'PAID'),
(2,2,75.00,'UNPAID'),
(3,3,95.00,'PAID');

INSERT INTO invoice_items VALUES
(1,1,'Membership Fee',100.00),
(2,1,'PT Session',20.00),
(3,2,'Yoga Class',75.00),
(4,3,'Monthly Plan',95.00);

INSERT INTO payments VALUES
(1,1,'CREDIT_CARD','2025-10-20'),
(2,3,'DEBIT','2025-10-22'),
(3,3,'CASH','2025-10-22');
