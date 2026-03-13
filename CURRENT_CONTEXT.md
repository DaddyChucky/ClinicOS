# CURRENT_CONTEXT.md

## Product Summary

This repository now implements **ClinicOS**, a clinic operations SaaS product for dental and medical practices.

Primary positioning:
- **ClinicOS**
- **ClinicOS AI**
- **Practice Desk**
- **Operations Console**
- Tagline: **The operating system for modern dental and medical practices.**

## Core Experiences

### `/`
The homepage has been redesigned to feel like a polished SaaS landing/entry page rather than an MVP.

Implemented behavior:
- Premium hero treatment with stronger typography, spacing, gradients, and visual depth
- Only two primary entry points:
  - **Practice Desk**
  - **Operations Console**
- Updated branding and copy throughout
- Better CTA hierarchy and calmer visual presentation

### `/workspace`
This route is the client-facing **Practice Desk** experience.

Implemented behavior:
- Rebranded header with:
  - back arrow to `/`
  - ClinicOS / Practice Desk branding
  - **Operations Console** button on the right
- Header fade now spans the full header surface
- Heavily improved workspace shell styling
- Three-column layout:
  - left column: ClinicOS AI description, guidance, recent chats
  - middle column: active chat only
  - right column: suggested scenarios, then **Practice Profile**
- Removed the old **Open Priorities** card
- Active chat now includes a fast **New Chat** action plus a user delete action
- Blank startup chats do not show delete actions until the chat has actual message activity
- Practice Desk is now support-only:
  - software questions
  - upgrade guidance
  - billing FAQs
  - escalation routing to a human specialist
- Practice Desk no longer handles sales, outreach, or marketing requests inside the main chat
- Practice Desk respects admin chat suspension state and disables typing when the chat is turned offline
- Practice Profile no longer shows the unused plan field or duplicate Location / Locations fields
- Practice Profile and Operations Console now share the same PMS / EHR explainer modal
- Practice Desk modals are fully readable and close when the user clicks outside them
- Human escalation now shows a temporary top confirmation banner, then keeps a persistent in-chat queue card that explains ClinicOS AI is disconnected and whether the chat is still waiting in queue or already has a human joined
- Recent chat cards now include in-list delete actions in addition to the active-chat delete button

### `/admin`
This route is the **Operations Console**.

Implemented behavior:
- Updated admin shell branding to ClinicOS / Operations Console
- Admin header now uses a back button pattern aligned to Practice Desk
- Header fade now spans the full header surface across admin views
- Added skeleton loading states across admin views
- Added storytelling / guidance cards to the specialist admin dashboards
- Main overview now uses:
  - scrollable recent chat rail
  - in-list delete actions directly from recent chat cards
  - editable chat-specific **Practice Profile**
  - **ClinicOS AI Triage Agent** controls with:
    - active chat power switch
    - all chats power switch for the ClinicOS AI Triage Agent
  - **Orchestration Logs** focused on Live vs Offline workstream state
  - deleted chat archive with admin-viewable transcript and audit modal
- `/admin/support` and `/admin/review` now point to the same merged **Review Queue** for human takeover of escalated Practice Desk chats
- The merged queue shows the full chat-specific Practice Profile, transcript, and audit trail for each escalated chat, and human replies are sent directly back into Practice Desk
- Archived chats are excluded from the live Review Queue and remain available only in the deleted chat archive / audit flow
- The Review Queue now only shows explicit Practice Desk human-handoff requests for support chats and dedupes active queue state down to one visible entry per chat
- The admin header now shows a live Review Queue notification count for chats still waiting in the human queue
- The duplicate header-level Review Queue button was removed; the single Review Queue button now lives in the main admin navigation between Operations Console and Sales & Outreach and carries the notification badge
- Admin pages no longer create chats automatically; only Practice Desk can create a new chat
- Practice Profile inputs now use example placeholders, a single **Location** field, and no unused plan field
- Admin can delete any chat; deleted chats disappear from the normal rail but remain in the audit archive

### `/admin/sales`
This route is now a dedicated **Sales & Outreach** operator workspace rather than a review pipeline.

Implemented behavior:
- Reframed the page around researching and qualifying dental / medical clinic prospects
- Replaced the old inline how-to card with a short guidance section and a modal:
  - **How Sales & Outreach Tool Works**
- Guidance now sits in the left rail above the scrollable **Research History** list
- Removed the old review-gated draft workflow from the admin tool
- Added a scrollable **Research History** rail for older prospect research runs
- Added **Suggested Researches** for realistic dental and medical prospecting targets
- Inputs now start empty and use example placeholders rather than static prefilled values
- Researching now shows an in-view skeleton state and the workspace auto-scrolls to the new research brief when it is ready
- Saved research can be permanently deleted from history through a confirmation modal, with no archive
- Research history cards now also support in-list delete actions
- Personalized outreach now includes a direct **Draft Email** action via `mailto:`
- The visible outreach result now focuses on the final email only and no longer shows a separate personalization-notes panel
- Outreach email quality was tightened in both the live and fallback generation paths, and the message now signs off as **- ClinicOS Team**
- Sales outputs are now saved for history without creating admin review work

### `/admin/marketing`
This route is now a dedicated marketing planning workspace without an approval queue.

Implemented behavior:
- Replaced the old inline how-to card with a short guidance section and a modal:
  - **How Marketing Tool Works**
- Guidance now sits in the left rail above saved **Campaign History**
- Removed the old admin review/approval framing from campaign generation
- Generated campaigns now appear as saved **Campaign History** instead of review-gated drafts
- Inputs now start from example placeholders and clearer objective framing instead of static prefilled values
- Campaign generation now shows an in-view skeleton state and auto-scrolls to the finished plan
- Saved campaign plans can be permanently deleted from Marketing history through a confirmation modal, with no archive
- Campaign history cards now also support in-list delete actions
- Removed the old **Persona Snapshot** panel from Marketing
- The campaign plan card now includes a working **PDF** print/download action for exporting the plan locally
- The campaign plan card also includes a **Draft Email** action via `mailto:`
- Added **Suggested Campaigns** for realistic clinic growth use cases
- Marketing outputs generated from the admin tool no longer create admin review work

## ClinicOS AI Behavior

The main assistant experience is no longer driven by the old hardcoded response strings in the orchestrator.

Implemented behavior:
- Added a dedicated **ClinicOS AI response composition layer**
- The final user-facing response is now synthesized from:
  - recent chat history
  - inferred practice memory
  - support task packets
  - escalation state
  - loop/unresolved state
- Responses are intended to feel more conversational and multi-paragraph instead of short template blocks
- Inside Practice Desk, the assistant now handles support-only workflows:
  - software support questions
  - upgrade guidance
  - billing FAQs
  - human escalation routing
- If the user asks for sales, outreach, or marketing help in Practice Desk, ClinicOS AI redirects them to the specialist tools in Operations Console
- The final response generation uses the OpenAI agent path when available, with a polished local fallback if live generation is unavailable

## Persistent Chat Memory

Chat memory is now more useful and more visible.

Implemented behavior:
- Conversation history remains persisted per chat
- Practice memory is built from:
  - user messages
  - conversation artifacts
  - agent task packet `memory_updates`
- ClinicOS AI can carry forward information such as:
  - clinic name
  - practice type
  - location
  - PMS / EHR
  - provider / front-desk sizing
  - billing signals
- The assistant can also carry forward **response preferences** inferred from the chat

## Practice Profile Completion

The Practice Profile now reflects progressive completion instead of a flat static summary.

Implemented behavior:
- Profile card redesigned with stronger key/value hierarchy
- Two-column presentation for core fields
- Profile completion percentage
- Missing profile fields surfaced cleanly
- Assistant guidance can ask for missing practice details when they would improve the next answer
- Operations Console can override the Practice Profile per chat through editable admin fields
- The unused plan field has been removed from the Practice Profile flow
- Duplicate Location / Locations presentation has been reduced to a single user-facing **Location** field

## Escalation Logic

Human escalation is now conditional in the main workspace instead of always visible.

Implemented behavior:
- **Talk to Human** is shown in Practice Desk only when escalation indicators are present
- Escalation logic uses conversation state including:
  - explicit human request
  - dissatisfaction / frustration
  - unresolved turn count
  - looping behavior
  - low confidence
  - agent-requested escalation
  - support/account-specific situations
- Escalation recommendations no longer create Review Queue entries by themselves; the live human queue now opens only from an explicit human request in Practice Desk
- When a user clicks **Talk to Human**, ClinicOS AI is disconnected for that chat and the backend persists:
  - a system handoff message in the transcript
  - queue position for the waiting chat
  - human takeover events in the audit trail
- Human handoff now has three visible stages across Practice Desk and Operations Console:
  - queued
  - agent reviewing
  - live human chat
- While a human support request is active, new user messages stay in the same chat but no longer trigger ClinicOS AI replies
- Human specialists can reply from the merged admin Review Queue and those replies appear in Practice Desk in the same transcript
- Admin can explicitly **Take Over Chat** before replying; sending a human reply also auto-takes over the chat if it was still queued
- Admin controls can suspend the active chat or take the ClinicOS AI Triage Agent offline for all Practice Desk chats

## Loading and Chat UX

The chat wait state has been upgraded.

Implemented behavior:
- Sending a message no longer leaves the page feeling frozen
- Practice Desk now shows:
  - optimistic user message rendering
  - in-chat assistant loading animation / skeleton
  - small spacing above the AI thinking bubble so the loading reply sits like a normal chat message
  - responsive composer state during waiting
  - a separate queue wait state for human escalation, without showing the AI thinking skeleton after the handoff
- Chat area auto-scrolls as the conversation updates
- Workspace and admin human-review transcripts now stay pinned to the newest message only when the operator is already at the bottom; scrolling upward disables auto-jump until they return to the end
- Admin specialist views now use matching skeleton loads for initial dashboard states
- Admin Sales & Outreach and Marketing also show inline loading skeletons while research or campaign generation is running

## Suggested Scenarios

The scenario system has been upgraded to feel more realistic and production-like.

Implemented behavior:
- Practice Desk shows **4 support scenarios at a time**
- Refresh rotates through a larger support-focused scenario pool
- The Practice Desk scenario pool includes **20+** realistic clinic support, billing, upgrade, and escalation workflows
- Sales & Outreach and Marketing maintain their own separate suggested research / suggested campaign systems in Operations Console

## Guidance Experience

Practice Desk now includes user-facing guidance.

Implemented behavior:
- Added a guidance section and modal explaining:
  - what ClinicOS AI can help with in Practice Desk
  - that Practice Desk is support-only
  - how to get better results
  - when follow-up questions may appear
  - when human escalation is appropriate
- Product modals now use solid readable panels and can be dismissed by clicking outside
- The merged admin Review Queue now uses a **How To Use This View** modal instead of permanently showing the guidance copy inline
- Offline states now use a red **Offline** badge instead of the old Guided badge
- Chat transcripts now visually distinguish:
  - ClinicOS AI replies
  - human support replies
  - system notices
  - the current sender's own messages

## UI / Branding Cleanup

Outdated branding and PoC-facing copy have been removed from the main product surfaces.

Implemented behavior:
- Current brand vocabulary is standardized around ClinicOS, ClinicOS AI, Practice Desk, and Operations Console
- Shared button styling now uses a broader icon system across admin navigation and key actions such as save, refresh, send, print, email draft, and delete
- Removed the old raw SDK success wording from the main user-facing experience
- Removed the old always-visible Talk to Human behavior in Practice Desk
- Removed the old Open Priorities card from the workspace
- Removed the unused plan field from user-facing Practice Profile flows
- Replaced broad admin control wording with ClinicOS Agent / ClinicOS AI Triage Agent terminology
- Sales & Outreach and Marketing admin tools no longer present themselves as draft-review queues
- Practice Desk no longer presents itself as a mixed growth / marketing copilot

## Deletion and Audit

Practice Desk chat deletion is now soft-delete and audit-aware.

Implemented behavior:
- Users can delete the active Practice Desk chat
- Admins can delete any chat from Operations Console
- Deleted chats no longer appear in normal workspace or admin chat lists
- Deleted chat data remains stored in the database
- Operations Console exposes archived deleted chats in the Orchestration Logs area
- Archive modals show who deleted the chat, the archived Practice Profile, the transcript, and the related log history
- Archive audit trail and transcript panels now use constrained scrolling so long content remains readable inside the modal

## Current Route Map

- `/` -> ClinicOS homepage / entry experience
- `/workspace` -> Practice Desk
- `/admin` -> Operations Console overview
- `/admin/support` -> merged human takeover Review Queue
- `/admin/sales`
- `/admin/marketing`
- `/admin/review` -> merged human takeover Review Queue

Legacy redirects still exist for older route aliases:
- `/support` -> `/admin/support`
- `/sales` -> `/admin/sales`
- `/marketing` -> `/admin/marketing`
- `/review` -> `/admin/review`

## Implementation Notes

Key implementation changes now present in the codebase:
- new ClinicOS AI response prompt and response agent
- orchestrator now keeps Practice Desk in the support lane and routes to human handoff only when appropriate
- case memory now reads and reuses agent memory updates
- practice profile includes completion/missing-field behavior
- homepage and workspace were redesigned with stronger SaaS polish
- Practice Desk loading, scenario, guidance, and escalation behavior were upgraded
- new admin control state now powers active-chat suspension, all-chat ClinicOS AI suspension, and workspace availability
- new chat-specific Practice Profile override flow is available from Operations Console
- escalated Practice Desk chats now use a persisted human support queue with queue position, system handoff messages, human replies, and audit log entries
- admin support and review were merged into a single human takeover queue that reads existing chats instead of creating new ones
- admin Sales & Outreach now stores saved research history plus personalized outreach output without creating review work, supports permanent deletion, includes in-list delete controls, offers a mailto draft action, and scrolls to the latest brief after generation
- admin Marketing now stores saved campaign history without creating review work, supports permanent deletion, includes in-list delete controls, offers a PDF print/download action, and scrolls to the latest plan after generation
- legacy review-queue data is filtered so admin-generated sales / marketing tool output does not appear in the review queue
- the human Review Queue now filters down to explicit Practice Desk support handoffs and hides duplicate active escalations per chat
- deleted Practice Desk chats are now soft-deleted, archived, and reviewable in Operations Console
