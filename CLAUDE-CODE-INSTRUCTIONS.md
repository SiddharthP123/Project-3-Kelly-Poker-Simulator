# CLAUDE CODE/AI ASSISTANT INSTRUCTIONS - WORKFLOW ORCHESTRATION:

---

# User Information:

**Hardware:** MacBook Air Apple M2, 2022.
**Last Updated:** March 23, 2026.
**Owner:** Siddharth Premanand ([@SiddharthP123](https://github.com/SiddharthP123)).
**For:** Claude Code / Cline / Cursor.

---

## Context:

This file contains instructions for AI coding assistants (Claude Code, Cline, Cursor) working on my projects.
**Note:** Copy this file to the root of each project when starting development.

---

## Table of Contents:

- [1. Plan Mode Default:](#1-plan-mode-default)
- [2. Subagent Strategy:](#2-subagent-strategy)
- [3. Self-Improvement Loop:](#3-self-improvement-loop)
- [4. Verification Before Done:](#4-verification-before-done)
- [5. Demand Elegance (Balanced):](#5-demand-elegance-balanced)
- [6. Autonomous Bug Fixing:](#6-autonomous-bug-fixing)
- [7. Task Management:](#7-task-management)
- [8. Core Principles:](#8-core-principles)
- [9. Reference Files:](#9-reference-files)
- [10. Security Requirements:](#10-security-requirements)
- [11. Git Workflow:](#11-git-workflow)
- [12. Agentic Behaviour Guardrails:](#12-agentic-behaviour-guardrails)
- [13. Context Window Management:](#13-context-window-management)
- [14. Testing Requirements:](#14-testing-requirements)
- [15. Future Integrations:](#15-future-integrations)

---

## 1. Plan Mode Default:

- Enter plan mode for ANY non-trivial task (3+ steps or architectural decisions).
- If something goes sideways, STOP and re-plan immediately.
- Use plan mode for verification steps, not just building.
- Write detailed specs upfront to reduce ambiguity.

---

## 2. Subagent Strategy:

- Use subagents liberally to keep main context window clean.
- Offload research, exploration, and parallel analysis to subagents.
- For complex problems, throw more compute at it via subagents.
- One task per subagent for focused execution.

---

## 3. Self-Improvement Loop:

- After ANY correction from me: update `tasks/lessons.md` with the pattern.
- Write rules for yourself that prevent the same mistake.
- Ruthlessly iterate on these lessons until mistake rate drops.
- Review lessons at session start for relevant project.

---

## 4. Verification Before Done:

- Never mark a task complete without proving it works.
- Diff behavior between main and your changes when relevant.
- Ask yourself: "Would a staff engineer approve this?".
- Run tests, check logs, demonstrate correctness.

---

## 5. Demand Elegance (Balanced):

- For non-trivial changes: pause and ask "is there a more elegant way?".
- If a fix feels hacky: "Knowing everything I know now, implement the elegant solution".
- Skip this for simple, obvious fixes -- don't over-engineer.
- Challenge your own work before presenting it.

---

## 6. Autonomous Bug Fixing:

- When given a bug report: just fix it. Don't ask for hand-holding.
- Point at logs, errors, failing tests -- then resolve them.
- Zero context switching required from me.
- Go fix failing CI tests without being told how.

---

## 7. Task Management:

### 7.1 Workflow:

1. **Plan First:** Write plan to `tasks/todo.md` with checkable items.
2. **Verify Plan:** Check in before starting implementation.
3. **Track Progress:** Mark items complete as you go.
4. **Explain Changes:** High-level summary at each step.
5. **Document Results:** Add review section to `tasks/todo.md`.
6. **Capture Lessons:** Update `tasks/lessons.md` after corrections.

### 7.2 File Structure:

- Putting task tracking within the repository (`project-root/tasks/`).
- `tasks/todo.md`: Current tasks and progress.
- `tasks/lessons.md`: Lessons learnt from mistakes.

---

## 8. Core Principles:

### 8.1 Simplicity First:

- Make every change as simple as possible.
- Impact minimal code.
- Avoid over-engineering.

### 8.2 No Laziness:

- Find root causes, not symptoms.
- No temporary fixes or hacks.
- Senior developer standards at all times.

### 8.3 Minimal Impact:

- Only touch what's necessary.
- No side effects or new bugs.
- Test thoroughly before marking complete.

---

## 9. Reference Files:

### 9.1 DEVELOPMENT ENVIRONMENT:

- **Location:** `~/Desktop/web-development/dev-docs/DEVELOPMENT-ENVIRONMENT.md`.

**Contains:**

- Hardware: MacBook Air M2, 2022.
- Node.js: v25.8.1.
- npm: 11.11.0.
- Git configuration.
- VS Code extensions.
- Terminal setup (iTerm2, Oh My Zsh, Powerlevel10k).
- CLI tools (tldr, tree, bat, fzf).

### 9.2 CODING PREFERENCES:

- **Location:** `~/Desktop/web-development/dev-docs/CODING-PREFERENCES.md`.

**Contains:**

- Code style (single quotes, no semicolons, 4-space indentation).
- Naming conventions (PascalCase components, kebab-case files, camelCase variables).
- File structure preferences (Next.js App Router layout).
- React patterns (functional components, early returns, custom hooks).
- UI components: shadcn/ui for foundational components, 21st.dev for design/marketing sections.
- Comment guidelines and JSDoc standards.
- Git commit message format (Conventional Commits).

### 9.3 PROJECT STACK:

- **Location:** `~/Desktop/web-development/dev-docs/PROJECT-STACK.md`.

**Contains:**

- Frontend: Next.js (App Router), Tailwind CSS, shadcn/ui, 21st.dev.
- Backend: Next.js API Routes + Firebase.
- Database: Firebase Firestore.
- Auth: Firebase Auth.
- Hosting: Vercel.
- Environment variable names and structure.

### 9.4 COMMON ISSUES:

- **Location:** `~/Desktop/web-development/dev-docs/COMMON-ISSUES.md`.

**Contains:**

- Previously encountered errors and solutions.
- Check here before asking me about errors.

### 9.5 FUTURE INTEGRATIONS:

- **Location:** `~/Desktop/web-development/dev-docs/FUTURE-INTEGRATIONS.md`.

**Contains:**

- Planned integrations that are deliberately deferred — do not implement unless explicitly instructed.
- Ruflo multi-agent orchestration (deferred until Claude Code alone becomes the bottleneck).
- Python microservice for financial models (QuantLib, pyfolio, pmdarima — deferred until financial calculator features are built).
- Claude Code agents folder with specialist instruction files (deferred until codebase has real structure).
- Firebase Storage (deferred until file upload features are needed — requires Blaze plan upgrade).
- Firebase Admin SDK (deferred until first protected API route is needed).

**Important for Claude Code:** Do NOT proactively implement any of these integrations. Each has a specific trigger condition defined in `FUTURE-INTEGRATIONS.md`. Only implement when explicitly instructed to do so.

---

## 10. Security Requirements:

### 10.1 Rate Limiting:

**All Public Endpoints Must Have:**

- IP-based rate limiting (sensible defaults: 100 requests/15min for general endpoints).
- User-based rate limiting (authenticated users: 1000 requests/hour).
- Graceful 429 responses with `Retry-After` header.
- Different limits for different endpoint types:
  - Auth endpoints: 5 attempts/15min.
  - API reads: 100 requests/15min.
  - API writes: 50 requests/15min.
  - File uploads: 10 uploads/hour.

**EXAMPLE:**

```js
// Example for Next.js API routes
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
```

### 10.2 Input Validation & Sanitization:

1. All User Inputs Must Be:

- Schema-based validated (use Zod).
- Type-checked at runtime.
- Length-limited (strings, arrays, objects).
- Sanitized for XSS attacks.
- Reject unexpected fields (strict mode).

2. Never Trust Client-Side Validation:

- Always validate on the server/backend.
- Never make direct database calls from client (especially Firebase).
- Use API routes as intermediary layer.

**EXAMPLE:**

```js
import { z } from 'zod';

const userInputSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100).trim(),
  age: z.number().int().min(0).max(150).optional(),
});

try {
  const validatedData = userInputSchema.parse(userInput);
} catch (error) {
  return res.status(400).json({ error: error.errors });
}
```

### 10.3 API Key & Secret Management:

1. Mandatory Practices:

- ❌ NEVER hardcode API keys, secrets, or credentials in code.
- ✅ ALWAYS use environment variables (.env.local).
- ✅ Store in .env.local and add to .gitignore.
- ✅ Use different keys for development/staging/production.
- ✅ Rotate keys regularly (quarterly minimum).
- ✅ Use secret management services for production (Vercel Env Vars).

2. Client vs Server:

- Client-side: Only use `NEXT_PUBLIC_*` variables for non-sensitive data.
- Server-side: Keep sensitive keys server-only (no `NEXT_PUBLIC_` prefix).
- Firebase: Use server-side Admin SDK for sensitive operations.

**EXAMPLE STRUCTURE:**

```bash
# .env.local

# Client-side (safe to expose)
NEXT_PUBLIC_FIREBASE_API_KEY=xxx
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=xxx
NEXT_PUBLIC_FIREBASE_PROJECT_ID=xxx
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=xxx
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=xxx
NEXT_PUBLIC_FIREBASE_APP_ID=xxx

# Server-side only (NEVER expose)
FIREBASE_ADMIN_PRIVATE_KEY=xxx
FIREBASE_ADMIN_CLIENT_EMAIL=xxx
```

### 10.4 Authentication & Password Security:

1. Preferred Approach - Firebase Auth (Managed):

- ✅ Use Firebase Auth for all authentication.
- ✅ Let Firebase manage password hashing, storage, and security.
- ✅ App only verifies JWTs — never handle raw passwords.
- ✅ Support email/password and Google OAuth.

2. Token Management:

- Use short-lived access tokens (Firebase default: 1 hour).
- Store tokens securely (Firebase SDK handles this automatically).
- Verify tokens on every protected API route using Firebase Admin SDK.

**EXAMPLE — protecting an API route:**

```js
import { adminAuth } from '@/lib/firebase-admin';

export async function GET(request) {
  const authHeader = request.headers.get('Authorization');
  const token = authHeader?.split('Bearer ')[1];

  if (!token) {
    return Response.json({ error: 'Unauthorised' }, { status: 401 });
  }

  try {
    const decodedToken = await adminAuth.verifyIdToken(token);
    // Proceed with decodedToken.uid
  } catch (error) {
    return Response.json({ error: 'Invalid token' }, { status: 401 });
  }
}
```

### 10.5 OWASP Best Practices:

Follow OWASP Top 10:

1. Broken Access Control:

- Verify user permissions on every request.
- Implement role-based access control (RBAC).
- Check ownership before allowing modifications.

2. Cryptographic Failures:

- Use HTTPS everywhere (Vercel enforces this automatically).
- Encrypt sensitive data at rest.

3. Injection:

- Use Firestore SDK (parameterized by design — no raw queries).
- Sanitize all user inputs with Zod.

4. Insecure Design:

- Security by design, not as afterthought.
- Principle of least privilege on Firestore security rules.

5. Security Misconfiguration:

- Never use Firebase in test mode in production.
- Keep Firestore security rules restrictive — deny by default.
- Keep dependencies updated.
- Use security headers (CSP, HSTS, X-Frame-Options).

6. Vulnerable Components:

- Regularly update dependencies (`npm audit`).
- Use Dependabot for automated updates.
- Remove unused dependencies.

7. Authentication Failures:

- Implement MFA where possible (Firebase Auth supports this).
- Use secure session management.

8. Software & Data Integrity:

- Verify package integrity (package-lock.json).
- Use signed commits.
- Implement CI/CD security checks.

9. Logging & Monitoring:

- Log security events.
- Monitor for suspicious activity.
- Never log sensitive data (tokens, passwords).

10. Server-Side Request Forgery (SSRF):

- Validate and sanitize URLs.
- Use allowlists for external requests.

### 10.6 Security Headers:

Implement these in `next.config.js`:

```js
const securityHeaders = [
  { key: 'X-DNS-Prefetch-Control', value: 'on' },
  {
    key: 'Strict-Transport-Security',
    value: 'max-age=63072000; includeSubDomains; preload',
  },
  { key: 'X-Frame-Options', value: 'SAMEORIGIN' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'X-XSS-Protection', value: '1; mode=block' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  {
    key: 'Permissions-Policy',
    value: 'camera=(), microphone=(), geolocation=()',
  },
];
```

### 10.7 Firebase Security Rules:

Always write restrictive Firestore rules. Default deny, explicit allow:

```js
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    // Deny everything by default
    match /{document=**} {
      allow read, write: if false;
    }

    // Users can only read/write their own document
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }

    // Courses readable by authenticated users, writable by admin only
    match /courses/{courseId} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && request.auth.token.admin == true;
    }
  }
}
```

### 10.8 Security Checklist:

Before Deploying:

- All API keys in environment variables (Vercel dashboard).
- No hardcoded secrets in code.
- Rate limiting implemented on public endpoints.
- Input validation on all user inputs (Zod).
- Authentication via Firebase Auth.
- HTTPS enforced (automatic on Vercel).
- Security headers configured in next.config.js.
- Dependencies updated (`npm audit` clean).
- No console.logs with sensitive data.
- Error messages don't leak system info.
- CORS properly configured.
- File upload validation (type, size, content).
- XSS prevention (sanitized outputs).
- Firebase security rules reviewed and restrictive.
- `.env.local` is in `.gitignore`.

### 10.9 Security Comments:

Always Include Comments For:

- Security-critical code sections.
- Why certain validation rules exist.
- Rate limiting thresholds reasoning.
- Authentication flow explanations.

**EXAMPLE:**

```js
// Security: Limit login attempts to prevent brute force attacks
// 5 attempts per 15 minutes per IP address
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: 'Too many login attempts, please try again later.',
});
```

### 10.10 Do Not Break Existing Functionality:

When Implementing Security:

- Run full test suite before and after changes.
- Test all user flows (registration, login, API calls).
- Verify existing features still work.
- Check for performance impact.
- Test rate limiting doesn't block legitimate users.
- Ensure error messages are user-friendly.

---

## 11. Git Workflow:

### 11.1 Branch Naming:

Use these prefixes consistently:

- `feature/short-description` — new features.
- `fix/short-description` — bug fixes.
- `chore/short-description` — dependency updates, config, tooling.
- `refactor/short-description` — code restructuring with no behaviour change.
- `hotfix/short-description` — urgent production fixes.

**Examples:** `feature/user-auth`, `fix/login-redirect`, `chore/update-deps`.

### 11.2 Commit Message Format:

Follow Conventional Commits:

```
<type>(optional scope): short description

Optional longer body explaining WHY, not what.
```

**Types:** `feat`, `fix`, `chore`, `refactor`, `test`, `docs`, `style`, `perf`.

**Examples:**

- `feat(auth): add Google OAuth login`
- `fix(api): correct rate limit header on 429 response`
- `chore: update dependencies to latest`

### 11.3 Commit Rules:

- ❌ NEVER commit directly to `main` or `master`.
- ❌ NEVER commit `.env` files or secrets.
- ✅ Commit in small, logical, atomic units.
- ✅ Each commit should pass tests and leave the codebase in a working state.
- ✅ Write commit messages in the imperative: "add feature" not "added feature".
- ✅ Reference issue numbers where relevant: `fix(auth): resolve token expiry (#42)`.

### 11.4 Pull Request Standards:

- Always open a PR for review before merging to `main`.
- PR title should follow the same Conventional Commits format.
- Include a short description of what changed and why.
- Link to any relevant issues or tickets.
- Ensure all CI checks pass before merging.

---

## 12. Agentic Behaviour Guardrails:

### 12.1 Actions That Require My Explicit Approval:

- ❌ NEVER delete files or directories without confirming with me first.
- ❌ NEVER run destructive shell commands (`rm -rf`, `DROP TABLE`, database wipes, etc.) without explicit approval.
- ❌ NEVER push to remote branches or open PRs without asking first.
- ❌ NEVER modify `.env` files, secrets, or credentials without confirming.
- ❌ NEVER install new dependencies without checking with me first.
- ❌ NEVER make changes outside the scope of the current task without flagging it.
- ❌ NEVER modify Firebase security rules without explicit approval.

### 12.2 Always Safe to Do Autonomously:

- ✅ Read files, search codebases, and explore the repo structure.
- ✅ Run tests and linting.
- ✅ Create new files within the project scope.
- ✅ Make and stage code changes (but not commit/push without approval).
- ✅ Look up documentation or research solutions.

### 12.3 When in Doubt:

- Default to asking rather than acting.
- Describe what you intend to do and why, then wait for a green light.
- Prefer reversible actions over irreversible ones.

---

## 13. Context Window Management:

### 13.1 Proactively Flag Context Limits:

- If you are approaching your context window limit, **stop and tell me immediately** — do not silently degrade, hallucinate, or start losing track of earlier instructions.
- Say something like: _"I'm approaching my context limit. I recommend starting a new session and I'll summarise where we are."_

### 13.2 Session Handoff:

When context is getting full, provide a concise handoff summary including:

1. What was accomplished this session.
2. Current state of the codebase / task.
3. What the next steps are.
4. Any open decisions or blockers.
5. Relevant file paths to re-read in the new session.

### 13.3 Staying Focused:

- Don't load unnecessary files into context.
- Summarise long files rather than reading them in full when possible.
- Keep subagent tasks scoped and isolated to prevent context bleed.

---

## 14. Testing Requirements:

### 14.1 Preferred Testing Framework:

- **Unit & Integration Tests:** [Vitest](https://vitest.dev/) (preferred for Next.js projects).
- **Component Tests:** React Testing Library alongside Vitest.
- **E2E Tests:** Playwright.
- If a project already uses Jest, continue with Jest for consistency.

### 14.2 Before Marking Complete:

- Code runs without errors.
- Functionality works as specified.
- Edge cases handled.
- No console errors or warnings.
- Responsive design tested (if applicable).
- Accessibility considered.
- Performance acceptable.

### 14.3 Before Presenting Code, Verify:

- Follows coding preferences from `CODING-PREFERENCES.md`.
- No hardcoded values (use constants/env vars).
- Error handling implemented.
- Comments added for complex logic.
- No unused imports or variables.
- Prettier formatting applied (matches `.prettierrc`).
- ESLint warnings resolved.
- Responsive and accessible (for UI).
- shadcn/ui used for foundational components, 21st.dev for design sections.

---

## 15. Future Integrations:

These are planned additions that are **deliberately deferred**. Do NOT implement any of these unless explicitly instructed by me. Each has a specific trigger condition — implementing them too early adds complexity without value.

Full details for each integration are in `~/Desktop/web-development/dev-docs/FUTURE-INTEGRATIONS.md`.

### 15.1 Ruflo — Multi-Agent Orchestration:

- **What:** Open-source framework that runs on top of Claude Code as an MCP server, orchestrating 60+ specialised agents in parallel swarms.
- **Do not implement until:** Running parallel workstreams across frontend, backend, and tests simultaneously, and Claude Code alone is the bottleneck.
- **Install when ready:** `claude mcp add claude-flow -- npx claude-flow@latest mcp start`

### 15.2 Python Microservice — Financial Models:

- **What:** A separate FastAPI server running Python financial libraries (QuantLib, pyfolio, pmdarima). Next.js API routes call it via HTTP and receive JSON results.
- **Do not implement until:** Building a Prospect feature that requires financial modelling (portfolio analyser, yield curve visualiser, returns forecaster, options pricer).
- **Architecture:** `Next.js API Route → FastAPI Python Server → financial model → JSON response`

### 15.3 Claude Code Agents Folder:

- **What:** A dedicated `agents/` folder at the project root with specialist instruction files — `frontend.md`, `backend.md`, `database.md`, `testing.md`, `devops.md`, `python.md`.
- **Do not implement until:** The codebase has real structure and substance to reference. Generic agent files before this point are unhelpful.

### 15.4 Firebase Storage:

- **What:** Firebase file storage for user-uploaded content (profile pictures, course assets, documents).
- **Do not implement until:** Building a feature that requires file uploads.
- **Requires:** Upgrading Firebase to Blaze (pay-as-you-go) plan first.

### 15.5 Firebase Admin SDK:

- **What:** Server-side Firebase SDK for verifying user tokens and performing privileged operations in API routes.
- **Do not implement until:** Building the first Next.js API route that needs server-side auth verification.
- **Setup:** Firebase Console → Project Settings → Service Accounts → Generate new private key. Add `FIREBASE_ADMIN_PROJECT_ID`, `FIREBASE_ADMIN_CLIENT_EMAIL`, `FIREBASE_ADMIN_PRIVATE_KEY` to `.env.local`.

---

## EXTRA: Project Setup Instructions:

When starting a new project with AI assistance:

### 1. Copy This File to Project Root:

```bash
cp ~/Desktop/web-development/dev-docs/CLAUDE-CODE-INSTRUCTIONS.md ./
```

### 2. Create Task Management Files:

```bash
mkdir tasks
touch tasks/todo.md
touch tasks/lessons.md
```

### 3. Initialise todo.md:

```md
# Project Tasks

## Current Sprint:

- [ ] Task 1
- [ ] Task 2

## Completed:

- [x] Project setup

## Backlog:

- [ ] Future task
```

### 4. Initialise lessons.md:

```md
# Lessons Learned

## Template:

- **Date:** YYYY-MM-DD
- **Mistake:** [What went wrong]
- **Correction:** [What was done to fix it]
- **Lesson:** [Rule to prevent this in the future]
- **Applied To:** [Where this lesson applies]
```

---

## EXTRA: Communication Style:

1. When Explaining Code:

- Start with high-level overview.
- Explain "why" not just "what".
- Use comments in code for complex logic.
- Provide examples when helpful.

2. When Asking for Clarification:

- Be specific about what's unclear.
- Suggest possible interpretations.
- Ask targeted questions.

3. When Reporting Progress:

- Summarize what was done.
- Highlight any deviations from plan.
- Note any blockers or concerns.
- Confirm next steps.

---

## EXTRA: Security & Best Practices:

**Always:**
✅ Use environment variables for secrets (.env.local).
✅ Validate user inputs with Zod.
✅ Handle errors gracefully.
✅ Follow principle of least privilege.
✅ Keep dependencies updated.
✅ Write secure, production-ready code.
✅ Write restrictive Firebase security rules.

**Never:**
❌ Hardcode API keys or secrets.
❌ Commit .env files.
❌ Use deprecated packages.
❌ Skip error handling.
❌ Leave console.logs in production code.
❌ Ignore security warnings.
❌ Use Firebase in test/open mode in production.

---

## EXTRA: Emergency Protocols:

1. If Build Breaks:

- Identify the breaking change.
- Check error logs thoroughly.
- Attempt automatic fix.
- If can't fix in 5 minutes: revert and re-plan.
- Document issue in `tasks/lessons.md`.

2. If Stuck:

- Review plan and verify understanding.
- Check `COMMON-ISSUES.md` for similar problems.
- Research documentation/Stack Overflow.
- If still stuck after 15 minutes: ask me for guidance.
- Document solution in `tasks/lessons.md`.

---

## EXTRA: Performance, Accessibility, and Documentation Guidelines:

**PERFORMANCE:**

1. Optimize For:

- Fast initial page load.
- Minimal bundle size.
- Efficient re-renders (React).
- Lazy loading where appropriate.
- Next.js Image component for all images (`next/image`).

2. Monitor:

- Bundle size (use Import Cost extension).
- Network requests.
- Console warnings.
- Memory usage.

**ACCESSIBILITY:**

1. Always Include:

- Semantic HTML elements.
- Alt text for images.
- ARIA labels where needed.
- Keyboard navigation support.
- Sufficient color contrast.
- Responsive text sizing.
- shadcn/ui components are accessible by default — use them.

**DOCUMENTATION:**

1. Code Comments:

- Explain complex algorithms.
- Document non-obvious decisions.
- Add TODOs for future improvements.
- Use JSDoc for public functions.

2. README Updates:

- Keep setup instructions current.
- Document new features.
- Update dependencies list.
- Add troubleshooting sections.

---

## FINAL CHECKLIST:

- All tasks in `todo.md` marked complete.
- Code reviewed against principles.
- Tests passing (if applicable).
- Documentation updated.
- No console errors or warnings.
- Responsive design verified.
- Performance acceptable.
- Security considerations addressed.
- Firebase security rules reviewed.
- Lessons captured in `lessons.md`.
- Ready for my review.

---
