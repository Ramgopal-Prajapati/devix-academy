from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import datetime

from academy.models import Department, Course, TrainerProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Safely initializes production departments, courses, and default accounts on Render if not already present.'

    def handle(self, *args, **options):
        self.stdout.write("Checking initial production setup on Render...")

        # 1. Departments
        tech_dept, _ = Department.objects.get_or_create(
            name="Tech",
            defaults={"description": "Software Engineering, Full Stack Development, Data Science & AI."}
        )
        non_tech_dept, _ = Department.objects.get_or_create(
            name="Non-Tech",
            defaults={"description": "Digital Marketing, Creative Design, Product Management."}
        )

        # 2. Courses
        courses_data = [
            ("Python Full Stack Development", tech_dept, "Complete Python, Django, DRF, PostgreSQL, HTML/CSS, React & Deployment.", "6 Months", Decimal('35000.00')),
            ("Java Full Stack Development", tech_dept, "Core Java, Advanced Java, Spring Boot, Microservices, Angular, MySQL & AWS.", "6 Months", Decimal('35000.00')),
            ("Data Science & Machine Learning", tech_dept, "Python, NumPy, Pandas, Scikit-Learn, Deep Learning, NLP, Power BI & Tableau.", "8 Months", Decimal('45000.00')),
            ("MERN Stack Web Development", tech_dept, "MongoDB, Express.js, React.js, Node.js, Next.js & Cloud Architecture.", "5 Months", Decimal('30000.00')),
            ("Digital Marketing & Growth", non_tech_dept, "SEO, SEM, Social Media Marketing, Content Strategy, Google Ads & Analytics.", "3 Months", Decimal('18000.00')),
            ("UI/UX Design & Branding", non_tech_dept, "Figma, Adobe XD, Design Systems, Wireframing, Prototyping & User Research.", "4 Months", Decimal('22000.00')),
        ]
        for name, dept, desc, dur, fees in courses_data:
            Course.objects.get_or_create(
                name=name,
                defaults={"department": dept, "description": desc, "duration": dur, "fees": fees, "is_active": True}
            )

        # 3. Branch Head (reena@samyak.com / Reena@123)
        if not User.objects.filter(role=User.Role.BRANCH_HEAD).exists():
            bh = User(
                username='reena@samyak.com',
                email='reena@samyak.com',
                first_name='Reena',
                last_name="Ma'am",
                phone='9876500000',
                role=User.Role.BRANCH_HEAD,
                is_staff=True,
                is_superuser=True
            )
            bh.set_password('Reena@123')
            bh.save()
            self.stdout.write(self.style.SUCCESS("[OK] Branch Head account created: reena@samyak.com"))
        else:
            self.stdout.write("[INFO] Branch Head already exists.")

        # 4. Trainer 1: Ram Sir (ramsir@samyak.com / Ramsir@123)
        if not User.objects.filter(email='ramsir@samyak.com').exists():
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
            self.stdout.write(self.style.SUCCESS("[OK] Trainer 1 created: ramsir@samyak.com"))
        else:
            self.stdout.write("[INFO] Trainer 1 already exists.")

        # 5. Trainer 2: Jiten Sir (jiten@samyak.com / Jiten@123)
        if not User.objects.filter(email='jiten@samyak.com').exists():
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
            self.stdout.write(self.style.SUCCESS("[OK] Trainer 2 created: jiten@samyak.com"))
        else:
            self.stdout.write("[INFO] Trainer 2 already exists.")

        self.stdout.write(self.style.SUCCESS("Render initial data check complete."))
