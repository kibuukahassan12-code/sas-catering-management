from app import app, db

from models import Vehicle, DispatchRun, LoadSheetItem, Event, User

from datetime import datetime, date, timedelta

from random import choice, randint



with app.app_context():

    # Check if data already exists

    existing_vehicles = Vehicle.query.count()

    existing_runs = DispatchRun.query.count()

    

    if existing_vehicles > 0 or existing_runs > 0:

        print(f"⚠️  Dispatch data already exists ({existing_vehicles} vehicles, {existing_runs} runs). Skipping seed.")

    else:

        # Get or create sample users for drivers

        from models import UserRole

        drivers = User.query.filter(User.role.in_([UserRole.Admin, UserRole.SalesManager, UserRole.Driver])).limit(3).all()

        if not drivers:

            # Create a sample driver if none exist

            from werkzeug.security import generate_password_hash

            from models import UserRole

            driver = User(

                email="driver@example.com",

                password_hash=generate_password_hash("password123"),

                role=UserRole.Driver

            )

            db.session.add(driver)

            db.session.flush()

            drivers = [driver]



        # Create vehicles if they don't exist

        vehicles = [

            Vehicle(

                registration_number="UAY 452Q",

                make="ISUZU",

                model="NKR Truck",

                capacity=2500,

                is_active=True,

                updated_at=datetime.utcnow()

            ),

            Vehicle(

                registration_number="UAX 992L",

                make="Toyota",

                model="HiAce Van",

                capacity=1500,

                is_active=True,

                updated_at=datetime.utcnow()

            ),

            Vehicle(

                registration_number="UBA 123C",

                make="Fuso",

                model="Fighter",

                capacity=5000,

                is_active=False,  # inactive

                updated_at=datetime.utcnow()

            ),

            Vehicle(

                registration_number="UBB 456D",

                make="Nissan",

                model="Urvan",

                capacity=1200,

                is_active=True,

                updated_at=datetime.utcnow()

            )

        ]



        db.session.add_all(vehicles)

        db.session.flush()



        # Get some events for dispatch runs

        events = Event.query.limit(5).all()

        if not events:

            print("⚠️  No events found. Creating dispatch runs without events.")

            events = [None] * 3



        # Create dispatch runs

        dispatch_runs = []

        today = date.today()

        

        # Today's runs

        for i in range(3):

            run_date = today

            vehicle = choice([v for v in vehicles if v.is_active])

            driver = choice(drivers) if drivers else None

            event = events[i] if i < len(events) else None

            

            run = DispatchRun(

                vehicle_id=vehicle.id if vehicle else None,

                driver_id=driver.id if driver else None,

                event_id=event.id if event else None,

                run_date=run_date,

                departure_time=datetime.utcnow().replace(hour=8 + i, minute=0, second=0, microsecond=0),

                status=choice(["Scheduled", "In Transit", "Completed"]),

                created_at=datetime.utcnow()

            )

            dispatch_runs.append(run)

            db.session.add(run)

            db.session.flush()

            

            # Add load sheet items

            load_items = [

                LoadSheetItem(

                    dispatch_run_id=run.id,

                    item_name=choice(["Food Trays", "Serving Utensils", "Table Linens", "Chairs", "Tables", "Décor Items"]),

                    quantity=randint(10, 50),

                    unit=choice(["pcs", "sets", "boxes"])

                ),

                LoadSheetItem(

                    dispatch_run_id=run.id,

                    item_name=choice(["Beverages", "Ice", "Napkins", "Plates", "Cutlery"]),

                    quantity=randint(20, 100),

                    unit=choice(["pcs", "packs", "cases"])

                )

            ]

            db.session.add_all(load_items)



        # Tomorrow's scheduled runs

        tomorrow = today + timedelta(days=1)

        for i in range(2):

            vehicle = choice([v for v in vehicles if v.is_active])

            driver = choice(drivers) if drivers else None

            event = events[i + 3] if i + 3 < len(events) else None

            

            run = DispatchRun(

                vehicle_id=vehicle.id if vehicle else None,

                driver_id=driver.id if driver else None,

                event_id=event.id if event else None,

                run_date=tomorrow,

                status="Scheduled",

                created_at=datetime.utcnow()

            )

            dispatch_runs.append(run)

            db.session.add(run)

            db.session.flush()

            

            # Add load sheet items

            load_items = [

                LoadSheetItem(

                    dispatch_run_id=run.id,

                    item_name=choice(["Food Trays", "Serving Utensils", "Table Linens"]),

                    quantity=randint(15, 40),

                    unit=choice(["pcs", "sets"])

                )

            ]

            db.session.add_all(load_items)



        db.session.commit()

        print(f"✓ Sample dispatch data added successfully!")

        print(f"  - {len(vehicles)} vehicles")

        print(f"  - {len(dispatch_runs)} dispatch runs")

        print(f"  - {len(dispatch_runs) * 2} load sheet items")
