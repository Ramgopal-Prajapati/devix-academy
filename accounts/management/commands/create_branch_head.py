from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, timedelta, time
from decimal import Decimal
from academy.models import (
    Department, Course, TrainerProfile, StudentProfile,
    TrainerNotice, StudentDirectMessage, CourseResource, Notification
)
from attendance.models import Attendance, TrainerAttendance, LeaveRequest, StudentLeaveRequest
from payroll.models import SalaryRecord

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates the single DeviX Academy Branch Head and optionally seeds demo data.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='branchhead', help='Branch Head username')
        parser.add_argument('--email', type=str, default='branchhead@devixacademy.com', help='Branch Head email')
        parser.add_argument('--password', type=str, default='Admin@12345', help='Branch Head password')
        parser.add_argument('--no-seed', action='store_true', help='Skip seeding demo departments, courses, trainers, and students.')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        no_seed = options['no_seed']

        self.stdout.write(self.style.NOTICE("Initializing DeviX Academy Branch Head setup..."))

        # Check if Branch Head already exists
        existing_bh = User.objects.filter(role=User.Role.BRANCH_HEAD).first()
        if existing_bh:
            self.stdout.write(self.style.WARNING(
                f"[INFO] A Branch Head already exists: '{existing_bh.username}' ({existing_bh.email})."
            ))
            self.stdout.write(self.style.WARNING(
                "Per system rules, only ONE Branch Head is permitted. Creation of a second one is blocked."
            ))
            branch_head = existing_bh
        else:
            # Check if username exists with another role
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.ERROR(f"Error: User with username '{username}' already exists with a different role."))
                return

            branch_head = User(
                username=username,
                email=email,
                first_name='Ram',
                last_name='Sir (Head)',
                role=User.Role.BRANCH_HEAD,
                is_staff=True,
                is_superuser=True
            )
            branch_head.set_password(password)
            branch_head.save()

            self.stdout.write(self.style.SUCCESS(
                f"[SUCCESS] Branch Head account successfully created!\n"
                f"   Username: {username}\n"
                f"   Email:    {email}\n"
                f"   Password: {password}\n"
                f"   Role:     {branch_head.get_role_display()}"
            ))

        if no_seed:
            self.stdout.write("Skipping demo data seeding as requested.")
            return

        self.stdout.write(self.style.NOTICE("\nSeeding demo data (Departments, Courses, Trainers, Students, Attendance)..."))

        # 1. Departments
        tech_dept, _ = Department.objects.get_or_create(
            name="Tech",
            defaults={"description": "Software Engineering, Full Stack Development, Data Science & AI."}
        )
        non_tech_dept, _ = Department.objects.get_or_create(
            name="Non-Tech",
            defaults={"description": "Digital Marketing, Creative Design, Product Management."}
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Departments created: Tech, Non-Tech"))

        # 2. Courses
        courses_data = [
            ("Python Full Stack Development", tech_dept, "Complete Python, Django, DRF, PostgreSQL, HTML/CSS, React & Deployment.", "6 Months", Decimal('35000.00')),
            ("Java Full Stack Development", tech_dept, "Core Java, Advanced Java, Spring Boot, Microservices, Angular, MySQL & AWS.", "6 Months", Decimal('35000.00')),
            ("Data Science & Machine Learning", tech_dept, "Python, NumPy, Pandas, Scikit-Learn, Deep Learning, NLP, Power BI & Tableau.", "8 Months", Decimal('45000.00')),
            ("MERN Stack Web Development", tech_dept, "MongoDB, Express.js, React.js, Node.js, Next.js & Cloud Architecture.", "5 Months", Decimal('30000.00')),
            ("Digital Marketing & Growth", non_tech_dept, "SEO, SEM, Social Media Marketing, Content Strategy, Google Ads & Analytics.", "3 Months", Decimal('18000.00')),
            ("UI/UX Design & Branding", non_tech_dept, "Figma, Adobe XD, Design Systems, Wireframing, Prototyping & User Research.", "4 Months", Decimal('22000.00')),
        ]

        created_courses = {}
        for name, dept, desc, dur, fees in courses_data:
            c, _ = Course.objects.get_or_create(
                name=name,
                defaults={"department": dept, "description": desc, "duration": dur, "fees": fees, "is_active": True}
            )
            created_courses[name] = c
        self.stdout.write(self.style.SUCCESS(f"  [OK] {len(courses_data)} Courses created."))

        # 3. Trainers (2 Trainers)
        trainers_spec = [
            {
                "username": "trainer_rahul",
                "email": "rahul.sharma@devixacademy.com",
                "first_name": "Rahul",
                "last_name": "Sharma",
                "password": "Trainer@12345",
                "trainer_id": "TRN-001",
                "phone": "9876543210",
                "department": tech_dept,
                "bio": "Senior Full Stack Architect with 8+ years experience guiding industry aspirants into top-tier MNCs.",
                "experience_years": Decimal("8.5"),
                "experience_details": "Former Lead Developer at Infosys and Cognizant. Specializes in Java Microservices, Spring Boot, React, and cloud-native applications.",
                "technologies": "Java Full Stack, Spring Boot, Microservices, React.js, Web Development, MySQL, Docker",
                "linkedin": "https://linkedin.com/in/rahul-sharma-devix",
                "github": "https://github.com/rahul-devix",
                "twitter": "https://x.com/rahul_sharma_tech",
                "instagram": "https://instagram.com/rahul.codes",
                "youtube": "https://youtube.com/@rahultechacademy",
                "website": "https://rahulsharma.dev",
                "monthly_salary": Decimal("65000.00"),
                "daily_working_hours": Decimal("5.5"),
                "expected_start_time": time(9, 0),
            },
            {
                "username": "trainer_priya",
                "email": "priya.patel@devixacademy.com",
                "first_name": "Priya",
                "last_name": "Patel",
                "password": "Trainer@12345",
                "trainer_id": "TRN-002",
                "phone": "9876543211",
                "department": tech_dept,
                "bio": "AI/ML Practitioner & Data Science Specialist passionate about making math and statistics practical for real-world applications.",
                "experience_years": Decimal("6.0"),
                "experience_details": "Ex-Data Scientist at Tiger Analytics. Delivered multiple production ML models and trained 800+ data engineers.",
                "technologies": "Data Science, Machine Learning, Python Full Stack, Deep Learning, Data Analytics, Pandas, TensorFlow",
                "linkedin": "https://linkedin.com/in/priya-patel-data",
                "github": "https://github.com/priya-patel",
                "twitter": "https://x.com/priya_ml_engineer",
                "instagram": "https://instagram.com/priyapatel.ai",
                "youtube": "https://youtube.com/@priyadatascience",
                "website": "https://priyapatel.ai",
                "monthly_salary": Decimal("70000.00"),
                "daily_working_hours": Decimal("4.0"),
                "expected_start_time": time(9, 0),
            }
        ]

        created_trainers = []
        for t_spec in trainers_spec:
            user = User.objects.filter(username=t_spec["username"]).first()
            if not user:
                user = User(
                    username=t_spec["username"],
                    email=t_spec["email"],
                    first_name=t_spec["first_name"],
                    last_name=t_spec["last_name"],
                    role=User.Role.TRAINER,
                    phone=t_spec["phone"]
                )
                user.set_password(t_spec["password"])
                user.save()

            trainer_profile, _ = TrainerProfile.objects.get_or_create(
                user=user,
                defaults={
                    "trainer_id": t_spec["trainer_id"],
                    "phone": t_spec["phone"],
                    "email": t_spec["email"],
                    "department": t_spec["department"],
                    "bio": t_spec["bio"],
                    "experience_years": t_spec["experience_years"],
                    "experience_details": t_spec["experience_details"],
                    "technologies": t_spec["technologies"],
                    "linkedin": t_spec["linkedin"],
                    "github": t_spec["github"],
                    "twitter": t_spec["twitter"],
                    "instagram": t_spec["instagram"],
                    "youtube": t_spec["youtube"],
                    "website": t_spec["website"],
                    "monthly_salary": t_spec["monthly_salary"],
                    "daily_working_hours": t_spec["daily_working_hours"],
                    "expected_start_time": t_spec["expected_start_time"],
                }
            )
            # Make sure updated fields are saved if already created
            trainer_profile.daily_working_hours = t_spec["daily_working_hours"]
            trainer_profile.expected_start_time = t_spec["expected_start_time"]
            trainer_profile.twitter = t_spec["twitter"]
            trainer_profile.instagram = t_spec["instagram"]
            trainer_profile.youtube = t_spec["youtube"]
            trainer_profile.website = t_spec["website"]
            trainer_profile.save()
            created_trainers.append(trainer_profile)
        self.stdout.write(self.style.SUCCESS(f"  [OK] {len(created_trainers)} Trainers created."))

        # 4. Students (5 Students)
        students_spec = [
            {
                "username": "student_amit",
                "name": "Amit Kumar",
                "email": "amit.kumar@gmail.com",
                "phone": "9876543221",
                "password": "Student@12345",
                "student_id": "DVX-2026-0001",
                "department": tech_dept,
                "course": created_courses["Python Full Stack Development"],
                "trainer": created_trainers[1], # Priya Patel
                "student_class": "Morning Batch A-1",
                "course_duration": "6 Months",
                "target_attendance_rate": 0.90, # Eligible
            },
            {
                "username": "student_sneha",
                "name": "Sneha Verma",
                "email": "sneha.verma@gmail.com",
                "phone": "9876543222",
                "password": "Student@12345",
                "student_id": "DVX-2026-0002",
                "department": tech_dept,
                "course": created_courses["Java Full Stack Development"],
                "trainer": created_trainers[0], # Rahul Sharma
                "student_class": "Weekend Pro Batch",
                "course_duration": "6 Months",
                "target_attendance_rate": 0.95, # Eligible
            },
            {
                "username": "student_rohan",
                "name": "Rohan Singh",
                "email": "rohan.singh@gmail.com",
                "phone": "9876543223",
                "password": "Student@12345",
                "student_id": "DVX-2026-0003",
                "department": tech_dept,
                "course": created_courses["Data Science & Machine Learning"],
                "trainer": created_trainers[1], # Priya Patel
                "student_class": "Evening AI Cohort",
                "course_duration": "8 Months",
                "target_attendance_rate": 0.60, # Below 75% -> Ineligible
            },
            {
                "username": "student_ananya",
                "name": "Ananya Iyer",
                "email": "ananya.iyer@gmail.com",
                "phone": "9876543224",
                "password": "Student@12345",
                "student_id": "DVX-2026-0004",
                "department": tech_dept,
                "course": created_courses["MERN Stack Web Development"],
                "trainer": created_trainers[0], # Rahul Sharma
                "student_class": "Morning Batch A-2",
                "course_duration": "5 Months",
                "target_attendance_rate": 0.85, # Eligible
            },
            {
                "username": "student_vikram",
                "name": "Vikram Patel",
                "email": "vikram.patel@gmail.com",
                "phone": "9876543225",
                "password": "Student@12345",
                "student_id": "DVX-2026-0005",
                "department": non_tech_dept,
                "course": created_courses["UI/UX Design & Branding"],
                "trainer": created_trainers[0], # Rahul Sharma
                "student_class": "Creative Studio Batch",
                "course_duration": "4 Months",
                "target_attendance_rate": 0.68, # Below 75% -> Ineligible
            },
        ]

        created_students = []
        today = date.today()
        start_date = today - timedelta(days=35)

        for s_spec in students_spec:
            user = User.objects.filter(username=s_spec["username"]).first()
            if not user:
                user = User(
                    username=s_spec["username"],
                    email=s_spec["email"],
                    first_name=s_spec["name"].split()[0],
                    last_name=" ".join(s_spec["name"].split()[1:]),
                    role=User.Role.STUDENT,
                    phone=s_spec["phone"]
                )
                user.set_password(s_spec["password"])
                user.save()

            student_profile, _ = StudentProfile.objects.get_or_create(
                user=user,
                defaults={
                    "student_id": s_spec["student_id"],
                    "name": s_spec["name"],
                    "email": s_spec["email"],
                    "phone": s_spec["phone"],
                    "department": s_spec["department"],
                    "course": s_spec["course"],
                    "trainer": s_spec["trainer"],
                    "course_duration": s_spec["course_duration"],
                    "start_date": start_date,
                    "end_date": start_date + timedelta(days=180),
                    "student_class": s_spec["student_class"],
                    "is_active": True,
                }
            )
            created_students.append((student_profile, s_spec["target_attendance_rate"]))
        self.stdout.write(self.style.SUCCESS(f"  [OK] {len(created_students)} Students created."))
        
        # 5. Student Attendance Records for the last 25 weekdays
        total_days = 25
        dates = []
        cur_date = today - timedelta(days=32)
        while len(dates) < total_days:
            if cur_date.weekday() < 5:  # Monday to Friday
                dates.append(cur_date)
            cur_date += timedelta(days=1)

        attendance_count = 0
        for student, target_rate in created_students:
            present_threshold = int(total_days * target_rate)
            for idx, d in enumerate(dates):
                status = "Present" if idx < present_threshold else "Absent"
                _, created = Attendance.objects.get_or_create(
                    student=student,
                    date=d,
                    defaults={
                        "status": status,
                        "marked_by": student.trainer.user if student.trainer else branch_head
                    }
                )
                if created:
                    attendance_count += 1
        self.stdout.write(self.style.SUCCESS(f"  [OK] {attendance_count} Student attendance logs generated."))

        # 6. Trainer Attendance Records (Punch-In & Punch-Out with 20-min grace rule)
        trainer_att_count = 0
        for trainer in created_trainers:
            for idx, d in enumerate(dates):
                status = "Present"
                check_in_time = time(9, 5)
                check_out_time = time(14, 40)
                hours_worked = Decimal("5.58")
                remark = "Completed full scheduled shift on time."

                # Simulate a Half Day for Rahul due to >20m late punch-in
                if trainer.trainer_id == "TRN-001" and idx == 3:
                    status = "Half_Day"
                    check_in_time = time(9, 35)
                    check_out_time = time(14, 30)
                    hours_worked = Decimal("4.92")
                    remark = "Late Punch-In by 35 mins (>20m grace) -> Half Day marked."
                # Simulate an approved leave day
                elif trainer.trainer_id == "TRN-001" and idx in [5]:
                    status = "Leave"
                    check_in_time = None
                    check_out_time = None
                    hours_worked = Decimal("0.00")
                    remark = "Approved Full Day Leave"

                _, created = TrainerAttendance.objects.get_or_create(
                    trainer=trainer,
                    date=d,
                    defaults={
                        "status": status,
                        "check_in": check_in_time,
                        "check_out": check_out_time,
                        "working_hours_recorded": hours_worked,
                        "remark": remark,
                    }
                )
                if created:
                    trainer_att_count += 1
        self.stdout.write(self.style.SUCCESS(f"  [OK] {trainer_att_count} Trainer punch attendance logs generated."))

        # 7. Leave Requests (Full Day and Half Day)
        # Approved Full Day leave for Rahul Sharma
        LeaveRequest.objects.get_or_create(
            trainer=created_trainers[0],
            from_date=dates[5],
            to_date=dates[5],
            defaults={
                "leave_duration_type": "FULL_DAY",
                "reason": "Family function and personal travel.",
                "status": "Approved",
                "reviewed_by": branch_head,
                "remark": "Approved. Deducted 1 day from payroll."
            }
        )

        # Approved Half Day leave for Priya Patel
        LeaveRequest.objects.get_or_create(
            trainer=created_trainers[1],
            from_date=dates[8],
            to_date=dates[8],
            defaults={
                "leave_duration_type": "HALF_DAY",
                "half_day_period": "FIRST_HALF",
                "reason": "Doctor consultation in morning session.",
                "status": "Approved",
                "reviewed_by": branch_head,
                "remark": "Approved for 1st half. Deducted 0.5 day from payroll."
            }
        )

        # Pending leave for Priya Patel
        LeaveRequest.objects.get_or_create(
            trainer=created_trainers[1],
            from_date=today + timedelta(days=3),
            to_date=today + timedelta(days=3),
            defaults={
                "leave_duration_type": "FULL_DAY",
                "reason": "Attending AI/ML National Academic Summit.",
                "status": "Pending",
                "remark": ""
            }
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Sample Full Day & Half Day Leave Requests generated."))

        # 8. Sample Salary Record with strict leave deductions
        prev_month = today.month - 1 if today.month > 1 else 12
        prev_year = today.year if today.month > 1 else today.year - 1
        
        working_days = 22
        present_days = 20
        full_day_leaves = Decimal("1.0")
        half_day_leaves = Decimal("0.0")
        half_day_punches = Decimal("1.0")
        absent_days = Decimal("0.0")
        total_deduction_days = full_day_leaves + (half_day_punches * Decimal("0.5"))  # 1.5 days
        
        per_day = (Decimal("65000.00") / Decimal(working_days)).quantize(Decimal("0.01"))
        deduction = (total_deduction_days * per_day).quantize(Decimal("0.01"))
        net = (Decimal("65000.00") - deduction).quantize(Decimal("0.01"))

        SalaryRecord.objects.get_or_create(
            trainer=created_trainers[0],
            month=prev_month,
            year=prev_year,
            defaults={
                "monthly_salary": Decimal("65000.00"),
                "working_days": working_days,
                "present_days": Decimal(present_days),
                "full_day_leaves": full_day_leaves,
                "half_day_leaves": half_day_leaves,
                "half_day_punches": half_day_punches,
                "leave_days": full_day_leaves,
                "paid_leave_days": Decimal("0.0"),
                "absent_days": absent_days,
                "total_deduction_days": total_deduction_days,
                "per_day_salary": per_day,
                "deduction": deduction,
                "net_salary": net,
                "generated_by": branch_head,
                "notes": "Salary processed with itemized deductions: 1 Full Day Leave & 1 Half Day Punch Delay."
            }
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Sample Salary Record created for TRN-001."))

        # 9. Trainer Leave & Holiday Notices
        # Rahul Sharma Leave Notice for his assigned students
        notice_rahul, _ = TrainerNotice.objects.get_or_create(
            trainer=created_trainers[0],
            title="Trainer Rahul on Leave - Lab Practice Session Assigned",
            defaults={
                "department": tech_dept,
                "notice_type": "LEAVE",
                "message": "Dear students, I will be attending an emergency corporate symposium on Thursday & Friday. Please work on the Spring Boot Microservices assignment (Exercise 4.2). We will review code submissions on Monday at 10:00 AM.",
                "from_date": today + timedelta(days=2),
                "to_date": today + timedelta(days=3),
                "is_active": True,
            }
        )

        # Priya Patel Holiday Notice for her students
        notice_priya, _ = TrainerNotice.objects.get_or_create(
            trainer=created_trainers[1],
            title="Institute Holiday Announcement - Deepavali Festival",
            defaults={
                "department": tech_dept,
                "notice_type": "HOLIDAY",
                "message": "DeviX Academy will remain closed from next Wednesday to Friday on account of Deepavali celebrations. Regular classes and AI project labs will resume the following Monday.",
                "from_date": today + timedelta(days=6),
                "to_date": today + timedelta(days=8),
                "is_active": True,
            }
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Sample Trainer Leave & Holiday Broadcast Notices created."))

        # 10. Direct Student Messages & 1-on-1 Chat (PDFs, materials, links, student replies)
        # Message to Sneha Verma from Rahul Sharma
        student_sneha_obj = StudentProfile.objects.filter(student_id="DVX-2026-0002").first()
        if student_sneha_obj:
            if not StudentDirectMessage.objects.filter(trainer=created_trainers[0], student=student_sneha_obj, subject="Week 4 Microservices Assignment & Architecture PDF").exists():
                StudentDirectMessage.objects.create(
                    trainer=created_trainers[0],
                    student=student_sneha_obj,
                    subject="Week 4 Microservices Assignment & Architecture PDF",
                    sender_role="TRAINER",
                    message="Hello Sneha, please find attached the architecture specification document for our distributed order service project. Ensure Docker compose definitions match the port bindings described.",
                    attachment="student_materials/project_assignment_week4.txt",
                    link_url="https://github.com/rahul-devix",
                    is_read=True,
                )
            # Student Sneha 1-on-1 reply to Rahul Sharma
            if not StudentDirectMessage.objects.filter(trainer=created_trainers[0], student=student_sneha_obj, subject="Reply from Sneha Verma").exists():
                StudentDirectMessage.objects.create(
                    trainer=created_trainers[0],
                    student=student_sneha_obj,
                    subject="Reply from Sneha Verma",
                    sender_role="STUDENT",
                    message="Thank you Rahul Sir! I have reviewed the architecture PDF and successfully containerized the services. Could you please take a look at my branch when you have a moment?",
                    link_url="https://github.com/sneha-verma/order-service",
                    is_read=False,
                )

        # Message to Amit Kumar from Priya Patel
        student_amit_obj = StudentProfile.objects.filter(student_id="DVX-2026-0001").first()
        if student_amit_obj:
            if not StudentDirectMessage.objects.filter(trainer=created_trainers[1], student=student_amit_obj, subject="Data Science Pandas & NumPy Practice Notebooks").exists():
                StudentDirectMessage.objects.create(
                    trainer=created_trainers[1],
                    student=student_amit_obj,
                    subject="Data Science Pandas & NumPy Practice Notebooks",
                    sender_role="TRAINER",
                    message="Hi Amit, great work on the EDA analysis yesterday. I have compiled advanced feature engineering notebooks and reference documentation for your self-study.",
                    attachment="course_resources/python_fullstack_guide.txt",
                    link_url="https://github.com/priya-patel",
                    is_read=True,
                )
            # Student Amit 1-on-1 reply to Priya Patel
            if not StudentDirectMessage.objects.filter(trainer=created_trainers[1], student=student_amit_obj, subject="Reply from Amit Kumar").exists():
                StudentDirectMessage.objects.create(
                    trainer=created_trainers[1],
                    student=student_amit_obj,
                    subject="Reply from Amit Kumar",
                    sender_role="STUDENT",
                    message="Understood Priya Ma'am. I have completed the exercise on missing value imputations and pushed the notebook. Thanks for the quick feedback!",
                    is_read=False,
                )
        self.stdout.write(self.style.SUCCESS("  [OK] Sample 1-on-1 Bidirectional Direct Messages & Replies created."))

        # 11. Course Learning Resources
        # Resource for Python Full Stack
        CourseResource.objects.get_or_create(
            course=created_courses["Python Full Stack Development"],
            title="Django ORM Optimization & MVT Architecture Cheatsheet",
            defaults={
                "trainer": created_trainers[1],
                "department": tech_dept,
                "description": "Comprehensive reference guide covering select_related, prefetch_related, indexing, and REST framework viewset patterns.",
                "resource_type": "FILE",
                "file": "course_resources/python_fullstack_guide.txt",
                "link_url": "https://docs.djangoproject.com/en/5.0/",
            }
        )

        # Resource for Java Full Stack
        CourseResource.objects.get_or_create(
            course=created_courses["Java Full Stack Development"],
            title="Spring Boot Microservices & JWT Auth Code Snippet",
            defaults={
                "trainer": created_trainers[0],
                "department": tech_dept,
                "description": "Ready-to-use SecurityFilterChain configuration and JWT token verification filter implementation for Spring Boot 3.",
                "resource_type": "NOTES",
                "notes_content": "@Configuration\n@EnableWebSecurity\npublic class SecurityConfig {\n    @Bean\n    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {\n        http.csrf(csrf -> csrf.disable())\n            .authorizeHttpRequests(auth -> auth\n                .requestMatchers(\"/api/auth/**\").permitAll()\n                .anyRequest().authenticated()\n            )\n            .sessionManagement(sess -> sess.sessionCreationPolicy(SessionCreationPolicy.STATELESS));\n        return http.build();\n    }\n}",
            }
        )

        # Resource for Data Science
        CourseResource.objects.get_or_create(
            course=created_courses["Data Science & Machine Learning"],
            title="Kaggle Dataset & Machine Learning Pipeline Tutorial",
            defaults={
                "trainer": created_trainers[1],
                "department": tech_dept,
                "description": "Interactive Kaggle notebook link and Scikit-Learn end-to-end pipeline tutorial for predictive classification modeling.",
                "resource_type": "LINK",
                "link_url": "https://scikit-learn.org/stable/modules/compose.html#pipeline",
            }
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Course Learning Resources created."))

        # 12. Student Leave Requests & Activity Notifications
        # Student Amit leaves (Pending)
        amit = created_students[0][0]
        sneha = created_students[1][0]
        priya = created_trainers[1]
        rahul = created_trainers[0]

        leave_pending, _ = StudentLeaveRequest.objects.get_or_create(
            student=amit,
            from_date=today + timedelta(days=2),
            to_date=today + timedelta(days=3),
            defaults={
                "leave_type": "Academic",
                "reason": "Final semester university project presentation and viva examination.",
                "status": "Pending",
            }
        )

        # Student Sneha leave (Approved with attendance marked 'Leave')
        leave_approved, created = StudentLeaveRequest.objects.get_or_create(
            student=sneha,
            from_date=today - timedelta(days=5),
            to_date=today - timedelta(days=4),
            defaults={
                "leave_type": "Medical",
                "reason": "Doctor appointment and viral recovery rest.",
                "status": "Approved",
                "reviewed_by": rahul.user,
                "trainer_remark": "Approved. Please get notes from Sneha's batchmates.",
            }
        )
        if created or leave_approved.status == 'Approved':
            Attendance.objects.update_or_create(
                student=sneha,
                date=today - timedelta(days=5),
                defaults={"status": "Leave", "marked_by": rahul.user}
            )
            Attendance.objects.update_or_create(
                student=sneha,
                date=today - timedelta(days=4),
                defaults={"status": "Leave", "marked_by": rahul.user}
            )

        # Activity Notifications
        Notification.objects.get_or_create(
            recipient=priya.user,
            title=f"Leave Request from {amit.name}",
            defaults={
                "message": f"{amit.name} ({amit.student_id}) requested 2 days leave for semester exams.",
                "link_url": "/trainer/student-leaves/",
                "notification_type": "LEAVE_REQUEST",
                "is_read": False,
            }
        )
        Notification.objects.get_or_create(
            recipient=amit.user,
            title="Welcome to DeviX Academy!",
            defaults={
                "message": f"Welcome {amit.name}! You are enrolled in Python Full Stack Development.",
                "link_url": "/student/dashboard/",
                "notification_type": "STUDENT_ENROLLED",
                "is_read": False,
            }
        )
        Notification.objects.get_or_create(
            recipient=sneha.user,
            title="Leave Application Approved",
            defaults={
                "message": f"Trainer Rahul Sharma approved your 2-day medical leave.",
                "link_url": "/student/leave/apply/",
                "notification_type": "LEAVE_REVIEW",
                "is_read": False,
            }
        )
        Notification.objects.get_or_create(
            recipient=branch_head,
            title="Trainer Leave Request",
            defaults={
                "message": "Trainer Priya Verma requested 1 day full-day leave.",
                "link_url": "/branch-head/leaves/",
                "notification_type": "LEAVE_REQUEST",
                "is_read": False,
            }
        )
        self.stdout.write(self.style.SUCCESS("  [OK] Student Leave Requests & Activity Notifications seeded."))

        self.stdout.write(self.style.SUCCESS(
            "\n" + "="*60 + "\n"
            "   DeviX Academy setup & demo data initialization COMPLETE!\n"
            "="*60 + "\n"
            "Demo Credentials Summary:\n"
            "  1. Branch Head:  username: 'branchhead'    | password: 'Admin@12345'\n"
            "  2. Trainer 1:    username: 'trainer_rahul' | password: 'Trainer@12345'\n"
            "  3. Trainer 2:    username: 'trainer_priya' | password: 'Trainer@12345'\n"
            "  4. Student 1:    username: 'student_amit'  | password: 'Student@12345' (Eligible: ~90%)\n"
            "  5. Student 2:    username: 'student_sneha' | password: 'Student@12345' (Eligible: ~95%)\n"
            "  6. Student 3:    username: 'student_rohan' | password: 'Student@12345' (Ineligible: ~60%)\n"
            "  7. Student 4:    username: 'student_ananya'| password: 'Student@12345' (Eligible: ~85%)\n"
            "  8. Student 5:    username: 'student_vikram'| password: 'Student@12345' (Ineligible: ~68%)\n"
            "="*60
        ))
