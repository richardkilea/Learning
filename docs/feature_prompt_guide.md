# Feature Prompt Guide

How to write prompts when requesting a new feature for your FastAPI project. Use this as a template to get consistent, high-quality results every conversation.

---

## The Prompt Template

Copy, fill in the blanks, and send alongside `production_reference.md` + `rules_of_engagement.md`:

```
I am building [app name] — [one-line description of the app].

The attached `production_reference.md` is the architecture blueprint.
The attached `rules_of_engagement.md` defines how you should work.

## Feature: [feature name]

### What it does
[2-3 sentences describing the feature from a user's perspective]

### Entities involved
- [Entity A]: [key fields — e.g. "name, email, role (enum: admin/member)"]
- [Entity B]: [key fields]
- Relationship: [e.g. "A user has many projects. A project belongs to one user."]

### Endpoints needed
- POST   /api/v1/[resource]          — [what it does]
- GET    /api/v1/[resource]          — [what it does, mention if paginated/filterable]
- GET    /api/v1/[resource]/{id}     — [what it does]
- PATCH  /api/v1/[resource]/{id}     — [what it does]
- DELETE /api/v1/[resource]/{id}     — [what it does]

### Auth requirements
- [Which endpoints need auth? Which are public?]
- [Any ownership rules? e.g. "Users can only edit their own projects"]

### Business rules
- [Constraints, validations, or edge cases]
- [e.g. "Project name must be unique per user", "Max 10 projects per free user"]

### Priority
[Start with X — build the rest after I confirm it works]
```

---

## Examples

### Example 1: Simple CRUD Feature

```
I am building TaskFlow — a project management API.

The attached `production_reference.md` is the architecture blueprint.
The attached `rules_of_engagement.md` defines how you should work.

## Feature: Task Management

### What it does
Users can create tasks within their projects, assign them to team members,
and track status (todo → in_progress → done).

### Entities involved
- Task: title, description (optional), status (enum: todo/in_progress/done),
  priority (enum: low/medium/high), due_date (optional), project_id, assignee_id (optional)
- Relationship: A project has many tasks. A task belongs to one project.
  A task can be assigned to one user.

### Endpoints needed
- POST   /api/v1/projects/{project_id}/tasks     — create a task in a project
- GET    /api/v1/projects/{project_id}/tasks     — list tasks (paginated, filterable by status/assignee)
- GET    /api/v1/tasks/{id}                       — get task details
- PATCH  /api/v1/tasks/{id}                       — update task (status, assignee, etc.)
- DELETE /api/v1/tasks/{id}                       — delete task

### Auth requirements
- All endpoints require auth
- Only project members can create/view tasks
- Only task creator or assignee can update/delete

### Business rules
- Default status is "todo"
- Status transitions: todo → in_progress → done (no skipping backwards)
- Title max 200 chars, description max 2000 chars
- due_date must be in the future when creating

### Priority
Start with the model + schema + basic CRUD (create, list, get).
Add status transitions and assignee logic after I confirm.
```

### Example 2: Auth Feature from Scratch

```
I am building StoreAPI — an e-commerce backend.

The attached `production_reference.md` is the architecture blueprint.
The attached `rules_of_engagement.md` defines how you should work.

## Feature: User Authentication

### What it does
Users register with email/password, log in to receive a JWT token,
and use the token to access protected endpoints.

### Entities involved
- User: email (unique), username (unique), password, is_active (default true),
  created_at

### Endpoints needed
- POST /api/v1/auth/register    — create account
- POST /api/v1/auth/token       — login, returns JWT
- GET  /api/v1/auth/me          — get current user profile (protected)
- PATCH /api/v1/auth/me         — update own profile (protected)

### Auth requirements
- register and token are public
- me endpoints require valid JWT

### Business rules
- Email must be unique (case-insensitive)
- Password minimum 8 characters
- Username 3-30 characters, alphanumeric + underscores only
- Return UserPublic (no email) for other users, UserPrivate (with email) for self

### Priority
Start with register + login + me. Update profile after.
```

### Example 3: Feature with File Uploads

```
I am building PortfolioAPI — a portfolio showcase backend.

The attached `production_reference.md` is the architecture blueprint.
The attached `rules_of_engagement.md` defines how you should work.

## Feature: Portfolio Projects with Image Gallery

### What it does
Users create portfolio projects with a title, description, tech stack tags,
and upload multiple images per project.

### Entities involved
- Project: title, description, live_url (optional), repo_url (optional),
  user_id, created_at
- ProjectImage: filename, original_name, project_id, sort_order
- ProjectTag: name (unique globally), many-to-many with Project
- Relationship: User has many projects. Project has many images.
  Project has many tags (M2M).

### Endpoints needed
- POST   /api/v1/projects                          — create project
- GET    /api/v1/projects                          — list all (paginated, filterable by tag)
- GET    /api/v1/projects/{id}                     — get with images + tags
- PATCH  /api/v1/projects/{id}                     — update details
- DELETE /api/v1/projects/{id}                     — delete project + cascade images
- POST   /api/v1/projects/{id}/images              — upload image(s)
- DELETE /api/v1/projects/{id}/images/{image_id}   — remove single image

### Auth requirements
- List and get are public
- Create, update, delete, upload require auth
- Only project owner can modify

### Business rules
- Max 10 images per project (jpg, png, webp only, max 5MB each)
- Tags are lowercase, created on-the-fly if they don't exist
- Deleting a project deletes all its images from disk + DB

### Priority
Start with Project CRUD + tags. Add image upload after I confirm the base works.
```

### Example 4: Adding a Feature to an Existing Project

```
I am continuing work on TaskFlow — a project management API.

The attached `production_reference.md` is the architecture blueprint.
The attached `rules_of_engagement.md` defines how you should work.

The project already has: User auth, Project CRUD, Task CRUD.

## Feature: Comments on Tasks

### What it does
Team members can comment on tasks to discuss progress, blockers, or decisions.

### Entities involved
- Comment: content, task_id, user_id, created_at, updated_at
- Relationship: A task has many comments. A comment belongs to one user and one task.

### Endpoints needed
- POST   /api/v1/tasks/{task_id}/comments    — add comment
- GET    /api/v1/tasks/{task_id}/comments    — list comments (paginated, newest first)
- PATCH  /api/v1/comments/{id}               — edit own comment
- DELETE /api/v1/comments/{id}               — delete own comment

### Auth requirements
- All endpoints require auth
- Only project members can view/add comments
- Only comment author can edit/delete

### Business rules
- Content: 1-2000 characters, required
- updated_at is set automatically on edit
- Deleting a task cascades to its comments

### Existing files to modify
- models/__init__.py — add Comment re-export
- schemas/__init__.py — add Comment schemas re-export
- api/router.py — add comments router

### Priority
Build it all — it's a small feature.
```

---

## Prompt Checklist

Before sending your feature prompt, verify:

- [ ] **Blueprint attached** — `production_reference.md` is included
- [ ] **Rules attached** — `rules_of_engagement.md` is included
- [ ] **Entities are clear** — field names, types, and relationships defined
- [ ] **Endpoints are listed** — HTTP method + path + purpose for each
- [ ] **Auth is specified** — which routes are public, which need auth, ownership rules
- [ ] **Business rules stated** — constraints, validations, edge cases
- [ ] **Priority is set** — what to build first, what to defer
- [ ] **Existing context** (if applicable) — what's already built, what files exist

---

## Tips

**Be specific about fields.** "A task has a title and status" is vague. "title (str, max 200, required), status (enum: todo/in_progress/done, default todo)" gives exact schemas.

**State relationships explicitly.** "User has many projects" tells the AI to set up `cascade="all, delete-orphan"`, `back_populates`, and `selectinload`.

**Set priority.** Building everything at once leads to untested code. Request the core first, verify it, then layer on complexity.

**Mention existing context.** If the project already has models or routes, say so. Otherwise you'll get duplicate `User` models and conflicting router wiring.

**One feature per prompt.** Don't ask for auth + tasks + comments in one go. Build incrementally — each feature gets its own prompt, its own review, its own tests passing.
