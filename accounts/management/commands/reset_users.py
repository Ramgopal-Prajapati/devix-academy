from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from academy.models import Department, Course, TrainerProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Deletes all existing demo users and creates Branch Head Reena and Trainers Ram Sir and Jiten Sir.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Deleting all existing users from the system..."))

        # Delete all users (cascades to profiles, attendance, leaves, notifications, etc.)
        deleted_count, _ = User.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} user and related records."))

        # Ensure Departments exist
        tech_dept, _ = Department.objects.get_or_create(
            name="Tech",
            defaults={"description": "Software Engineering, Full Stack Development, Data Science & AI."}
        )
        non_tech_dept, _ = Department.objects.get_or_create(
            name="Non-Tech",
            defaults={"description": "Digital Marketing, Creative Design, Product Management."}
        )

        # 1. Create Branch Head: reena@samyak.com / Reena@123
        self.stdout.write(self.style.NOTICE("Creating Branch Head: reena@samyak.com ..."))
        branch_head = User(
            username='reena@samyak.com',
            email='reena@samyak.com',
            first_name='Reena',
            last_name="Ma'am",
            phone='9876500000',
            role=User.Role.BRANCH_HEAD,
            is_staff=True,
            is_superuser=True
        )
        branch_head.set_password('Reena@123')
        branch_head.save()

        # 2. Create Trainer 1: ramsir@samyak.com / Ramsir@123
        self.stdout.write(self.style.NOTICE("Creating Trainer 1: ramsir@samyak.com ..."))
        ramsir_user = User(
            username='ramsir@samyak.com',
            email='ramsir@samyak.com',
            first_name='Ram',
            last_name='Sir',
            phone='9876500001',
            role=User.Role.TRAINER
        )
        ramsir_user.set_password('Ramsir@123')
        ramsir_user.save()

        TrainerProfile.objects.create(
            user=ramsir_user,
            trainer_id="TRN-001",
            phone="9876500001",
            email="ramsir@samyak.com",
            department=tech_dept,
            technologies="Python Full Stack, Django, Data Science, Web Development, Java Full Stack, C/C++",
            experience_years=Decimal("10.0"),
            bio="Senior Technical Mentor and Founder at DeviX Academy. 10+ years specializing in Full Stack Engineering, Python, Django, Data Science and Cloud Architecture.",
            monthly_salary=Decimal("60000.00"),
            daily_working_hours=Decimal("5.0"),
            expected_start_time=datetime.time(9, 0),
            linkedin="https://linkedin.com/in/ramsir",
            github="https://github.com/ramsir",
            twitter="https://twitter.com/ramsir",
            instagram="https://instagram.com/ramsir_devix",
            youtube="https://youtube.com/@DeviXAcademy",
            website="https://devixacademy.com"
        )

        # 3. Create Trainer 2: jiten@samyak.com / Jiten@123
        self.stdout.write(self.style.NOTICE("Creating Trainer 2: jiten@samyak.com ..."))
        jiten_user = User(
            username='jiten@samyak.com',
            email='jiten@samyak.com',
            first_name='Jiten',
            last_name='Sir',
            phone='9876500002',
            role=User.Role.TRAINER
        )
        jiten_user.set_password('Jiten@123')
        jiten_user.save()

        TrainerProfile.objects.create(
            user=jiten_user,
            trainer_id="TRN-002",
            phone="9876500002",
            email="jiten@samyak.com",
            department=tech_dept,
            technologies="Java Full Stack, Spring Boot, Microservices, Angular, MySQL, Docker",
            experience_years=Decimal("7.5"),
            bio="Lead Java and Enterprise Systems Instructor. Specializing in Spring Boot microservices, high-scale APIs, Docker and database optimization.",
            monthly_salary=Decimal("50000.00"),
            daily_working_hours=Decimal("4.5"),
            expected_start_time=datetime.time(9, 30),
            linkedin="https://linkedin.com/in/jiten-sir",
            github="https://github.com/jiten-devix",
            twitter="https://twitter.com/jiten_devix",
            instagram="https://instagram.com/jiten_devix",
            youtube="https://youtube.com/@DeviXAcademy",
            website="https://devixacademy.com"
        )

        self.stdout.write(self.style.SUCCESS(
            "\n"
            "============================================================\n"
            "   DeviX Academy Users Successfully Configured!\n"
            "============================================================\n"
            "Active Credentials:\n"
            "  1. Branch Head: reena@samyak.com  | Password: Reena@123\n"
            "  2. Trainer 1:   ramsir@samyak.com | Password: Ramsir@123\n"
            "  3. Trainer 2:   jiten@samyak.com  | Password: Jiten@123\n"
            "============================================================"
        ))
