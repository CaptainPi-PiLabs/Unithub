# Unit Hub
>⚠️ **Work In Progress**\
This project is still in early development. Features, APIs, and data models are likely to change.

Unit Hub is an open-source Django application designed to help structured groups clearly document and understand how their unit operates.
It provides a central place to view unit structure, roles, and training, showing who holds which positions, what qualifications exist, and what is required to progress.
By making this information visible and easy to understand, Unit Hub supports onboarding, reduces administrative overhead, and preserves a clear history of how the unit has evolved over time.

## Key Features
- Custom organisational structure (platoons, sections, ranks)
- Membership assignments with full history
- Training and certification management
- User progression and award timeline
- Role-based and API-based access control

## Apps
| App        | Purpose                           | Status       |
|------------|-----------------------------------|--------------|
| Orbat      | Unit structure & membership       | In progress  |
| Training   | Courses & certifications          | In progress  |
| Timeline   | User progression history          | In progress  |
| Users      | Authentication & permissions      | In progress  |
| APIs       | Internal & service integrations   | Experimental |
| Attendance | Event attendance tracking         | Planned      |
| Events     | Event management                  | Planned      |
| Dashboard  | Latest feed, events, welcome page | Planned      |

## Configuration
Environment variables (via `.env`):
```env
DEBUG=False
SECRET_KEY=
ALLOWED_HOSTS=*

DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_REDIRECT_URI=http://localhost:8000/auth/discord/callback/

ENABLE_EVENTS=True     # Enable WIP events features
ENABLE_TRAINING=True   # Enable WIP training features
```
