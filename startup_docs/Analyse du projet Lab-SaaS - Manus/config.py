Text file: config.py
Latest content with line numbers:
2	Configuration de l'application via Pydantic Settings.
3	
4	Charge les variables d'environnement depuis .env de façon sûre et typée.
5	"""
6	
7	from functools import lru_cache
8	from typing import Literal
9	
10	from pydantic import Field, field_validator
11	from pydantic_settings import BaseSettings, SettingsConfigDict
12	
13	
14	class Settings(BaseSettings):
15	    """
16	    Configuration de l'application LabSaaS.
17	    
18	    Toutes les variables sont chargées depuis le fichier .env (racine du projet).
19	    Les valeurs par défaut sont définies ici pour développement local.
20	    
21	    Usage:
22	        from app.core.config import get_settings
23	        
24	        settings = get_settings()
25	        print(settings.database_url)
26	    """
27	    
28	    # ============================================
29	    # APPLICATION
30	    # ============================================
31	    
32	    app_name: str = Field(default="LabSaaS", description="Nom de l'application")
33	    app_version: str = Field(default="0.1.0-alpha", description="Version")
34	    environment: Literal["development", "staging", "production"] = Field(
35	        default="development",
36	        description="Environnement d'exécution"
37	    )
38	    debug: bool = Field(default=True, description="Mode debug (logs verbeux)")
39	    testing_mode: bool = Field(default=False, description="Mode test E2E (rate limit disabled)")
40	    
41	    # ============================================
42	    # SERVER
43	    # ============================================
44	    
45	    api_host: str = Field(default="0.0.0.0", description="Host API")
46	    api_port: int = Field(default=8000, ge=1024, le=65535, description="Port API")
47	    api_base_url: str = Field(
48	        default="http://localhost:8000",
49	        description="URL base de l'API"
50	    )
51	    
52	    # CORS Origins (séparés par virgule dans .env)
53	    cors_origins: str = Field(
54	        default="http://localhost:5173,http://127.0.0.1:5173",
55	        description="Origins autorisées pour CORS (séparées par virgule)"
56	    )
57	    
58	    @property
59	    def cors_origins_list(self) -> list[str]:
60	        """Convertit la string CORS en liste."""
61	        return [origin.strip() for origin in self.cors_origins.split(",")]
62	    
63	    # ============================================
64	    # DATABASE (PostgreSQL) - Pour Étape 2
65	    # ============================================
66	    
67	    database_url: str = Field(
68	        default="postgresql+asyncpg://labsaas:labsaas_dev_password@localhost:5432/labsaas",
69	        description="URL connexion PostgreSQL (format SQLAlchemy async - DOIT contenir +asyncpg)"
70	    )
71	    
72	    @field_validator("database_url")
73	    @classmethod
74	    def validate_async_driver(cls, v: str) -> str:
75	        """Valide que l'URL utilise un driver async."""
76	        if v.startswith("postgresql://") and "+asyncpg" not in v:
77	            # Auto-correction : ajouter +asyncpg
78	            v = v.replace("postgresql://", "postgresql+asyncpg://")
79	            import logging
80	            logging.warning(f"⚠️  DATABASE_URL corrigé : ajout de +asyncpg pour driver async")
81	        return v
82	    db_echo: bool = Field(default=False, description="Logger toutes les queries SQL")
83	    db_pool_size: int = Field(default=20, ge=5, le=100, description="Taille pool connexions")
84	    db_max_overflow: int = Field(default=10, ge=0, le=50, description="Max overflow pool")
85	    db_pool_timeout: int = Field(default=30, ge=5, le=60, description="Timeout pool (secondes)")
86	    
87	    # ============================================
88	    # REDIS - Pour Étape 14
89	    # ============================================
90	    
91	    redis_url: str = Field(
92	        default="redis://localhost:6379/0",
93	        description="URL connexion Redis"
94	    )
95	    redis_ttl_session: int = Field(
96	        default=604800,  # 7 jours
97	        description="TTL sessions Redis (secondes)"
98	    )
99	    
100	    # ============================================