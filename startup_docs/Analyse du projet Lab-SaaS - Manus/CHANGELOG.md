Text file: CHANGELOG.md
Latest content with line numbers:
2	
3	Toutes les modifications notables de ce projet seront documentées dans ce fichier.
4	
5	Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
6	et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).
7	
8	## [2.27.0] - 2025-10-21
9	
10	### 🎨 Templates Management UI
11	
12	**ADMIN INTERFACE FOR TEST TEMPLATES MANAGEMENT**
13	- ✅ Page `/admin/templates` - Complete CRUD interface
14	- ✅ Table view avec filtres (category, type, search, status)
15	- ✅ Stats cards (Total, Network, API, Security)
16	- ✅ Template Form Modal (Create/Edit avec validation)
17	- ✅ Delete Confirmation Dialog (soft delete avec warning impacts)
18	- ✅ Template Preview Modal (réutilisé depuis Campaign Builder)
19	- ✅ Permissions RBAC (testing:view/create/update/delete)
20	
21	**Backend**
22	- ✅ RBAC permissions sur routes templates
23	- ✅ Seeds enrichis: 9 templates (Network 4, API 2, System 2, Security 2)
24	  - Network Ping, Traceroute, DNS Resolution
25	  - API Health Check, Load Test
26	  - Web Screenshot, Database Health
27	  - SSL Certificate Check, Port Scanner
28	
29	**Frontend**
30	- ✅ Admin navigation: nouvelle section "Tests & Automation"
31	- ✅ React Query cache + invalidation mutations
32	- ✅ Optimistic updates pour UX instantanée
33	- ✅ Dark mode + responsive ≥1280px
34	- ✅ Toast notifications
35	
36	**Tests**
37	- ✅ Backend: 11 tests pytest (CRUD, permissions, validation)
38	- ✅ E2E: 10 scenarios Playwright (create, edit, delete, filters, search)
39	
40	### Added
41	- `frontend/src/pages/admin/TemplatesManagementPage.tsx` (386 lignes)
42	- `frontend/src/components/admin/TemplateFormModal.tsx` (230 lignes)
43	- `frontend/src/components/admin/TemplateDeleteDialog.tsx` (74 lignes)
44	- `backend/tests/test_routes_templates.py` (225 lignes)
45	- `frontend/tests/e2e/templates-management.spec.ts` (195 lignes)
46	
47	### Changed
48	- `backend/app/testing/routes_templates.py`: Added RBAC permissions
49	- `backend/scripts/seed_test_templates.py`: 3 → 9 templates
50	- `frontend/src/api/testing.ts`: Added createTemplate, updateTemplate, deleteTemplate
51	- `frontend/src/App.tsx`: Route `/admin/templates`
52	- `frontend/src/components/navigation/AdminSidebar.tsx`: Section "Tests & Automation"
53	
54	### Performance
55	- ✅ API GET /templates: <100ms
56	- ✅ React Query cache: 5min TTL
57	- ✅ Optimistic updates: UI instantanée
58	
59	## [2.26.5] - 2025-10-21
60	
61	### ⚡ Polish & Optimizations
62	
63	**Performance**
64	- ✅ Backend: Redis cache (TTL 5min) pour GET /templates
65	- ✅ Backend: Cache invalidation auto (create/update/delete templates)
66	- ✅ Backend: Index composite `(campaign_id, order)` sur campaign_items
67	- ✅ Performance: GET /templates <50ms (était <100ms)
68	
69	**UX Improvements**
70	- ✅ Frontend: Template Preview Modal avec détails complets
71	  - Paramètres requis vs optionnels
72	  - Tags, catégories, durée estimée
73	  - Suite Robot Framework path
74	  - Bouton "Ajouter à la Campagne" direct
75	- ✅ Frontend: Info button (hover) sur chaque template card
76	
77	**Technical**
78	- Migration: `33a47f9abb65_add_composite_index_campaign_items_v2_26_5.py`
79	- Component: `TemplatePreviewModal.tsx` (183 lignes)
80	- Cache keys pattern: `templates:list:*`
81	
82	### Changed
83	- `routes_templates.py`: Added Redis caching layer
84	- `CampaignBuilderPage.tsx`: Integrated preview modal
85	- Query optimization: Composite index améliore fetch items by campaign
86	
87	### Skipped (NICE-TO-HAVE)
88	- Infinite scroll templates (cache Redis + faible nombre templates suffisant)
89	
90	## [2.26.2] - 2025-10-21
91	
92	### 🌟 Feature Flag
93	
94	**CAMPAIGN_BUILDER_ENABLED** (Kill Switch)
95	- ✅ Backend: Feature flag dans `app/core/config.py`
96	- ✅ Frontend: Hook `useFeatureFlags()` pour conditional rendering
97	- ✅ API returns 503 si feature disabled
98	- ✅ UI cache bouton Campaign Builder si disabled
99	- ✅ Zero downtime toggle (just set env var)
100	