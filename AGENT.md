# AGENTS.md

# AI Test Guy — Architecture & Refactor Guide

## Project Overview

AI Test Guy is an SAT tutoring and SAT practice platform built as a full-stack web application.

The system combines:
- a React frontend SPA
- a FastAPI backend
- PostgreSQL relational data models
- Supabase authentication
- AI tutoring agents powered by OpenAI and tutoring-specific tooling

The project is NOT a microservices architecture.

The intended architecture is a modular monolith:
one deployable backend application with clearly separated internal modules and responsibilities.

The backend already contains significant business logic and should remain the primary source of truth for:
- SAT tutoring logic
- exam progression
- scoring
- adaptive modules
- tutor workflows
- survival mode logic
- daily task generation
- user progression/state
- AI orchestration

---

# Current High-Level Architecture

Frontend (React + Vite)
    ↓
API Layer (FastAPI)
    ↓
Service / Domain Layer
    ↓
Database + AI Tutor Agents + External Services

External systems:
- Supabase Auth
- OpenAI APIs
- WolframAlpha
- PostgreSQL
- pgvector embeddings

---

# Core Architectural Principles

## 1. Keep Backend Logic In The Backend

The frontend should NOT:
- implement SAT grading logic
- implement adaptive exam logic
- implement tutor reasoning logic
- duplicate backend validation
- directly manipulate database concepts

The backend should remain responsible for:
- tutoring decisions
- exam generation
- scoring
- hints/explanations
- tutor orchestration
- business rules
- persistence rules

Frontend should focus on:
- rendering UI
- managing local interaction state
- navigation
- API communication
- animations/loading/error states

---

# 2. Maintain Modular Monolith Structure

Do NOT split the project into microservices.

Do NOT introduce unnecessary distributed systems complexity.

Prefer:
- clearly separated modules
- service layers
- helper utilities
- domain-oriented organization

over:
- multiple backend services
- event buses
- overly abstract enterprise patterns

This is a startup-style architecture optimized for velocity and maintainability.

---

# 3. Refactor For Clarity Over Cleverness

Prioritize:
- readability
- maintainability
- explicit naming
- small functions
- predictable flow
- low coupling

Avoid:
- deeply nested logic
- giant React components
- duplicated API calls
- hidden side effects
- unnecessary abstraction layers

---

# Frontend Architecture

## Frontend Responsibilities

The React frontend is responsible for:
- routing/navigation
- rendering SAT questions and tutor responses
- displaying timers/exam state
- user interactions
- local UI state
- optimistic UI where appropriate
- API communication
- auth/session persistence

The frontend should consume clean backend APIs.

---

# Recommended Frontend Structure

src/
  components/
  pages/
  layouts/
  hooks/
  contexts/
  services/
  api/
  utils/
  constants/
  types/

---

# Frontend Refactor Goals

## Components
- break large components into smaller focused components
- separate layout/UI from business logic
- avoid excessive prop drilling

## API Calls
Move all API requests into:
- services/
or
- api/

Avoid raw fetch calls inside page components.

## State Management
Keep:
- local UI state local
- shared app state centralized

Avoid unnecessary global state.

## Tutor Rendering
Tutor rendering should remain presentation-focused:
- markdown rendering
- KaTeX rendering
- chat display
- streaming visualization

Tutor reasoning belongs in backend services.

---

# Backend Architecture

The FastAPI backend is the application's core domain layer.

The backend is NOT just a transport API.

It contains:
- adaptive SAT exam systems
- tutor orchestration
- practice logic
- scoring logic
- survival mode systems
- recommendation systems
- AI tutoring services

---

# Recommended Backend Structure

app/
  api/
  services/
  tutors/
  sat/
  exams/
  practice/
  survival/
  users/
  auth/
  db/
  models/
  schemas/
  prompts/
  utils/

---

# Backend Module Responsibilities

## api/
FastAPI route definitions only.

Should:
- validate requests
- call services
- return responses

Should NOT:
- contain large business logic
- contain prompt engineering
- directly manipulate DB logic

---

## services/
Core business logic layer.

Contains:
- orchestration logic
- exam progression
- scoring
- recommendation systems
- task generation
- tutor workflows

---

## tutors/
AI tutor systems and tutoring agents.

Examples:
- ConversationalSATTutor
- ConversationalEnglishSATTutor
- PracticeQuestionTutor

Tutor agents should be modular and isolated.

---

## sat/
SAT-specific logic and metadata.

Examples:
- SAT domains
- difficulty rules
- scoring mappings
- adaptive progression logic

---

## db/
Database connection/session management.

---

## models/
SQLAlchemy models.

Keep models focused on persistence structure.

Avoid placing heavy business logic inside models.

---

## schemas/
Pydantic request/response models.

Used to standardize API contracts.

---

# AI System Design

The AI tutoring system should evolve toward:

Frontend
→ API Route
→ Tutor Service
→ Specialized Tutor Agent
→ LLM + Tooling
→ Structured Tutor Response
→ Frontend Renderer

Keep:
- prompts
- tutor instructions
- parsing
- reasoning

inside backend tutor systems.

Avoid putting prompt engineering inside React components.

---

# Auth Architecture

Authentication uses:
- Supabase auth on frontend
- Supabase token verification on backend
- local Postgres user synchronization

This hybrid model is intentional.

Do NOT remove backend auth verification.

---

# Database Architecture

Primary database: PostgreSQL

Current domain entities include:
- users
- SAT questions
- mock exams
- mock exam sections
- mock exam questions
- practice attempts
- daily tasks
- survival sessions
- user performance
- college recommendations

Maintain relational consistency.

Avoid premature NoSQL migration.

---

# API Design Guidelines

All API routes should:
- be explicit
- return predictable JSON
- use typed schemas
- separate transport from logic

Avoid:
- massive all-purpose endpoints
- inconsistent response shapes
- frontend-specific backend hacks

---

# Refactor Priorities

## Highest Priority
1. Reduce large component complexity
2. Centralize API calls
3. Separate UI from business logic
4. Improve naming consistency
5. Modularize tutor systems
6. Standardize backend service structure

## Medium Priority
1. Add typed interfaces
2. Improve error handling
3. Add response schemas
4. Reduce duplicated utility logic

## Low Priority
1. Performance optimizations
2. Advanced caching
3. Infrastructure scaling

Focus on maintainability first.

---

# Important Constraints

## Do NOT:
- convert into microservices
- over-engineer abstractions
- introduce unnecessary frameworks
- move tutoring logic into frontend
- create excessive global state
- optimize prematurely

## Prefer:
- simple patterns
- explicit flow
- modular services
- readable code
- stable APIs

---

# Ideal Long-Term Direction

The project should evolve into:

- clean modular monolith backend
- reusable tutoring engine
- scalable SAT domain model
- maintainable React frontend
- isolated tutor agents/services
- clean API boundaries
- production-ready AI tutoring platform

without sacrificing startup iteration speed.

