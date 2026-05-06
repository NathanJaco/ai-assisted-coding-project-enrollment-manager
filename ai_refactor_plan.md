1. Backend refactor plan with practical steps

Start by separating the code based on responsibility, not just by function name. The first step should be to identify everything that directly uses SQLite and plan to move that into a database/store class. Next, identify the functions that represent student actions or enrollment rules and plan to move those into a service/manager class. After that, keep constants, sample data, JSON export, and the main runner separate because those parts support the app but are not the main database or service logic.

The refactor should happen in small steps. First create the database/store class, then move database-only functions into it. Then create the service/manager class and have it call the store instead of writing SQL directly. Finally, update the runner so it creates the store and service objects and uses them to test the same behavior as the original starter file.

2. What should move into a database/store class

The database/store class should handle SQLite row work. This includes opening the database connection, creating tables, seeding sample data, finding a course by enrollment key, getting available course keys, getting student enrollments, getting student enrollment history, getting one student course record, getting all enrollment records, and updating enrollment rows.

The store class should be the only place where raw SQL appears. That keeps SELECT, INSERT, and UPDATE statements away from the service layer.

3. What should move into a service/manager class

The service/manager class should handle the meaning behind student enrollment actions. This includes validating an enrollment key, enrolling or reactivating a student, soft-unenrolling a student, and creating student summary counts.

For example, enroll_with_key should become mostly service logic. The service should check whether the student information and key are valid, ask the store for the matching course, and then ask the store to save or update the enrollment record. The service decides what should happen, while the store handles how the database changes.

4. What should stay as config, setup, export, or runner code

Constants like DB_PATH, SNAPSHOT_PATH, statuses, current student, and sample course keys should stay outside the main service logic. They can be kept as config/constants so they are easy to find and change.

The JSON snapshot export should not be mixed into the core enrollment rules. It can stay as a separate helper/export function or be handled by the runner. The main runner should stay simple: create the objects, run setup, call a few methods, print results, and export the snapshot if needed.

5. Why this plan improves the design

This plan improves the design because each part of the program has a clearer job. The database/store class focuses on SQLite and rows. The service/manager class focuses on student rules and enrollment meaning. The runner focuses on starting and testing the flow.

This also makes the code easier to change later. For example, if the database query changes, it should only affect the store class. If the enrollment rule changes, it should mostly affect the service class. That is the main benefit of moving from procedural code to a layered object-oriented design.