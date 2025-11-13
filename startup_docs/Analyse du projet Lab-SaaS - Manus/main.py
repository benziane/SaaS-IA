Text file: main.py
Latest content with line numbers:
1	"""
2	LabSaaS Backend API - Point d'entrée FastAPI.
3	
4	Application FastAPI pour gestion de ressources télécom avec assistance IA.
5	"""
6	
7	from contextlib import asynccontextmanager
8	from typing import AsyncGenerator
9	
10	from fastapi import FastAPI, Request
11	from fastapi.middleware.cors import CORSMiddleware
12	
13	from app.admin.routes import router as admin_router
14	from app.admin.version_routes import router as settings_version_router
15	from app.admin.dashboard_api import router as dashboard_router  # Dashboard Stats v2.12.0
16	from app.ai.routes import router as ai_router
17	from app.audit.routes import router as audit_router
18	from app.auth.routes import router as auth_router, permissions_router as basic_permissions_router
19	from app.auth.router_permissions import router as permissions_router  # Full permissions router
20	from app.auth.rbac_api import router as rbac_router  # RBAC Management API
21	from app.auth.metadata_versions_api import router as metadata_versions_router  # Metadata Versioning v2.9.1
22	from app.auth.permission_group_routes import router as permission_groups_router  # Permission Groups v2.13.0
23	from app.devices.routes import router as devices_router
24	from app.devices.bulk_routes import router as devices_bulk_router
25	from app.sims.routes import router as sims_router
26	from app.ues.routes import router as ues_router
27	from app.users.routes import router as users_router
28	from app.hierarchy.routes import router as hierarchy_router
29	from app.monitoring.routes import router as monitoring_router
30	from app.testing.routes import router as testing_router
31	from app.testing.scheduler_routes import router as scheduler_router
32	from app.testing.routes_templates import router as templates_router  # Campaign Templates v2.24.0
33	from app.testing.routes_notifications import router as notifications_router  # Notifications v2.25.0
34	from app.testing.routes_analytics import router as analytics_router  # Analytics v2.25.0
35	from app.testing.routes_bulk import router as bulk_router  # Bulk Actions v2.25.0
36	from app.testing import scheduler as scheduler_service  # Robot Framework Testing v2.16.0
37	from app.testing.routes_allure import router as testing_allure_router  # Allure Reports v2.18.0
38	from app.core.health import router as health_router
39	from app.common.db import close_db, init_db, AsyncSessionLocal
40	from app.core.redis import redis_service
41	from app.core.http_client import get_http_client, close_http_client
42	from app.core.startup import initialize_monitoring_services
43	from app.core.metrics import prometheus_middleware, get_prometheus_metrics
44	from app.core import metrics
45	from app.core.config import get_settings
46	# from app.core.logging import setup_logging, get_logger
47	# from app.core.middleware import RequestLoggingMiddleware, UserContextMiddleware
48	
49	settings = get_settings()
50	
51	# ============================================
52	# SENTRY INTEGRATION (v2.8.0)
53	# ============================================
54	
55	# Initialize Sentry for error tracking (production-ready)
56	if settings.sentry_enabled and settings.sentry_dsn:
57	    try:
58	        import sentry_sdk
59	        from sentry_sdk.integrations.fastapi import FastAPIIntegration
60	        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
61	        
62	        sentry_sdk.init(
63	            dsn=settings.sentry_dsn,
64	            integrations=[
65	                FastAPIIntegration(),
66	                SqlalchemyIntegration(),
67	            ],
68	            environment=settings.sentry_environment,
69	            traces_sample_rate=settings.sentry_traces_sample_rate,
70	            # Set release version for tracking
71	            release=f"labsaas@{settings.app_version}",
72	            # Attach user context automatically
73	            send_default_pii=True,
74	            # Performance monitoring
75	            profiles_sample_rate=settings.sentry_traces_sample_rate,
76	        )
77	        print(f"✅ Sentry initialized: {settings.sentry_environment} (traces: {settings.sentry_traces_sample_rate * 100}%)")
78	    except ImportError:
79	        print("⚠️  Sentry SDK not installed. Run: uv add sentry-sdk")
80	    except Exception as e:
81	        print(f"⚠️  Failed to initialize Sentry: {e}")
82	
83	# ============================================
84	# CONFIGURATION LOGGING
85	# ============================================
86	
87	# LOGGING TEMPORAIREMENT DESACTIVE - OPTIMISATION PERFORMANCES
88	# logger = setup_logging()
89	
90	class DummyLogger:
91	    """Logger stub pour éviter les erreurs."""
92	    def info(self, *args, **kwargs): pass
93	    def debug(self, *args, **kwargs): pass
94	    def warning(self, *args, **kwargs): pass
95	    def error(self, *args, **kwargs): pass
96	
97	logger = DummyLogger()
98	
99	# ============================================
100	# LIFESPAN - Gestion Startup/Shutdown
101	# ============================================
102	
103	
104	@asynccontextmanager
105	async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
106	    """
107	    Gère le cycle de vie de l'application.
108	    
109	    - Startup : Initialiser connexions DB, Redis, etc.
110	    - Shutdown : Fermer connexions proprement
111	    
112	    Remplace les anciens @app.on_event("startup") (deprecated).
113	    """
114	    # ──── STARTUP ────
115	    logger.info("application_startup", message="Application starting...")
116	    
117	    # Initialiser connexion PostgreSQL
118	    logger.info("database_init", message="Initializing PostgreSQL connection...")
119	    await init_db()
120	    logger.info("database_ready", message="PostgreSQL connected!", database="labsaas")
121	    
122	    # Initialiser connexion Redis
123	    logger.info("redis_init", message="Initializing Redis connection...")
124	    await redis_service.connect()
125	    logger.info("redis_ready", message="Redis connected!", url=settings.redis_url)
126	    
127	    # Initialiser HTTP Client Pool pour APIs externes
128	    logger.info("http_client_init", message="Initializing HTTP client pool...")
129	    http_client = get_http_client()
130	    await http_client.connect()
131	    logger.info("http_client_ready", message="HTTP client pool ready!", max_connections=200)
132	    
133	    # TODO Étape 12 : Initialiser client AI (Anthropic)
134	    
135	    # Initialiser services monitoring selon GlobalSettings
136	    logger.info("monitoring_auto_start", message="Initializing monitoring services...")
137	    async with AsyncSessionLocal() as session:
138	        await initialize_monitoring_services(session)
139	    logger.info("monitoring_auto_start_complete", message="Monitoring services initialized")
140	    
141	    # Initialiser APScheduler pour scheduled campaigns (v2.21.0)
142	    logger.info("scheduler_init", message="Initializing APScheduler for test campaigns...")
143	    scheduler_service.init_scheduler()
144	    logger.info("scheduler_ready", message="APScheduler ready with scheduled campaigns loaded")
145	    
146	    logger.info("application_ready", message="Application ready!", version="0.1.0-alpha")
147	    
148	    yield  # ← Application tourne ici
149	    
150	    # ──── SHUTDOWN ────
151	    logger.info("application_shutdown", message="Application shutting down...")
152	    
153	    # Fermer connexion PostgreSQL
154	    logger.info("database_closing", message="Closing PostgreSQL connection...")
155	    await close_db()
156	    logger.info("database_closed", message="PostgreSQL disconnected cleanly")
157	    
158	    # Shutdown APScheduler
159	    logger.info("scheduler_closing", message="Shutting down APScheduler...")
160	    scheduler_service.shutdown_scheduler()
161	    logger.info("scheduler_closed", message="APScheduler shut down cleanly")
162	    
163	    # Fermer connexion Redis
164	    logger.info("redis_closing", message="Closing Redis connection...")
165	    await redis_service.close()
166	    logger.info("redis_closed", message="Redis disconnected cleanly")
167	    
168	    # Fermer HTTP Client Pool
169	    logger.info("http_client_closing", message="Closing HTTP client pool...")
170	    await close_http_client()
171	    logger.info("http_client_closed", message="HTTP client pool closed cleanly")
172	    
173	    # TODO Étape 12 : Fermer client AI
174	    
175	    logger.info("application_stopped", message="Application stopped cleanly")
176	
177	
178	# ============================================
179	# CRÉATION APPLICATION FASTAPI
180	# ============================================
181	
182	# ============================================
183	# PROTECTION SWAGGER EN PRODUCTION
184	# ============================================
185	
186	# Désactiver documentation API en production pour sécurité
187	# En dev/staging, Swagger UI et ReDoc sont disponibles
188	docs_url = None if settings.environment == "production" else "/docs"
189	redoc_url = None if settings.environment == "production" else "/redoc"
190	openapi_url = None if settings.environment == "production" else "/openapi.json"
191	
192	app = FastAPI(
193	    title="LabSaaS API",
194	    description="API REST pour gestion ressources télécom avec assistance IA",
195	    version="0.1.0-alpha",
196	    docs_url=docs_url,       # Swagger UI (disabled in production)
197	    redoc_url=redoc_url,     # ReDoc (disabled in production)
198	    openapi_url=openapi_url,  # OpenAPI spec (disabled in production)
199	    lifespan=lifespan,      # Gestion startup/shutdown
200	)
201	
202	# ============================================
203	# MIDDLEWARE - Prometheus Metrics
204	# ============================================
205	
206	app.middleware("http")(prometheus_middleware)
207	# app.add_middleware(RequestLoggingMiddleware)
208	# app.add_middleware(UserContextMiddleware)
209	
210	# ============================================
211	# MIDDLEWARE - Security Headers
212	# ============================================
213	
214	@app.middleware("http")
215	async def add_security_headers(request: Request, call_next):
216	    """
217	    Ajoute les headers de sécurité à toutes les réponses (si activé dans GlobalSettings).
218	    
219	    Conforme OWASP (v2.5.0):
220	    - X-Content-Type-Options: Prévient MIME sniffing
221	    - X-Frame-Options: Prévient clickjacking
222	    - X-XSS-Protection: Protection XSS legacy browsers
223	    - Strict-Transport-Security: Force HTTPS
224	    - Content-Security-Policy: Contrôle ressources chargées
225	    
226	    Configurable via GlobalSettings.security_headers_enabled
227	    """
228	    response = await call_next(request)
229	    
230	    # Vérifier si security headers activés (GlobalSettings)
231	    # Note: Pour performance, on check au démarrage ou cache ce setting
232	    # Pour l'instant, toujours activé par défaut (sécurité first)
233	    # TODO: Implémenter cache setting avec invalidation
234	    security_headers_enabled = True  # Default True pour sécurité
235	    
236	    if security_headers_enabled:
237	        # OWASP Security Headers
238	        response.headers["X-Content-Type-Options"] = "nosniff"
239	        response.headers["X-Frame-Options"] = "DENY"
240	        response.headers["X-XSS-Protection"] = "1; mode=block"
241	        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
242	        
243	        # CSP: Exception pour /docs (Swagger UI nécessite CDN)
244	        if request.url.path in ["/docs", "/openapi.json"]:
245	            response.headers["Content-Security-Policy"] = "default-src 'self' https://cdn.jsdelivr.net https://fastapi.tiangolo.com; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com;"
246	        else:
247	            response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';"
248	        
249	        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
250	        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
251	    
252	    return response
253	
254	# ============================================
255	(Content truncated due to size limit. Use page ranges or line ranges to read remaining content)