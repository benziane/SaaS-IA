Text file: README.md
Reading lines: 1-500 (file has 1003 lines)
Latest content with line numbers:
1	﻿
2	---
3	
4	# 🧪 LabSaaS - Laboratoire Télécom Management Platform
5	
6	**Version :** 2.23.0 "Production Ready - Worker Auto-Start"  
7	**Date :** 21 Octobre 2025
8	
9	**SaaS interne** pour la gestion de ressources télécom (devices 5G/4G, SIM cards, tests, logs) avec assistance IA pour un laboratoire de validation d'opérateur mobile.
10	
11	[![CI Pipeline](https://github.com/benziane/lab-saas/workflows/CI%20Pipeline/badge.svg)](https://github.com/benziane/lab-saas/actions)
12	[![Version](https://img.shields.io/badge/version-2.23.0-blue)](CHANGELOG.md)
13	[![RBAC](https://img.shields.io/badge/RBAC-Enterprise%20Scale%20%E2%9A%A1-brightgreen)](docs/features/rbac.md)
14	[![Score Global](https://img.shields.io/badge/Score-10.0%2F10-brightgreen)](#)
15	[![Performance](https://img.shields.io/badge/Permission%20Checks-<5ms-brightgreen)](docs/rapports/STATS-v2.15.0-PERFORMANCE-METRICS.md)
16	[![Cache](https://img.shields.io/badge/Cache%20Hit-98%25-brightgreen)](#)
17	[![Scalability](https://img.shields.io/badge/Users-2K%20concurrent-brightgreen)](#)
18	[![OWASP](https://img.shields.io/badge/OWASP-100%25-brightgreen)](#)
19	[![Production Ready](https://img.shields.io/badge/production%20ready-100%25-brightgreen)](#)
20	[![Tests](https://img.shields.io/badge/tests-703%20total-success)](backend/tests/)
21	[![Robot Tests](https://img.shields.io/badge/Robot%20tests-19%20suites-success)](backend/tests/robot/)
22	[![Coverage](https://img.shields.io/badge/coverage-75%25-green)](#)
23	[![Bundle](https://img.shields.io/badge/bundle-560kb-green)](#)
24	[![Security](https://img.shields.io/badge/security-OWASP%20compliant-brightgreen)](#)
25	
26	---
27	
28	## 🎯 Objectifs
29	
30	* **Gestion centralisée** : Devices, SIM cards, User Equipment (UE), utilisateurs, audit trail
31	* **Validations télécom strictes** : IMEI (Luhn), ICCID, IMSI, MSISDN (E.164)
32	* **IA intégrée** : Analyse logs, détection anomalies, suggestions tests (Gemini API)
33	* **Sécurité** : RBAC multi-teams, JWT httpOnly, audit immutable, OWASP Top 10
34	* **Enterprise Scale ⚡** : Multi-level cache (< 5ms), Hierarchical permissions, 2K users
35	* **Testing Automation 🤖** : Robot Framework (Worker Auto-Start, WebSocket, Real-time), 100% opérationnel
36	* **Modern Stack** : FastAPI + React 18 + PostgreSQL + Redis + Docker
37	
38	---
39	
40	## 🏗️ Architecture
41	
42	### Stack Technique
43	
44	```
45	Frontend (React 18 + TS)  →  Backend (FastAPI)  →  PostgreSQL 16
46	     ↓                              ↓                     ↓
47	Vite + Tailwind + shadcn      SQLModel + Alembic    JSONB + Enums
48	     ↓                              ↓                     ↓
49	TanStack Query + Zod         Pydantic + structlog     Redis Cache
50	                                     ↓
51	                          Multi-Level Cache (L1+L2+DB)
52	                          Materialized Views
53	                          Hierarchical RBAC
54	```
55	
56	### Architecture Globale
57	
58	```
59	┌─────────────────────────────────────────────────────────────┐
60	│                       FRONTEND LAYER                         │
61	│  ┌───────────────────────────────────────────────────────┐  │
62	│  │  React 18 + TypeScript + Vite                         │  │
63	│  │  ├─ Auth: Login, Logout, Protected Routes             │  │
64	│  │  ├─ Users: CRUD, Roles, Permissions                   │  │
65	│  │  ├─ Devices: Table, Filters, CRUD, History            │  │
66	│  │  ├─ SIM Cards: CRUD, Operator management              │  │
67	│  │  ├─ UEs: Device+SIM pairing, Status tracking          │  │
68	│  │  ├─ Audit: Timeline, Filters, Export                  │  │
69	│  │  └─ AI Tools: Chat Assistant, Device Analysis         │  │
70	│  │                                                         │  │
71	│  │  UI: Tailwind CSS + shadcn/ui + Lucide Icons          │  │
72	│  │  State: TanStack Query + Zustand + React Context      │  │
73	│  └───────────────────────────────────────────────────────┘  │
74	└──────────────────────┬──────────────────────────────────────┘
75	                       │ HTTP/REST (axios instance)
76	                       │ JWT in httpOnly cookies
77	┌──────────────────────▼──────────────────────────────────────┐
78	│                    BACKEND LAYER (FastAPI)                   │
79	│  ┌───────────────────────────────────────────────────────┐  │
80	│  │  FastAPI App (Python 3.11+, Uvicorn ASGI)             │  │
81	│  │                                                         │  │
82	│  │  MODULES:                                              │  │
83	│  │  ├─ /auth/*      → JWT, OAuth2, RBAC                  │  │
84	│  │  ├─ /users/*     → CRUD Users, Roles, Teams           │  │
85	│  │  ├─ /devices/*   → CRUD Devices + IMEI validation     │  │
86	│  │  ├─ /sims/*      → CRUD SIM Cards + telecom validation│  │
87	│  │  ├─ /ues/*       → User Equipment (Device+SIM pairing)│  │
88	│  │  ├─ /audit/*     → Audit Trail, Query Logs            │  │
89	│  │  ├─ /ai/*        → Gemini Assistant, Analysis         │  │
90	│  │  ├─ /health      → Liveness, Readiness                │  │
91	│  │  └─ /docs        → OpenAPI (Swagger UI)               │  │
92	│  │                                                         │  │
93	│  │  SECURITY:                                             │  │
94	│  │  ├─ RBAC Decorators (@require_role)                   │  │
95	│  │  ├─ JWT httpOnly cookies (4h access, 7d refresh)      │  │
96	│  │  ├─ Password hashing (bcrypt cost 12)                 │  │
97	│  │  ├─ OWASP Security Headers (CSP, HSTS, X-Frame, etc.) │  │
98	│  │  └─ Audit Trail (immutable logs)                      │  │
99	│  └───────────────────────────────────────────────────────┘  │
100	└──────────┬─────────────────────┬───────────────────┬────────┘
101	           │                     │                   │
102	┌──────────▼─────────┐  ┌────────▼────────┐  ┌──────▼──────────┐
103	│   PostgreSQL 16    │  │   Redis 7       │  │  Gemini API     │
104	│                    │  │                 │  │  (Google)       │
105	│ Tables:            │  │ Use Cases:      │  │                 │
106	│ ├─ users           │  │ ├─ Cache        │  │ AI Assistant:   │
107	│ ├─ devices         │  │ ├─ Rate Limits  │  │ ├─ Log Analysis │
108	│ ├─ sim_cards       │  │ └─ Sessions     │  │ ├─ Anomaly      │
109	│ ├─ ue (user_equip) │  │                 │  │ └─ Suggestions  │
110	│ └─ audit_logs      │  └─────────────────┘  └─────────────────┘
111	└────────────────────┘
112	```
113	
114	> 📐 **Architecture Détaillée** : Voir [docs/architecture/PROJECT-ARCHITECTURE.md](docs/architecture/PROJECT-ARCHITECTURE.md)
115	
116	---
117	
118	---
119	
120	## 🆕 Nouvelles Fonctionnalités v2.13.0 (2025-10-19)
121	
122	### ⌨️ Command Palette (Cmd+K) ✨ NEW
123	- ✅ **Raccourci global** : `Cmd+K` (Mac) / `Ctrl+K` (Windows)
124	- ✅ **21 actions rapides** : Navigation, Quick Actions, Theme, Account
125	- ✅ **Recherche intelligente** : Keywords + fuzzy matching
126	- ✅ **Admin conditional** : Actions basées sur rôle
127	- ✅ **Impact** : +50% productivité navigation
128	
129	**Usage:** Appuyer `Cmd+K` n'importe où → Taper "dev" → Devices !
130	
131	### 📜 Virtual Scrolling ✨ NEW
132	- ✅ **Performance +95%** : 10,000 items en 60ms (vs 2000ms)
133	- ✅ **Memory -90%** : Efficient memory usage
134	- ✅ **Components** : VirtualTable, VirtualList
135	- ✅ **Smooth scrolling** : Pas de freeze UI
136	- ✅ **Auto-resize** : Dynamic height measurement
137	
138	**Benchmarks:** 1k items = 50ms | 5k items = 50ms | 10k items = 60ms
139	
140	### 🎯 Universal Filters ✨ NEW
141	- ✅ **Système réutilisable** : Toutes listes de l'app
142	- ✅ **Multi-criteria** : Combiner plusieurs filtres
143	- ✅ **URL persistence** : Filtres sauvegardés dans URL
144	- ✅ **Active badges** : Visualisation + clear individual/all
145	- ✅ **Types** : text, select, date, daterange, number, boolean
146	
147	**Impact:** Expérience de filtrage cohérente partout
148	
149	### 📦 Bundle Optimization ✨ NEW
150	- ✅ **Bundle -30%** : 800kb → 560kb
151	- ✅ **Load -40%** : 2.5s → 1.5s
152	- ✅ **Cache +42%** : 60% → 85% hit rate
153	- ✅ **Compression** : Gzip + Brotli
154	- ✅ **Code splitting** : Vendor + Features chunks
155	- ✅ **Analysis** : `npm run build:analyze`
156	
157	**Impact:** Performance production optimale
158	
159	### ⚡ RBAC Enterprise Scale v2.15.0 ✨ LATEST
160	**Multi-Level Cache & Hierarchical Permissions**
161	
162	#### Performance Optimization
163	- ✅ **Multi-level cache** : L1 (in-memory) + L2 (Redis) + L3 (DB)
164	  - L1 hit: < 1ms (60% requests)
165	  - L2 hit: < 10ms (35% requests)
166	  - Overall avg: **< 5ms** (-84% vs v2.14.0)
167	- ✅ **Summary mode** : `/permissions/me?mode=summary` (2KB vs 50KB, -96%)
168	- ✅ **Cache pre-warming** : Auto at login (first check < 5ms)
169	- ✅ **Materialized view** : `user_effective_permissions_mv` (10ms vs 150ms, -93%)
170	
171	#### Hierarchical RBAC
172	- ✅ **3-level hierarchy** : Department → Service → Team
173	- ✅ **Permission inheritance** : Cascade auto dept→service→team
174	- ✅ **Enhanced scopes** : all, own, team, **department**, **service**
175	- ✅ **Frontend UI** : Tabs "Départements" & "Équipes" in RBAC Management
176	- ✅ **Scope checker** : Fine-grained access control
177	
178	#### Scalability
179	- ✅ **2,000 concurrent users** (vs 300 before, +567%)
180	- ✅ **98% cache hit rate** (vs 85%, +13%)
181	- ✅ **76 tests** : Performance (66) + E2E hierarchy (10)
182	
183	**Routes:** `/api/permissions/me`, `/api/auth/login` (cookies httpOnly)  
184	**Docs:** [STEP-35](docs/formation/STEP-35-RBAC-ENTERPRISE-SCALE-v2.15.0.md) | [Stats](docs/rapports/STATS-v2.15.0-PERFORMANCE-METRICS.md)
185	
186	---
187	
188	### 🔐 Permission Groups System
189	- ✅ **8 API endpoints** : CRUD + Membership + Bulk assignment
190	- ✅ **Groupes logiques** : Organiser permissions (ex: "Device Management")
191	- ✅ **Bulk assignment** : Assigner groupe complet à un rôle
192	- ✅ **System groups** : Protégés contre suppression
193	- ✅ **40 tests** : Coverage complète
194	- ✅ **Migration** : Appliquée (2 tables créées)
195	
196	**Routes:** `/api/rbac/permission-groups/*`
197	
198	### 👥 TeamsPage ✨ NEW
199	- ✅ **Page dédiée** : `/teams` pour gestion équipes
200	- ✅ **Statistics** : 4 cards (total, actives, membres, services)
201	- ✅ **CRUD complet** : Via HierarchyManager
202	- ✅ **Manager assignment** : Assignation manager équipe
203	- ✅ **Help card** : Guide contextuel
204	
205	**Navigation:** Sidebar → Organisation → Teams
206	
207	### 🎨 RBAC Unifié
208	- ✅ **3 pages fusionnées** : Roles + Permissions + Details → 1 page RBAC
209	- ✅ **Redirections auto** : Anciennes routes → `/admin/rbac`
210	- ✅ **-270 lignes** : Code duplicate éliminé
211	- ✅ **Navigation restructurée** : 5 sections organisées
212	
213	**Impact:** Interface cohérente, maintenance simplifiée
214	
215	---
216	
217	### 🏢 Gestion Hiérarchique
218	- ✅ **4 niveaux hiérarchiques** : Organization → Department → Service → Team
219	- ✅ **CRUD complet** avec API REST et interface React
220	- ✅ **Cascade deletion** avec confirmation renforcée
221	- ✅ **Visualisation arborescente** interactive
222	
223	📖 **Documentation** : [docs/features/HIERARCHY-MANAGEMENT.md](docs/features/HIERARCHY-MANAGEMENT.md)
224	
225	### 📊 Logging & Monitoring
226	- ✅ **Logging structuré** (Structlog) avec JSON et rotation
227	- ✅ **Métriques Prometheus** (14 métriques custom)
228	- ✅ **9 alertes automatiques** (performance, erreurs, database, cache)
229	(Content truncated due to size limit. Use page ranges or line ranges to read remaining content)