import os
import sys
from datetime import datetime, date
from decimal import Decimal

from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from db import engine, get_session
from models import (
    Base,
    ClassRegistration,
    Equipment,
    FitnessGoal,
    GroupClass,
    HealthMetric,
    Invoice,
    InvoiceItem,
    MaintenanceLog,
    Member,
    Payment,
    PersonalTrainingSession,
    Room,
    Trainer,
    TrainerAvailability,
)

def seed(reset: bool = True):
    load_dotenv()
    if reset:
        print("Resetting database (drop/create)...")
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    with get_session() as session:
        if session.query(Member).count() > 0:
            print("Database already seeded; skipping.")
            # Already seeded
            return
        print("Seeding demo data...")

        trainers = [
            Trainer(first_name="Tom", last_name="Hill", username="tom", email="tom@fit.com", password_hash=generate_password_hash("password"), certification="NASM"),
            Trainer(first_name="Lisa", last_name="Ray", username="lisa", email="lisa@fit.com", password_hash=generate_password_hash("password"), certification="ACE"),
            Trainer(first_name="Mark", last_name="Lee", username="mark", email="mark@fit.com", password_hash=generate_password_hash("password"), certification="ISSA"),
        ]
        session.add_all(trainers)
        session.flush()

        members = [
            Member(first_name="Alice", last_name="Brown", username="alice", email="alice@mail.com", password_hash=generate_password_hash("password"), date_of_birth=date(1998, 5, 5), gender="Female", phone="111-111"),
            Member(first_name="Bob", last_name="Smith", username="bob", email="bob@mail.com", password_hash=generate_password_hash("password"), date_of_birth=date(1995, 2, 12), gender="Male", phone="222-222"),
            Member(first_name="Carol", last_name="Jones", username="carol", email="carol@mail.com", password_hash=generate_password_hash("password"), date_of_birth=date(2000, 8, 19), gender="Female", phone="333-333"),
        ]
        session.add_all(members)
        session.flush()

        rooms = [
            Room(room_name="Studio A", capacity=20),
            Room(room_name="Studio B", capacity=10),
            Room(room_name="Studio C", capacity=15),
        ]
        session.add_all(rooms)
        session.flush()

        session.add_all(
            [
                FitnessGoal(member_id=members[0].member_id, goal_type="Weight Loss", target_value=Decimal("65.0"), is_active=True),
                FitnessGoal(member_id=members[1].member_id, goal_type="Muscle Gain", target_value=Decimal("80.0"), is_active=True),
                FitnessGoal(member_id=members[2].member_id, goal_type="Endurance", target_value=Decimal("30.0"), is_active=True),
            ]
        )

        session.add_all(
            [
                HealthMetric(member_id=members[0].member_id, weight=Decimal("72.5"), heart_rate=70, body_fat=Decimal("18.2"), recorded_at=datetime(2025, 10, 1)),
                HealthMetric(member_id=members[0].member_id, weight=Decimal("71.0"), heart_rate=68, body_fat=Decimal("17.9"), recorded_at=datetime(2025, 10, 15)),
                HealthMetric(member_id=members[1].member_id, weight=Decimal("85.0"), heart_rate=75, body_fat=Decimal("22.0"), recorded_at=datetime(2025, 10, 10)),
                HealthMetric(member_id=members[2].member_id, weight=Decimal("60.0"), heart_rate=72, body_fat=Decimal("19.5"), recorded_at=datetime(2025, 10, 12)),
            ]
        )

        session.add_all(
            [
                TrainerAvailability(trainer_id=trainers[0].trainer_id, start_time=datetime(2025, 11, 1, 9, 0), end_time=datetime(2025, 11, 1, 12, 0)),
                TrainerAvailability(trainer_id=trainers[0].trainer_id, start_time=datetime(2025, 11, 2, 13, 0), end_time=datetime(2025, 11, 2, 17, 0)),
                TrainerAvailability(trainer_id=trainers[1].trainer_id, start_time=datetime(2025, 11, 1, 10, 0), end_time=datetime(2025, 11, 1, 14, 0)),
            ]
        )

        session.add_all(
            [
                PersonalTrainingSession(member_id=members[0].member_id, trainer_id=trainers[0].trainer_id, room_id=rooms[0].room_id, start_time=datetime(2025, 11, 1, 9, 30), end_time=datetime(2025, 11, 1, 10, 30), session_type="Session", status="SCHEDULED"),
                PersonalTrainingSession(member_id=members[1].member_id, trainer_id=trainers[1].trainer_id, room_id=rooms[1].room_id, start_time=datetime(2025, 11, 2, 13, 30), end_time=datetime(2025, 11, 2, 14, 30), session_type="Session", status="SCHEDULED"),
                PersonalTrainingSession(member_id=members[2].member_id, trainer_id=trainers[2].trainer_id, room_id=rooms[2].room_id, start_time=datetime(2025, 11, 3, 15, 0), end_time=datetime(2025, 11, 3, 16, 0), session_type="Session", status="SCHEDULED"),
            ]
        )

        classes = [
            GroupClass(class_name="Yoga", trainer_id=trainers[1].trainer_id, room_id=rooms[0].room_id, class_time=datetime(2025, 11, 5, 10, 0), capacity=15, status="SCHEDULED"),
            GroupClass(class_name="HIIT", trainer_id=trainers[0].trainer_id, room_id=rooms[1].room_id, class_time=datetime(2025, 11, 6, 18, 0), capacity=10, status="SCHEDULED"),
            GroupClass(class_name="Spin", trainer_id=trainers[2].trainer_id, room_id=rooms[2].room_id, class_time=datetime(2025, 11, 7, 9, 0), capacity=12, status="SCHEDULED"),
        ]
        session.add_all(classes)
        session.flush()

        session.add_all(
            [
                ClassRegistration(member_id=members[0].member_id, class_id=classes[0].class_id),
                ClassRegistration(member_id=members[1].member_id, class_id=classes[0].class_id),
                ClassRegistration(member_id=members[2].member_id, class_id=classes[1].class_id),
            ]
        )

        equipment = [
            Equipment(room_id=rooms[0].room_id, equipment_name="Treadmill", status="OPERATIONAL"),
            Equipment(room_id=rooms[0].room_id, equipment_name="Exercise Bike", status="OPERATIONAL"),
            Equipment(room_id=rooms[1].room_id, equipment_name="Bench Press", status="UNDER_REPAIR"),
        ]
        session.add_all(equipment)
        session.flush()

        session.add_all(
            [
                MaintenanceLog(equipment_id=equipment[2].equipment_id, issue_description="Loose bolts", status="OPEN", created_at=datetime(2025, 10, 1)),
                MaintenanceLog(equipment_id=equipment[1].equipment_id, issue_description="Pedal noise", status="RESOLVED", created_at=datetime(2025, 10, 5)),
                MaintenanceLog(equipment_id=equipment[0].equipment_id, issue_description="Screen issue", status="OPEN", created_at=datetime(2025, 10, 6)),
            ]
        )

        invoices = [
            Invoice(member_id=members[0].member_id, issue_date=date(2025, 10, 15), total_amount=Decimal("120.00"), status="PAID", notes="Membership and PT"),
            Invoice(member_id=members[1].member_id, issue_date=date(2025, 10, 20), total_amount=Decimal("75.00"), status="UNPAID", notes="Yoga punch pass"),
            Invoice(member_id=members[2].member_id, issue_date=date(2025, 10, 22), total_amount=Decimal("95.00"), status="PAID", notes="Monthly plan"),
        ]
        session.add_all(invoices)
        session.flush()

        session.add_all(
            [
                InvoiceItem(invoice_id=invoices[0].invoice_id, description="Membership Fee", quantity=1, unit_price=Decimal("100.00")),
                InvoiceItem(invoice_id=invoices[0].invoice_id, description="PT Session", quantity=1, unit_price=Decimal("20.00")),
                InvoiceItem(invoice_id=invoices[1].invoice_id, description="Yoga Class", quantity=3, unit_price=Decimal("25.00")),
                InvoiceItem(invoice_id=invoices[2].invoice_id, description="Monthly Plan", quantity=1, unit_price=Decimal("95.00")),
            ]
        )

        session.add_all(
            [
                Payment(invoice_id=invoices[0].invoice_id, amount=Decimal("120.00"), payment_method="CREDIT_CARD", status="SUCCESS", payment_date=datetime(2025, 10, 20)),
                Payment(invoice_id=invoices[2].invoice_id, amount=Decimal("95.00"), payment_method="DEBIT", status="SUCCESS", payment_date=datetime(2025, 10, 22)),
                Payment(invoice_id=invoices[2].invoice_id, amount=Decimal("0.00"), payment_method="CASH", status="SUCCESS", payment_date=datetime(2025, 10, 22)),
            ]
        )
        print("Seeding complete.")


if __name__ == "__main__":
    try:
        seed(reset=True)
        print("Seed script finished successfully.")
    except Exception as exc:
        print(f"Seed script failed: {exc}")
        raise
